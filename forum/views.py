"""
All forum logic is kept here - displaying lists of forums, threads 
and posts, adding new threads, and adding replies.
"""

import time
from datetime import datetime, timedelta
from django.utils.timesince import timeuntil
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from django.views.generic.list import ListView
from django.contrib.sites.models import Site
from django.contrib import comments, messages
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.cache import get_cache, InvalidCacheBackendError, ImproperlyConfigured

from forum.models import Forum, Thread
from forum.forms import CreateThreadForm, ReplyForm
from forum.signals import thread_created


FORUM_PAGINATION = getattr(settings, 'FORUM_PAGINATION', 20)
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')
FORUM_FLOOD_CONTROL = getattr(settings, 'FORUM_FLOOD_CONTROL', {})
FORUM_POST_EXPIRE_IN = getattr(settings, 'FORUM_POST_EXPIRE_IN', 0)


def get_forum_cache():
    try:
        cache = get_cache('forum')
    except (InvalidCacheBackendError, ImproperlyConfigured):
        cache = None
    return cache


class ForumList(ListView):
    def get_queryset(self):
        return Forum.objects.for_user(self.request.user).filter(parent__isnull=True, site=settings.SITE_ID)


class ThreadList(ListView):
    template_object_name='thread',
    template_name='forum/thread_list.html'
    paginate_by = FORUM_PAGINATION
    def get_queryset(self):
        try:
            self.f = Forum.objects.for_user(self.request.user
                    ).select_related().get(slug=self.kwargs.get('slug'), site=settings.SITE_ID)
        except Forum.DoesNotExist:
            raise Http404
        return self.f.thread_set.all()

    def get_context_data(self, **kwargs):
        context = super(ThreadList, self).get_context_data(**kwargs)
        post_title, post_url, expire_date = '', '', None
        form = CreateThreadForm()

        cache = get_forum_cache()
        if self.request.user.is_authenticated() and cache:
            user = self.request.user
            key = make_cache_forum_key(user, self.f.slug, settings.SITE_ID)
            try:
                from_cache = cache.get(key)
            except Exception:
                raise Exception("No fuckin idea %s" % key)
            if from_cache:
                post_title, post_url, expire_date = from_cache
                expire_date = datetime.fromtimestamp(expire_date)
                form = None
        #child_forums = f.child.for_groups(request.user.groups.all())

        recent_threads = [i for i in self.get_queryset()[:30] if i.posts > 0][:10]
        active_threads = Thread.nonrel_objects.get_list("%s-latest-threads" % self.f.slug, limit=10)
        context.update({
            'forum': self.f,
            'active_threads': active_threads,
            'recent_threads': recent_threads,
            'form': form,
            'last_post_title': post_title,
            'last_post_url': post_url,
            'last_post_expiry': expire_date
        })
        return context


class PostList(ListView):
    template_object_name='post'
    template_name='forum/thread.html'
    paginate_by=FORUM_PAGINATION
    model = comments.get_model()
    def get_queryset(self, **kwargs):
        self.object = get_object_or_404(Thread, slug=self.kwargs.get('thread'), forum__site=settings.SITE_ID)
        if not Forum.objects.has_access(self.object.forum, self.request.user):
            raise Http404
        Post = comments.get_model()
        return Post.objects.exclude(pk=self.object.comment_id).filter(
            content_type=ContentType.objects.get_for_model(Thread),
            object_pk=self.object.pk).order_by('submit_date')

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data(**kwargs)
        s = None

        if s:
            initial = {'subscribe': True}
        else:
            initial = {'subscribe': False}

        form = ReplyForm(initial=initial)
        context.update({
            'thread': self.object,
            'forum': self.object.forum,
            'subscription': s,
            'form': form,
        })
        return context


def make_cache_forum_key(user, forum, key_prefix=''):
    return ':'.join([str(key_prefix), str(forum), user.username]).replace(' ','-')


def get_forum_expire_datetime(forum, start=None):
    if forum in FORUM_FLOOD_CONTROL:
        expire_in = FORUM_FLOOD_CONTROL.get(forum, FORUM_POST_EXPIRE_IN)
        start = start or datetime.now()
        expire_datetime = start + timedelta(seconds=expire_in)
        return time.mktime(expire_datetime.timetuple())


