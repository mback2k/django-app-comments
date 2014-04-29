# -*- coding: utf-8 -*-
from django.utils import text
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from ...models import Author, Thread, Post, Vote
import xml.etree.ElementTree as ET
import isodate

class Command(BaseCommand):
    args = '<disqus-export-file.xml>'
    help = 'Import Disqus comments from XML export file'

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Missing argument: <disqus-export-file.xml>')

        with open(args[0], 'r') as disqus_file:
            disqus_tree = ET.parse(disqus_file)
            disqus_root = disqus_tree.getroot()

            with transaction.atomic():
                self.handle_post(disqus_root)

        self.stdout.write('Successfully imported Disqus comments from XML export file')

    def handle_post(self, disqus_root, parent_id=None, parent=None, depth=0):
        for post_item in disqus_root.findall('{http://disqus.com}post'):
            post_parent_item = post_item.find('{http://disqus.com}parent')
            if not post_parent_item is None:
                post_parent_id = post_parent_item.attrib['{http://disqus.com/disqus-internals}id']
            else:
                post_parent_id = None

            if post_parent_id == parent_id:
                post_id = post_item.attrib['{http://disqus.com/disqus-internals}id']

                print '\t'*depth, post_id

                post_message_text = self.get_value_text(post_item, '{http://disqus.com}message')
                post_created_datetime = self.get_value_datetime(post_item, '{http://disqus.com}createdAt')

                post_is_deleted_bool     = self.get_value_bool(post_item, '{http://disqus.com}isDeleted',     False)
                post_is_approved_bool    = self.get_value_bool(post_item, '{http://disqus.com}isApproved',    True )
                post_is_flagged_bool     = self.get_value_bool(post_item, '{http://disqus.com}isFlagged',     False)
                post_is_spam_bool        = self.get_value_bool(post_item, '{http://disqus.com}isSpam',        False)
                post_is_highlighted_bool = self.get_value_bool(post_item, '{http://disqus.com}isHighlighted', False)

                post_author_item = post_item.find('{http://disqus.com}author')

                author = self.handle_author(post_id, post_author_item)

                if not parent is None:
                    thread = parent.thread
                else:
                    thread = Thread.objects.create(category='discussion')
                    thread.crdate = post_created_datetime
                    thread.save(update_fields=('crdate',))

                post = Post.objects.create(id=post_id, parent=parent, thread=thread, author=author,
                                           content=post_message_text, is_deleted=post_is_deleted_bool,
                                           is_approved=post_is_approved_bool, is_flagged=post_is_flagged_bool,
                                           is_spam=post_is_spam_bool, is_highlighted=post_is_highlighted_bool)
                post.crdate=post_created_datetime
                post.save(update_fields=('crdate',))

                self.handle_post(disqus_root, post_id, post, depth+1)

    def handle_author(self, post_id, author_item):
        author_name_text     = self.get_value_text(author_item, '{http://disqus.com}name'    )
        author_email_text    = self.get_value_text(author_item, '{http://disqus.com}email'   )
        author_username_text = self.get_value_text(author_item, '{http://disqus.com}username')

        try:
            if author_username_text:
                try:
                    author = Author.objects.get(username=author_username_text, is_active=True)
                except Author.DoesNotExist:
                    author = Author.objects.get(email=author_email_text, is_active=True)
                    author.username = author_username_text

            else:
                author = Author.objects.get(email=author_email_text, is_active=False)

            if author_email_text:
                author.email = author_email_text
            if author_name_text:
                author.first_name = author_name_text

            author.save()

        except Author.DoesNotExist:
            if author_username_text:
                is_active = True
            else:
                is_active = False
                author_username_text = u'disqus-%s-%s' % (post_id, text.slugify(author_name_text))

            author = Author.objects.create_user(username=author_username_text,
                                                email=author_email_text,
                                                first_name=author_name_text)

            if not is_active:
                author.is_active = is_active
                author.save(update_fields=('is_active',))

        print author.username
        return author

    def get_value_text(self, item, name, encoding='utf-8'):
        if not item is None and not name is None:
            item = item.find(name)
            if not item is None and not item.text is None:
                return unicode(item.text.encode(encoding), encoding=encoding)
        return None

    def get_value_bool(self, item, name, default):
        if not item is None and not name is None:
            item = item.find(name)
            if not item is None and not item.text is None:
                return item.text in ('true', '1', True, 1)
        return default

    def get_value_datetime(self, item, name):
        if not item is None and not name is None:
            item = item.find(name)
            if not item is None and not item.text is None:
                return isodate.parse_datetime(item.text)
        return None
