# -*- coding: utf-8 -*-
from django.db import transaction
from django.utils import timezone, text
from django.core.management.base import BaseCommand, CommandError
from social.apps.django_app.default.models import UserSocialAuth
from ...models import User, Author, Thread, Post, Vote
from disqusapi import DisqusAPI
import isodate

class Command(BaseCommand):
    args = '<disqus-forum> <secret-key> <public-key>'
    help = 'Import Disqus comments and authors from JSON API'

    def handle(self, *args, **options):
        if len(args) < 3:
            raise CommandError('Missing arguments: <disqus-forum> <secret-key> <public-key>')

        disqus_api = DisqusAPI(args[1], args[2])
        disqus_forum = args[0]
        disqus_posts_include = ('unapproved', 'approved', 'spam', 'deleted', 'flagged', 'highlighted')
        disqus_posts = disqus_api.posts.list(forum=disqus_forum,
                                             include=disqus_posts_include,
                                             order='asc')

        disqus_posts_list = []
        while len(disqus_posts):
            disqus_posts_list += disqus_posts.response
            print 'Fetched', len(disqus_posts_list), 'posts'
            if disqus_posts.cursor.get('hasNext', False):
                print 'Fetching more posts'
                disqus_posts = disqus_api.posts.list(forum=disqus_forum,
                                                     include=disqus_posts_include,
                                                     order='asc',
                                                     cursor=disqus_posts.cursor.get('next'))
            else:
                break

        with transaction.atomic():
            self.handle_post(disqus_posts_list)

        self.stdout.write('Successfully imported Disqus comments and authors from JSON API')

    def handle_post(self, disqus_posts_list, parent_id=None, parent=None, depth=0):
        for disqus_post in disqus_posts_list:
            post_parent_id = disqus_post.get('parent', None)
            if post_parent_id:
                post_parent_id = int(post_parent_id)
            if post_parent_id == parent_id:
                post_id = int(disqus_post.get('id'))

                print '\t'*depth, post_id

                post_message = disqus_post.get('message')
                post_created = disqus_post.get('createdAt')

                post_is_deleted     = disqus_post.get('isDeleted',     False)
                post_is_approved    = disqus_post.get('isApproved',    True )
                post_is_flagged     = disqus_post.get('isFlagged',     False)
                post_is_spam        = disqus_post.get('isSpam',        False)
                post_is_highlighted = disqus_post.get('isHighlighted', False)

                disqus_author = disqus_post.get('author')

                author = self.handle_author(post_id, disqus_author)

                if not parent is None:
                    thread = parent.thread
                else:
                    thread = Thread.objects.create(category='discussion')
                    thread.crdate = self.parse_datetime(post_created)
                    thread.save(update_fields=('crdate',))

                post = Post.objects.create(id=post_id, parent=parent, thread=thread, author=author,
                                           content=post_message, is_deleted=post_is_deleted,
                                           is_approved=post_is_approved, is_flagged=post_is_flagged,
                                           is_spam=post_is_spam, is_highlighted=post_is_highlighted)
                post.crdate = self.parse_datetime(post_created)
                post.save(update_fields=('crdate',))

                self.handle_post(disqus_posts_list, post_id, post, depth+1)

    def handle_author(self, post_id, disqus_author):
        author_name         = disqus_author.get('name'       )
        author_id           = disqus_author.get('id'         , None)
        author_username     = disqus_author.get('username'   , None)
        author_is_anonymous = disqus_author.get('isAnonymous', True)
        author_joined       = disqus_author.get('joinedAt'   , None)

        if author_is_anonymous:
            author_username = u'anonymous-%d' % post_id
            author = Author.objects.create_user(username=author_username,
                                                first_name=author_name)
            author.is_active = False
            author.save(update_fields=('is_active',))

            return author

        try:
            author = Author.objects.get(id=int(author_id),
                                        username=author_username,
                                        is_active=True)

        except Author.DoesNotExist:
            author = Author.objects.create_user(id=int(author_id),
                                                username=author_username,
                                                first_name=author_name)
            author.date_joined = self.parse_datetime(author_joined)
            author.save(update_fields=('date_joined',))

            user = User.objects.get(id=author.id)
            UserSocialAuth.objects.create(user=user,
                                          provider='disqus',
                                          uid=author_id)

        print author.username
        return author

    def parse_datetime(self, datetime):
        return timezone.make_aware(isodate.parse_datetime(datetime), timezone.utc)
