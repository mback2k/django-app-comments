# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import condition
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.forms import inlineformset_factory
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Author, Thread, Post, Vote, Media, Attachment
from .forms import PostNewForm, PostReplyForm, PostEditForm
from .tasks import notification_post_moderation_pending, notification_post_approved, notification_post_new_reply
import os.path, datetime

def show_threads_latest(request, category):
    if request.user.has_perm('comments.change_post') or request.user.has_perm('comments.delete_post'):
        thread_list = Thread.objects.filter(category=category)
    else:
        thread_list = Thread.objects.filter(category=category).exclude(is_deleted=True)
    return thread_list

def show_threads_etag(request, category):
    if len(messages.get_messages(request)):
        return None
    try:
        thread_list = show_threads_latest(request, category)
        thread_list_posts = Post.objects.filter(thread__in=thread_list)
        etag = '%d:%d:%d:%d' % (thread_list.count(),
                                thread_list.latest('tstamp').id,
                                thread_list_posts.count(),
                                thread_list_posts.latest('tstamp').id)
        if request.user.is_authenticated():
            etag += ':%d' % request.user.id
        return etag
    except Thread.DoesNotExist, e:
        return None

def show_threads_last_modified(request, category):
    if len(messages.get_messages(request)):
        return None
    try:
        thread_list = show_threads_latest(request, category)
        thread_list_posts = Post.objects.filter(thread__in=thread_list)
        last_modified = max(thread_list.latest('tstamp').tstamp,
                            thread_list_posts.latest('tstamp').tstamp,
                            datetime.datetime.fromtimestamp(os.path.getmtime(__file__),
                                                            timezone.get_current_timezone()))
        if request.user.is_authenticated():
            last_modified = max(last_modified, request.user.last_login)
        return last_modified
    except Thread.DoesNotExist, e:
        return None

@condition(etag_func=show_threads_etag, last_modified_func=show_threads_last_modified)
def show_threads(request, category):
    thread_list = show_threads_latest(request, category)

    paginator = Paginator(thread_list, 10)
    page = request.GET.get('page')
    try:
        threads = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        threads = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        threads = paginator.page(paginator.num_pages)

    template_values = {
        'category': category,
        'threads': threads,
    }

    return render_to_response('show_threads.html', template_values, context_instance=RequestContext(request))

def show_posts_latest(request, category, thread_id):
    if request.user.has_perm('comments.change_post') or request.user.has_perm('comments.delete_post'):
        thread = get_object_or_404(Thread, category=category, id=thread_id)
    else:
        thread = get_object_or_404(Thread, category=category, id=thread_id, is_deleted=False)
    return thread

def show_posts_etag(request, category, thread_id):
    if len(messages.get_messages(request)):
        return None
    try:
        thread = show_posts_latest(request, category, thread_id)
        thread_latest_post = thread.posts.latest('tstamp')
        etag = '%d:%d:%d:%d' % (thread.posts.count(),
                                thread.id,
                                thread_latest_post.id,
                                thread_latest_post.vote_sum or 0)
        if request.user.is_authenticated():
            etag += ':%d' % request.user.id
        return etag
    except Http404, e:
        return None

def show_posts_last_modified(request, category, thread_id):
    if len(messages.get_messages(request)):
        return None
    try:
        thread = show_posts_latest(request, category, thread_id)
        last_modified = max(thread.posts.latest('tstamp').tstamp,
                            datetime.datetime.fromtimestamp(os.path.getmtime(__file__),
                                                            timezone.get_current_timezone()))
        if request.user.is_authenticated():
            last_modified = max(last_modified, request.user.last_login)
        return last_modified
    except Http404, e:
        return None

@condition(etag_func=show_posts_etag, last_modified_func=show_posts_last_modified)
def show_posts(request, category, thread_id):
    try:
        thread = show_posts_latest(request, category, thread_id)
    except Http404, e:
        try:
            thread = Thread.objects.exclude(category=category).get(id=thread_id)
            return HttpResponsePermanentRedirect(thread.get_absolute_url())
        except Thread.DoesNotExist, e2:
            raise e

    try:
        if request.user.has_perm('comments.change_post') or request.user.has_perm('comments.delete_post'):
            first_post = thread.first_post
        else:
            first_post = thread.first_active_post
    except Post.DoesNotExist, e:
        raise Http404

    template_values = {
        'category': category,
        'thread': thread,
        'first_post': first_post,
    }

    return render_to_response('show_posts.html', template_values, context_instance=RequestContext(request))


