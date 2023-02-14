"""
URLConf for Django-Forum.

django-forum assumes that the forum application is living under
/forum/.

Usage in your base urls.py:
    url(r'^forum/', include('forum.urls')),

"""

from django.urls import re_path
from forum.feeds import RssForumFeed, AtomForumFeed
from forum.sitemap import ForumSitemap, ThreadSitemap, PostSitemap
from forum.views import ForumList, ThreadList, PostList, thread

sitemap_dict = {
    'forums': ForumSitemap,
    'threads': ThreadSitemap,
    'posts': PostSitemap,
}

urlpatterns = [
    re_path(r'^$', ForumList.as_view(), name='forum_list'),
    re_path(r'^(?P<url>(rss).*)/$', RssForumFeed()),
    re_path(r'^(?P<url>(atom).*)/$', AtomForumFeed()),

    re_path(r'^(?P<slug>[-\w]+)/$', ThreadList.as_view(), name='forum_thread_list'),
    re_path(r'^(?P<forum>[-\w]+)/preview/$', thread, name='forum_preview_thread'),
    re_path(r'^(?P<forum>[-\w]+)/(?P<thread>[-\w]+)/edit/$', thread, name='forum_edit_thread'),

    re_path(r'^(?P<forum>[-\w]+)/(?P<thread>[-\w]+)/$', PostList.as_view(), name='forum_view_thread'),
]