def can_post(forum, user):
    if forum.only_staff_posts:
        return user.is_authenticated and user.is_staff
    return user.is_authenticated


def previewthread(request, forum):
    """
    Renders a preview of the new post and gives the user
    the option to modify it before posting. If called without
    a POST, redirects to newthread.

    Only allows a user to post if they're logged in.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, request.path))

    f = get_object_or_404(Forum, slug=forum, site=settings.SITE_ID)

    if not Forum.objects.has_access(f, request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        if not can_post(f, request.user):
            return HttpResponseForbidden
        cache = get_forum_cache()
        key = make_cache_forum_key(request.user, forum, settings.SITE_ID)

        if cache and forum in FORUM_FLOOD_CONTROL:
            if cache.get(key):
                post_title, post_url, expiry = cache.get(key)
                expiry = timeuntil(datetime.fromtimestamp(expiry))
                messages.error(request, "You can't post a thread in the forum %s for %s." %
                                        (f.title, expiry))

                return HttpResponseRedirect(post_url)

        form = CreateThreadForm(request.POST)
        if form.is_valid():
            t = Thread(
                forum=f,
                title=form.cleaned_data['title'],
            )
            Post = comments.get_model()
            ct = ContentType.objects.get_for_model(Thread)

            # If previewing, render preview and form.
            if "preview" in request.POST:
                return render_to_response('forum/previewthread.html',
                    RequestContext(request, {
                        'form': form,
                        'forum': f,
                        'thread': t,
                        'comment': form.cleaned_data['body'],
                        'user': request.user,
                    }))

            # No preview means we're ready to save the post.
            else:
                t.save()
                p = Post(
                    content_type=ct,
                    object_pk=t.pk,
                    user=request.user,
                    comment=form.cleaned_data['body'],
                    submit_date=datetime.now(),
                    site=Site.objects.get_current(),
                )
                p.save()
                t.latest_post = p
                t.comment = p
                t.save()
                Thread.nonrel_objects.push_to_list('%s-latest-comments' % t.forum.slug, t, trim=30)

                thread_created.send(sender=Thread, instance=t, author=request.user)
                if cache and forum in FORUM_FLOOD_CONTROL:
                    cache.set(key,
                              (t.title, t.get_absolute_url(), get_forum_expire_datetime(forum)),
                              FORUM_FLOOD_CONTROL.get(forum, FORUM_POST_EXPIRE_IN))

                return HttpResponseRedirect(t.get_absolute_url())

    else:
        form = CreateThreadForm()

    return render_to_response('forum/newthread.html',
        RequestContext(request, {
            'form': form,
            'forum': f, 
        }))

def newthread(request, forum):
    """
    Rudimentary post function - this should probably use 
    newforms, although not sure how that goes when we're updating 
    two models.

    Only allows a user to post if they're logged in.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, request.path))

    f = get_object_or_404(Forum, slug=forum, site=settings.SITE_ID)
    
    if not Forum.objects.has_access(f, request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = CreateThreadForm(request.POST)
        """
        #shouldn't be able to post without previewing first
        if form.is_valid():
            t = Thread(
                forum=f,
                title=form.cleaned_data['title'],
            )
            t.save()
            Post = comments.get_model()
            ct = ContentType.objects.get_for_model(Thread)

            p = Post(
                content_type=ct,
                object_pk=t.pk,
                user=request.user,
                comment=form.cleaned_data['body'],
                submit_date=datetime.now(),
                site=Site.objects.get_current(),
            )
            p.save()
            t.latest_post = p
            t.comment = p
            t.save()
   
            " " "
            undecided
            if form.cleaned_data.get('subscribe', False):
                s = Subscription(
                    author=request.user,
                    thread=t
                    )
                s.save()
            " " "
            return HttpResponseRedirect(t.get_absolute_url())
        """
    else:
        form = CreateThreadForm()

    return render_to_response('forum/newthread.html',
        RequestContext(request, {
            'form': form,
            'forum': f,
        }))