@login_required
@transaction.atomic
def new_post(request, category):
    MediaFormset = inlineformset_factory(Post, Media, fields=('image',),
                                         min_num=0, max_num=3, can_delete=False)
    AttachmentFormset = inlineformset_factory(Post, Attachment, fields=('file',),
                                              min_num=0, max_num=3, can_delete=False)

    if request.method == 'POST':
        post_form = PostNewForm(data=request.POST)
        media_formset = MediaFormset(data=request.POST, files=request.FILES, prefix='media')
        attachment_formset = AttachmentFormset(data=request.POST, files=request.FILES, prefix='attachment')
    else:
        post_form = PostNewForm()
        media_formset = MediaFormset(prefix='media')
        attachment_formset = AttachmentFormset(prefix='attachment')

    if post_form.is_valid() and media_formset.is_valid() and attachment_formset.is_valid():
        post = post_form.save(commit=False)
        media_set = media_formset.save(commit=False)
        attachment_set = attachment_formset.save(commit=False)

        post.thread = Thread.objects.create(category=category)
        post.author = Author.objects.get(pk=request.user.pk)
        post.is_approved = post.author.posts.filter(is_approved=True).exists() and not len(media_set) and not len(attachment_set)
        post.save()

        for media in media_set:
            media.post = post
            media.save()

        for attachment in attachment_set:
            attachment.post = post
            attachment.save()

        if not post.is_approved:
            notification_post_moderation_pending.apply_async(countdown=1, kwargs={'post_id': post.id, 'mode': 'approval'})
            messages.info(request, _('<strong>Thanks</strong>, your comment has successfully been submitted but requires approval.<br />' \
                                     'You will be informed via email once it has been reviewed and approved.'))
        else:
            messages.success(request, _('<strong>Thanks</strong>, your comment has successfully been submitted and posted.'))

        return HttpResponseRedirect(post.thread.get_absolute_url())

    template_values = {
        'category': category,
        'post_form': post_form,
        'media_formset': media_formset,
        'attachment_formset': attachment_formset,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def reply_post(request, category, thread_id, parent_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    parent = get_object_or_404(Post, thread=thread, id=parent_id)

    MediaFormset = inlineformset_factory(Post, Media, fields=('image',),
                                         min_num=0, max_num=3, can_delete=False)
    AttachmentFormset = inlineformset_factory(Post, Attachment, fields=('file',),
                                              min_num=0, max_num=3, can_delete=False)

    if request.method == 'POST':
        post_form = PostReplyForm(data=request.POST)
        media_formset = MediaFormset(data=request.POST, files=request.FILES, prefix='media')
        attachment_formset = AttachmentFormset(data=request.POST, files=request.FILES, prefix='attachment')
    else:
        post_form = PostReplyForm(initial={'parent': parent, 'thread': thread})
        media_formset = MediaFormset(prefix='media')
        attachment_formset = AttachmentFormset(prefix='attachment')

    if post_form.is_valid() and media_formset.is_valid() and attachment_formset.is_valid():
        post = post_form.save(commit=False)
        media_set = media_formset.save(commit=False)
        attachment_set = attachment_formset.save(commit=False)

        post.author = Author.objects.get(pk=request.user.pk)
        post.is_approved = post.author.posts.filter(is_approved=True).exists() and not len(media_set) and not len(attachment_set)
        post.save()

        for media in media_set:
            media.post = post
            media.save()

        for attachment in attachment_set:
            attachment.post = post
            attachment.save()

        if not post.is_approved:
            notification_post_moderation_pending.apply_async(countdown=1, kwargs={'post_id': post.id, 'mode': 'approval'})
            messages.info(request, _('<strong>Thanks</strong>, your comment has successfully been submitted but requires approval.<br />' \
                                     'You will be informed via email once it has been reviewed and approved.'))
        else:
            notification_post_new_reply.apply_async(countdown=1, kwargs={'post_id': post.id})
            messages.success(request, _('<strong>Thanks</strong>, your comment has successfully been submitted and posted.'))

        return HttpResponseRedirect(post.get_absolute_url())

    template_values = {
        'category': category,
        'post_form': post_form,
        'media_formset': media_formset,
        'attachment_formset': attachment_formset,
        'thread': thread,
        'parent': parent,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def edit_post(request, category, thread_id, post_id):
    author = Author.objects.get(pk=request.user.pk)
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, author=author, id=post_id)

    if not post.is_editable:
        return HttpResponseRedirect(thread.get_absolute_url())

    MediaFormset = inlineformset_factory(Post, Media, fields=('image',),
                                         min_num=0, max_num=3, can_delete=True)
    AttachmentFormset = inlineformset_factory(Post, Attachment, fields=('file',),
                                              min_num=0, max_num=3, can_delete=False)

    if request.method == 'POST':
        post_form = PostEditForm(instance=post, data=request.POST)
        media_formset = MediaFormset(instance=post, data=request.POST, files=request.FILES, prefix='media')
        attachment_formset = AttachmentFormset(instance=post, data=request.POST, files=request.FILES, prefix='attachment')
    else:
        post_form = PostEditForm(instance=post)
        media_formset = MediaFormset(instance=post)
        attachment_formset = AttachmentFormset(instance=post)

    if post_form.is_valid() and media_formset.is_valid() and attachment_formset.is_valid():
        post = post_form.save(commit=False)
        media_set = media_formset.save(commit=False)
        attachment_set = attachment_formset.save(commit=False)

        post.is_approved = post.author.posts.exclude(id=post.id).filter(is_approved=True).exists() and not len(media_set) and not len(attachment_set)
        post.save()

        for media in media_set:
            media.save()

        for attachment in attachment_set:
            attachment.save()

        if not post.is_approved:
            notification_post_moderation_pending.apply_async(countdown=1, kwargs={'post_id': post.id, 'mode': 'approval'})
            messages.info(request, _('<strong>Thanks</strong>, your comment has successfully been edited but requires approval.<br />' \
                                     'You will be informed via email once it has been reviewed and approved.'))
        else:
            messages.success(request, _('<strong>Great</strong>, your comment has successfully been edited.'))

        return HttpResponseRedirect(post.get_absolute_url())

    template_values = {
        'category': category,
        'post_form': post_form,
        'media_formset': media_formset,
        'attachment_formset': attachment_formset,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))


@login_required
def vote_post(request, category, thread_id, post_id, mode):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    modes = {'up': 1, 'down': -1}

    try:
        vote = Vote.objects.get(user=request.user, post=post)
        vote.delete()
    except Vote.DoesNotExist:
        vote = Vote(user=request.user, post=post, mode=modes[mode])
        vote.save()

    vote_sum = post.vote_sum
    if vote_sum:
        was_flagged_post = post.is_flagged
        was_highlighted_post = post.is_highlighted

        post.is_flagged = vote_sum <= -3
        post.is_highlighted = vote_sum >= 3
        post.save(update_fields=('is_flagged', 'is_highlighted'))

        if post.is_flagged and not was_flagged_post:
            notification_post_moderation_pending.delay(post_id=post.id, mode='flagged')
        if post.is_highlighted and not was_highlighted_post:
            notification_post_moderation_pending.delay(post_id=post.id, mode='highlighted')

    messages.success(request, _('<strong>Thanks</strong>, your vote has successfully been recorded.'))

    return HttpResponseRedirect(post.get_absolute_url())


@permission_required('comments.change_post')
def approve_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_approved = not(post.is_approved)
    post.save(update_fields=('is_approved', 'tstamp'))

    if post.is_approved:
        notification_post_approved.delay(post_id=post.id)
        notification_post_new_reply.delay(post_id=post.id)
        messages.success(request, _('<strong>Great</strong>, the post has successfully been approved.'))
    else:
        messages.warning(request, _('<strong>Careful</strong>, the post has now been disapproved.'))

    return HttpResponseRedirect(post.get_absolute_url())

@permission_required('comments.change_post')
def spam_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_spam = not(post.is_spam)
    post.save(update_fields=('is_spam', 'tstamp'))

    if post.is_spam:
        messages.warning(request, _('<strong>Careful</strong>, the post has successfully been marked as spam.'))
    else:
        messages.success(request, _('<strong>Great</strong>, the post has now been marked as no-spam.'))

    return HttpResponseRedirect(post.get_absolute_url())

@permission_required('comments.delete_post')
def delete_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_deleted = not(post.is_deleted)
    post.save(update_fields=('is_deleted', 'tstamp'))

    thread.is_deleted = not(thread.posts.exclude(is_deleted=True).exists())
    thread.save(update_fields=('is_deleted', 'tstamp'))

    if post.is_deleted:
        messages.error(request, _('<strong>Careful</strong>, the post has successfully been marked as deleted.'))
    else:
        messages.success(request, _('<strong>Great</strong>, the post has now been marked as not-deleted.'))

    return HttpResponseRedirect(post.get_absolute_url())
