# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from ...models import Author, Thread, Post, Vote
import xml.etree.ElementTree as ET

class Command(BaseCommand):
    args = '<disqus-export-file.xml>'
    help = 'Import Disqus comments from XML export file'

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Missing argument: <disqus-export-file.xml>')

        with open(args[0], 'r') as disqus_file:
            disqus_tree = ET.parse(disqus_file)
            disqus_root = disqus_tree.getroot()

            self.handle_post(disqus_root)

        self.stdout.write('Successfully imported Disqus comments from XML export file')

    def handle_post(self, disqus_root, parent_id=None, depth=0):
        for post_item in disqus_root.findall('{http://disqus.com}post'):
            post_parent_item = post_item.find('{http://disqus.com}parent')
            if not post_parent_item is None:
                post_parent_id = post_parent_item.attrib['{http://disqus.com/disqus-internals}id']
            else:
                post_parent_id = None

            if post_parent_id == parent_id:
                post_id = post_item.attrib['{http://disqus.com/disqus-internals}id']

                post_message_item = post_item.find('{http://disqus.com}message')
                post_message_text = post_message_item.text.encode('utf-8')

                post_is_deleted_item = post_item.find('{http://disqus.com}isDeleted')
                post_is_deleted_bool = post_is_deleted_item.text in ('true', '1', True, 1) if post_is_deleted_item else False

                post_is_approved_item = post_item.find('{http://disqus.com}isApproved')
                post_is_approved_bool = post_is_approved_item.text in ('true', '1', True, 1) if post_is_approved_item else True

                post_is_flagged_item = post_item.find('{http://disqus.com}isFlagged')
                post_is_flagged_bool = post_is_flagged_item.text in ('true', '1', True, 1) if post_is_flagged_item else False

                post_is_spam_item = post_item.find('{http://disqus.com}isSpam')
                post_is_spam_bool = post_is_spam_item.text in ('true', '1', True, 1) if post_is_spam_item else False

                post_is_highlighted_item = post_item.find('{http://disqus.com}isHighlighted')
                post_is_highlighted_bool = post_is_highlighted_item.text in ('true', '1', True, 1) if post_is_highlighted_item else False

                print '\t'*depth, post_id, post_message_text

                self.handle_post(disqus_root, post_id, depth+1)
