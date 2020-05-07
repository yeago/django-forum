# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.COMMENTS_MODEL),
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
                ('category', models.ForeignKey(blank=True, to='forum.Category', null=True, on_delete=models.deletion.SET_NULL)),
                ('parent', models.ForeignKey(related_name='child', blank=True, to='forum.Forum', null=True, on_delete=models.deletion.SET_NULL)),
                ('site', models.ForeignKey(to='sites.Site', on_delete=models.deletion.CASCADE)),
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
                ('comment', models.ForeignKey(related_name='commentthread_set', blank=True, to=settings.COMMENTS_MODEL, null=True, on_delete=models.deletion.SET_NULL)),
                ('forum', models.ForeignKey(to='forum.Forum', on_delete=models.deletion.CASCADE)),
                ('latest_post', models.ForeignKey(blank=True, editable=False, to=settings.COMMENTS_MODEL, null=True, on_delete=models.deletion.SET_NULL)),
            ],
            options={
                'ordering': ('-id',),
                'verbose_name': 'Thread',
                'verbose_name_plural': 'Threads',
            },
        ),
    ]
