"""
All forum logic is kept here - displaying lists of forums, threads 
and posts, adding new threads, and adding replies.
"""

from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotAllowed
from django.template import RequestContext, Context, loader
from django import forms
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.defaultfilters import striptags, wordwrap
from django.contrib.sites.models import Site
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list

from forum.models import Forum,Thread
from forum.forms import CreateThreadForm, ReplyForm
from forum.signals import thread_created

FORUM_PAGINATION = getattr(settings, 'FORUM_PAGINATION', 20)
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')

def forums_list(request):
    queryset = Forum.objects.for_user(request.user).filter(parent__isnull=True)
    return object_list( request,
                        queryset=queryset)

def forum(request, slug):
    """
    Displays a list of threads within a forum.
    Threads are sorted by their sticky flag, followed by their 
    most recent post.
    """
    try:
        f = Forum.objects.for_user(request.user).select_related().get(slug=slug)
    except Forum.DoesNotExist:
        raise Http404

    form = CreateThreadForm()
    #child_forums = f.child.for_groups(request.user.groups.all())

    recent_threads = f.thread_set.filter(posts__gt=0).select_related().order_by('-id')[:10]
    active_threads = f.thread_set.select_related().filter(latest_post__submit_date__gt=\
            datetime.now() - timedelta(hours=36)).order_by('-posts')[:10]

    return object_list( request,
                        queryset=f.thread_set.select_related('forum').order_by('-latest_post__submit_date'),
                        paginate_by=FORUM_PAGINATION,
                        template_object_name='thread',
                        template_name='forum/thread_list.html',
                        extra_context = {
                            'forum': f,
                #'child_forums': child_forums,
                'active_threads': active_threads,
                'recent_threads': recent_threads,
                            'form': form,
                        })

def thread(request, forum, thread):
    """
    Increments the viewed count on a thread then displays the 
    posts for that thread, in chronological order.
    """
    try:
        t = Thread.objects.select_related().get(slug=thread)
        if not Forum.objects.has_access(t.forum, request.user):
            raise Http404
    except Thread.DoesNotExist:
        raise Http404

    Post = comments.get_model()
    p = Post.objects.exclude(pk=t.comment_id).filter(content_type=\
        ContentType.objects.get_for_model(Thread),object_pk=t.pk).order_by('submit_date')
    s = None
    """
    not sure
    if request.user.is_authenticated():
        s = t.subscription_set.select_related().filter(author=request.user)
    """

    #t.views += 1
    #t.save()

    if s:
        initial = {'subscribe': True}
    else:
        initial = {'subscribe': False}

    form = ReplyForm(initial=initial)

    return object_list( request,
                        queryset=p,
                        page=request.GET.get('p',None) or None,
                        paginate_by=FORUM_PAGINATION,
                        template_object_name='post',
                        template_name='forum/thread.html',
                        extra_context = {
                            'forum': t.forum,
                            'thread': t,
                            'object': t,
                            'subscription': s,
                            'form': form,
                        })

def previewthread(request, forum):
    """
    Renders a preview of the new post and gives the user
    the option to modify it before posting. If called without
    a POST, redirects to newthread.

    Only allows a user to post if they're logged in.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, request.path))

    f = get_object_or_404(Forum, slug=forum)

    if not Forum.objects.has_access(f, request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
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

                thread_created.send(sender=Thread, instance=t, author=request.user)

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

    f = get_object_or_404(Forum, slug=forum)
    
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

def updatesubs(request):
    """
    Allow users to update their subscriptions all in one shot.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, request.path))

    subs = Subscription.objects.select_related().filter(author=request.user)

    if request.POST:
        # remove the subscriptions that haven't been checked.
        post_keys = [k for k in request.POST.keys()]
        for s in subs:
            if not str(s.thread.id) in post_keys:
                s.delete()
        return HttpResponseRedirect(reverse('forum_subscriptions'))

    return render_to_response('forum/updatesubs.html',
        RequestContext(request, {
            'subs': subs,
            'next': request.GET.get('next')
        }))
       
