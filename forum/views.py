"""
All forum logic is kept here - displaying lists of forums, threads
and posts, adding new threads, and adding replies.
"""

import time
from datetime import datetime, timedelta
from django.utils.timesince import timeuntil
from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from django.views.generic.list import ListView
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from forum.signals import thread_created

try:
    from django.contrib import comments
except ImportError:
    import django_comments as comments

from forum.models import Forum, Thread, Category, get_forum_cache
from forum.forms import ThreadForm, ReplyForm


FORUM_PAGINATION = getattr(settings, 'FORUM_PAGINATION', 20)
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')
FORUM_FLOOD_CONTROL = getattr(settings, 'FORUM_FLOOD_CONTROL', {})
FORUM_POST_EXPIRE_IN = getattr(settings, 'FORUM_POST_EXPIRE_IN', 0)


class ForumList(ListView):
    def get_queryset(self):
        return Forum.objects.for_user(
            self.request.user).filter(restricted=False, parent__isnull=True, site=settings.SITE_ID)

    def get_context_data(self, **kwargs):
        context = super(ForumList, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated() and hasattr(user, 'userprofile') and getattr(user.userprofile, 'is_upgraded', False):
            categories = Category.objects.all()
        else:
            categories = Category.objects.filter(only_upgraders=False)
        context['categories'] = categories
        if self.request.user.is_authenticated():
            context['restricted_forums'] = [i.forum for i in Forum.allowed_users.through.objects.filter(
                user=self.request.user)]
        for item in self.get_queryset():
            context["%s_forum" % item.slug.replace('-', '_')] = item
        return context


class ThreadList(ListView):
    template_object_name = 'thread',
    paginate_by = FORUM_PAGINATION

    def get_template_names(self):
        return [
            'forum/%s_thread_list.html' % self.forum.slug,
            'forum/thread_list.html',
        ]

    def get_queryset(self, sticky=False):
        try:
            self.forum = Forum.objects.for_user(
                self.request.user).select_related().get(slug=self.kwargs.get('slug'), site=settings.SITE_ID)
            if self.forum.restricted:
                if not self.request.user.is_authenticated() or self.request.user not in self.forum.allowed_users.all():
                    raise Http404
        except Forum.DoesNotExist:
            raise Http404
        return self.forum.thread_set.filter(sticky=sticky)

    def get_context_data(self, **kwargs):
        context = super(ThreadList, self).get_context_data(**kwargs)
        post_title, post_url, expire_date = '', '', None
        form = ThreadForm(user=self.request.user)

        cache = get_forum_cache()
        if self.request.user.is_authenticated() and cache:
            user = self.request.user
            key = make_cache_forum_key(user, self.forum.slug, settings.SITE_ID)
            try:
                from_cache = cache.get(key)
            except Exception:
                raise Exception("No fuckin idea %s" % key)
            if from_cache:
                post_title, post_url, expire_date = from_cache
                expire_date = datetime.fromtimestamp(expire_date)
                form = None

        recent_threads = [i for i in self.get_queryset()[:30] if i.posts > 0][:10]
        active_threads = Thread.nonrel_objects.get_list("%s-latest-threads" % self.forum.slug, limit=10)
        sticky_threads = self.get_queryset(sticky=True)
        context.update({
            'forum': self.forum,
            'active_threads': active_threads,
            'recent_threads': recent_threads,
            'sticky_threads': sticky_threads,
            'form': form,
            'last_post_title': post_title,
            'last_post_url': post_url,
            'last_post_expiry': expire_date
        })
        return context


class PostList(ListView):
    template_object_name = 'post'
    paginate_by = FORUM_PAGINATION
    model = comments.get_model()

    def get_template_names(self):
        return [
            'forum/%s_thread.html' % self.object.forum.slug,
            'forum/thread.html',
        ]

    def get(self, *args, **kwargs):
        re = super(PostList, self).get(*args, **kwargs)
        if self.object.forum.slug != self.kwargs.get('forum'):
            return HttpResponseRedirect(self.object.get_absolute_url())
        return re

    def get_queryset(self, **kwargs):
        self.object = get_object_or_404(Thread, slug=self.kwargs.get('thread'), forum__site=settings.SITE_ID)
        if not Forum.objects.has_access(self.object.forum, self.request.user):
            raise Http404
        Post = comments.get_model()
        return Post.objects.filter(
            content_type=ContentType.objects.get_for_model(Thread),
            object_pk=self.object.pk).order_by('submit_date')

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data(**kwargs)
        s = None

        if s:
            initial = {'subscribe': True}
        else:
            initial = {'subscribe': False}

        form = None
        if self.request.user.is_authenticated() and self.request.user not in self.object.banned_users.all():
            form = ReplyForm(initial=initial)

        context.update({
            'thread': self.object,
            'forum': self.object.forum,
            'subscription': s,
            'form': form,
        })
        return context


def make_cache_forum_key(user, forum, key_prefix=''):
    k = ':'.join([str(key_prefix), str(forum), user.username]).replace(' ', '-')
    # avoid encoding problems with memcache
    return k.encode('ascii', 'replace')


def get_forum_expire_datetime(forum, start=None):
    if forum in FORUM_FLOOD_CONTROL:
        expire_in = FORUM_FLOOD_CONTROL.get(forum, FORUM_POST_EXPIRE_IN)
        start = start or datetime.now()
        expire_datetime = start + timedelta(seconds=expire_in)
        return time.mktime(expire_datetime.timetuple())


def thread(request, forum, thread=None):
    instance = None
    if thread:
        instance = get_object_or_404(Thread, slug=thread, forum__slug=forum,
                                     forum__site=settings.SITE_ID)
    f_instance = get_object_or_404(Forum, slug=forum, site=settings.SITE_ID)

    def can_post(forum, user):
        if forum.only_staff_posts:
            return user.is_authenticated() and user.is_staff
        if forum.only_upgraders:
            return user.is_authenticated() and (user.is_staff or (hasattr(user, 'userprofile') and
                                                                getattr(user.userprofile, 'is_upgraded', False)))
        return user.is_authenticated()

    if not can_post(f_instance, request.user):
        return HttpResponseForbidden()

    if not Forum.objects.has_access(f_instance, request.user):
        return HttpResponseForbidden()

    if not request.user.is_authenticated():
        if instance and instance.comment and instance.comment.user != request.user:
            return HttpResponseForbidden()

    form = ThreadForm(request.POST or None, instance=instance, user=request.user, forum=f_instance)

    # If previewing, render preview and form.
    if "preview" in request.POST:
        if form.is_valid():
            data = form.cleaned_data
        else:
            data = form.data

        return render(
            request,
            'forum/previewthread.html',
            {
                'form': form,
                'thread': Thread(
                    title=data.get('title') or form.initial.get('title') or '',
                    forum=f_instance),
                'forum': f_instance,
                'instance': instance,
                'comment': data.get('body') or form.initial.get('body') or '',
            })

    if request.method == "POST" and form.is_valid():
        if not thread:
            cache = get_forum_cache()
            key = make_cache_forum_key(request.user, forum, settings.SITE_ID)

            if cache and forum in FORUM_FLOOD_CONTROL:
                if cache.get(key):
                    post_title, post_url, expiry = cache.get(key)
                    expiry = timeuntil(datetime.fromtimestamp(expiry))
                    messages.error(request, "You can't post a thread in the forum %s for %s." %
                                            (f_instance.title, expiry))

                    return HttpResponseRedirect(post_url)
        instance = form.save()
        if not thread:
            Thread.nonrel_objects.push_to_list('%s-latest-comments' % f_instance.slug, instance, trim=30)
            thread_created.send(sender=Thread, instance=instance, author=request.user)
        return HttpResponseRedirect(instance.get_absolute_url())

    if hasattr(form, 'cleaned_data'):
        preview_comment = form.cleaned_data.get('body')
    else:
        preview_comment = form.data.get('body') or form.initial.get('body') or ''

    preview_instance = None
    if not instance:
        if hasattr(form, 'cleaned_data'):
            title = form.cleaned_data.get('title') or ''
        else:
            title = form.data.get('title') or form.initial.get('title') or ''
        preview_instance = Thread(
            title=title,
            forum=f_instance)

    return render(
        request,
        'forum/previewthread.html',
        {
            'form': form,
            'thread': preview_instance or instance,
            'forum': f_instance,
            'comment': preview_comment or '',
            })
