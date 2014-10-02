# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Thread'
        db.create_table(u'comments_thread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(default='discussion', max_length=20)),
            ('crdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('tstamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'comments', ['Thread'])

        # Adding model 'Post'
        db.create_table(u'comments_post', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='posts', null=True, to=orm['comments.Post'])),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['comments.Thread'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['auth.User'])),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('crdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('tstamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('edited', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_flagged', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_spam', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_highlighted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'comments', ['Post'])

        # Adding model 'Vote'
        db.create_table(u'comments_vote', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['comments.Post'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['auth.User'])),
            ('mode', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'comments', ['Vote'])

        # Adding unique constraint on 'Vote', fields ['post', 'user']
        db.create_unique(u'comments_vote', ['post_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Vote', fields ['post', 'user']
        db.delete_unique(u'comments_vote', ['post_id', 'user_id'])

        # Deleting model 'Thread'
        db.delete_table(u'comments_thread')

        # Deleting model 'Post'
        db.delete_table(u'comments_post')

        # Deleting model 'Vote'
        db.delete_table(u'comments_vote')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'comments.post': {
            'Meta': {'ordering': "('-crdate', '-tstamp')", 'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'crdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'edited': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_flagged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_highlighted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_spam': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'posts'", 'null': 'True', 'to': u"orm['comments.Post']"}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['comments.Thread']"}),
            'tstamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'comments.thread': {
            'Meta': {'ordering': "('-crdate', '-tstamp')", 'object_name': 'Thread'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'discussion'", 'max_length': '20'}),
            'crdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tstamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'comments.vote': {
            'Meta': {'unique_together': "(('post', 'user'),)", 'object_name': 'Vote'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode': ('django.db.models.fields.SmallIntegerField', [], {}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['comments.Post']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': u"orm['auth.User']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['comments']