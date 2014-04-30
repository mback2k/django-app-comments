# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import messages
from .models import User, Author, Thread, Post, Vote
from .forms import PostNewForm, PostReplyForm, PostEditForm
from .tasks import notification_post_approval_pending, notification_post_approved, notification_post_new_reply

def show_threads(request, category):
    if request.user.has_perm('comments.change_post') or request.user.has_perm('comments.delete_post'):
        thread_list = Thread.objects.filter(category=category).exclude(is_deleted=True)
    else:
        thread_list = Thread.objects.filter(category=category)

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

def show_posts(request, category, thread_id):
    if request.user.has_perm('comments.change_post') or request.user.has_perm('comments.delete_post'):
        thread = get_object_or_404(Thread, category=category, id=thread_id)
    else:
        thread = get_object_or_404(Thread, category=category, id=thread_id, is_deleted=False)

    template_values = {
        'category': category,
        'thread': thread,
    }

    return render_to_response('show_posts.html', template_values, context_instance=RequestContext(request))

@login_required
def new_post(request, category):
    if request.method == 'POST':
        post_form = PostNewForm(data=request.POST)
    else:
        post_form = PostNewForm()

    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.thread = Thread.objects.create(category=category)
        post.author = Author.objects.get(pk=request.user.pk)
        post.is_approved = post.author.posts.filter(is_approved=True).exists()
        post.clean_content(commit=False)
        post.save()

        if not post.is_approved:
            notification_post_approval_pending.delay(post_id=post.id)

        return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

    template_values = {
        'category': category,
        'post_form': post_form,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))

@login_required
def reply_post(request, category, thread_id, parent_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    parent = get_object_or_404(Post, thread=thread, id=parent_id)

    if request.method == 'POST':
        post_form = PostReplyForm(data=request.POST)
    else:
        post_form = PostReplyForm(initial={'parent': parent, 'thread': thread})

    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.author = Author.objects.get(pk=request.user.pk)
        post.is_approved = post.author.posts.filter(is_approved=True).exists()
        post.clean_content(commit=False)
        post.save()

        if not post.is_approved:
            notification_post_approval_pending.delay(post_id=post.id)
        else:
            notification_post_new_reply.delay(post_id=post.id)

        return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

    template_values = {
        'category': category,
        'post_form': post_form,
        'thread': thread,
        'parent': parent,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))

@login_required
def edit_post(request, category, thread_id, post_id):
    author = Author.objects.get(pk=request.user.pk)
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, author=author, id=post_id)

    if not post.is_editable:
        return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

    if request.method == 'POST':
        post_form = PostEditForm(instance=post, data=request.POST)
    else:
        post_form = PostEditForm(instance=post)

    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.clean_content(commit=False)
        post.save()
        return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

    template_values = {
        'category': category,
        'post_form': post_form,
    }

    return render_to_response('edit_post.html', template_values, context_instance=RequestContext(request))

@login_required
def vote_post(request, category, thread_id, post_id, mode):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    modes = {'up': 1, 'down': -1}

    try:
        vote = Vote.objects.get(user=request.user, post=post)
        vote.mode = modes[mode]
    except Vote.DoesNotExist:
        vote = Vote(user=request.user, post=post, mode=modes[mode])
    vote.save()

    return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

@permission_required('comments.change_post')
def approve_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_approved = not(post.is_approved)
    post.save()

    if post.is_approved:
        notification_post_approved.delay(post_id=post.id)
        notification_post_new_reply.delay(post_id=post.id)

    return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

@permission_required('comments.change_post')
def spam_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_spam = not(post.is_spam)
    post.save()

    return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))

@permission_required('comments.delete_post')
def delete_post(request, category, thread_id, post_id):
    thread = get_object_or_404(Thread, category=category, id=thread_id)
    post = get_object_or_404(Post, thread=thread, id=post_id)

    post.is_deleted = not(post.is_deleted)
    post.save()

    return HttpResponseRedirect(reverse('comments:show_posts', kwargs={'category': category, 'thread_id': post.thread.id}))
