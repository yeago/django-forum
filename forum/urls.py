"""
URLConf for Django-Forum.

django-forum assumes that the forum application is living under
/forum/.

Usage in your base urls.py:
    url(r'^forum/', include('forum.urls')),

"""

from django.conf.urls import url
from forum.feeds import RssForumFeed, AtomForumFeed
from forum.sitemap import ForumSitemap, ThreadSitemap, PostSitemap
from forum.views import ForumList, ThreadList, PostList, thread

sitemap_dict = {
    'forums': ForumSitemap,
    'threads': ThreadSitemap,
    'posts': PostSitemap,
}

urlpatterns = [
    url(r'^$', ForumList.as_view(), name='forum_list'),
    url(r'^(?P<url>(rss).*)/$', RssForumFeed()),
    url(r'^(?P<url>(atom).*)/$', AtomForumFeed()),

    url(r'^(?P<slug>[-\w]+)/$', ThreadList.as_view(), name='forum_thread_list'),
    url(r'^(?P<forum>[-\w]+)/preview/$', thread, name='forum_preview_thread'),
    url(r'^(?P<forum>[-\w]+)/(?P<thread>[-\w]+)/edit/$', thread, name='forum_edit_thread'),

    url(r'^(?P<forum>[-\w]+)/(?P<thread>[-\w]+)/$', PostList.as_view(), name='forum_view_thread'),
]
