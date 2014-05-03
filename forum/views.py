"""
All forum logic is kept here - displaying lists of forums, threads 
and posts, adding new threads, and adding replies.
"""

from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from django.views.generic.list import ListView
from django.contrib.sites.models import Site
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.conf import settings

from forum.models import Forum, Thread
from forum.forms import CreateThreadForm, ReplyForm
from forum.signals import thread_created


FORUM_PAGINATION = getattr(settings, 'FORUM_PAGINATION', 20)
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/accounts/login/')


class ForumList(ListView):
    def get_queryset(self):
        return Forum.objects.for_user(self.request.user).filter(parent__isnull=True, site=settings.SITE_ID)


class ThreadList(ListView):
    template_object_name='thread',
    template_name='forum/thread_list.html'
    paginate_by = FORUM_PAGINATION
    def get_queryset(self):
        try:
            self.f = Forum.objects.for_user(self.request.user).select_related().get(slug=self.kwargs.get('slug'), site=settings.SITE_ID)
        except Forum.DoesNotExist:
            raise Http404
        return self.f.thread_set.select_related('latest_post').order_by('-latest_post__submit_date')

    def get_context_data(self, **kwargs):
        context = super(ThreadList, self).get_context_data(**kwargs)

        form = CreateThreadForm()
        #child_forums = f.child.for_groups(request.user.groups.all())

        recent_threads = self.f.thread_set.filter(posts__gt=0).order_by('-id')[:10]
        active_threads = self.f.thread_set.select_related('latest_post').filter(latest_post__submit_date__gt=\
                datetime.now() - timedelta(hours=36)).order_by('-posts')[:10]

        context.update({
            'forum': self.f,
            'active_threads': active_threads,
            'recent_threads': recent_threads,
            'form': form,
        })
        return context


class PostList(ListView):
    template_object_name='post'
    template_name='forum/thread.html'
    paginate_by=FORUM_PAGINATION
    model = comments.get_model()
    def get_queryset(self, **kwargs):
        self.object = get_object_or_404(Thread, slug=self.kwargs.get('thread'))
        if not Forum.objects.has_access(self.object.forum, self.request.user):
            raise Http404
        Post = comments.get_model()
        return Post.objects.exclude(pk=self.object.comment_id).filter(content_type=\
            ContentType.objects.get_for_model(Thread), object_pk=self.object.pk).order_by('submit_date')

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
       
