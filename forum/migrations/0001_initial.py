# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comments_app', '0002_auto_20151104_2141'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('only_upgraders', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=250)),
                ('slug', models.SlugField()),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('slug', models.SlugField(verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description')),
                ('ordering', models.IntegerField(null=True, verbose_name='Ordering', blank=True)),
                ('only_staff_posts', models.BooleanField(default=False)),
                ('only_staff_reads', models.BooleanField(default=False)),
                ('only_upgraders', models.BooleanField(default=False)),
                ('allowed_users', models.ManyToManyField(help_text=b'Ignore if non-restricted', related_name='allowed_forums', to=settings.AUTH_USER_MODEL, blank=True)),
                ('category', models.ForeignKey(blank=True, to='forum.Category', null=True)),
                ('parent', models.ForeignKey(related_name='child', blank=True, to='forum.Forum', null=True)),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
            options={
                'ordering': ['ordering', 'title'],
                'verbose_name': 'Forum',
                'verbose_name_plural': 'Forums',
            },
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('slug', models.SlugField(max_length=105, verbose_name='Slug')),
                ('sticky', models.BooleanField(default=False, verbose_name='Sticky?')),
                ('closed', models.BooleanField(default=False, verbose_name='Closed?')),
                ('posts', models.IntegerField(default=0, verbose_name='Posts')),
                ('views', models.IntegerField(default=0, verbose_name='Views')),
                ('comment', models.ForeignKey(related_name='commentthread_set', blank=True, to='comments_app.TappedComment', null=True)),
                ('forum', models.ForeignKey(to='forum.Forum')),
                ('latest_post', models.ForeignKey(blank=True, editable=False, to='comments_app.TappedComment', null=True)),
            ],
            options={
                'ordering': ('-id',),
                'verbose_name': 'Thread',
                'verbose_name_plural': 'Threads',
            },
        ),
    ]
