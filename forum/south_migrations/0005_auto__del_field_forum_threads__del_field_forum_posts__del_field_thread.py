# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Forum.threads'
        db.delete_column(u'forum_forum', 'threads')

        # Deleting field 'Forum.posts'
        db.delete_column(u'forum_forum', 'posts')

        # Deleting field 'Thread.site'
        db.delete_column(u'forum_thread', 'site_id')


    def backwards(self, orm):
        # Adding field 'Forum.threads'
        db.add_column(u'forum_forum', 'threads',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Forum.posts'
        db.add_column(u'forum_forum', 'posts',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Thread.site'
        raise RuntimeError("Cannot reverse this migration. 'Thread.site' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Thread.site'
        db.add_column(u'forum_thread', 'site',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site']),
                      keep_default=False)


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
        u'comments_app.tappedcomment': {
            'Meta': {'object_name': 'TappedComment', 'db_table': "'django_comments'"},
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type_set_for_tappedcomment'", 'to': u"orm['contenttypes.ContentType']"}),
            'edit_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_removed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_pk': ('django.db.models.fields.TextField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'tappedcomment_comments'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'wikicomment': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'forum.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'only_upgraders': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'forum.forum': {
            'Meta': {'ordering': "['ordering', 'title']", 'object_name': 'Forum'},
            'allowed_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'allowed_forums'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Category']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'only_staff_posts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'only_staff_reads': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'only_upgraders': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child'", 'null': 'True', 'to': u"orm['forum.Forum']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'forum.thread': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Thread'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'commentthread_set'", 'null': 'True', 'to': u"orm['comments_app.TappedComment']"}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Forum']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_post': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['comments_app.TappedComment']", 'null': 'True', 'blank': 'True'}),
            'posts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '105'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['forum']