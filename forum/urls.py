"""
URLConf for Django-Forum.

django-forum assumes that the forum application is living under
/forum/.

Usage in your base urls.py:
    (r'^forum/', include('forum.urls')),

"""

from django.conf.urls.defaults import patterns, url
from forum.feeds import RssForumFeed, AtomForumFeed
from forum.sitemap import ForumSitemap, ThreadSitemap, PostSitemap
from forum.views import ForumList, ThreadList, PostList

sitemap_dict = {
    'forums': ForumSitemap,
    'threads': ThreadSitemap,
    'posts': PostSitemap,
}

urlpatterns = patterns('',
    url(r'^$', ForumList.as_view(), name='forum_list'),
    (r'^(?P<url>(rss).*)/$', RssForumFeed()),
    (r'^(?P<url>(atom).*)/$', AtomForumFeed()),
    url(r'^(?P<slug>[-\w]+)/$', ThreadList.as_view(), name='forum_thread_list'),
    url(r'^(?P<forum>[-\w]+)/new/$', 'forum.views.newthread', name='forum_new_thread'),
    url(r'^(?P<forum>[-\w]+)/preview/$', 'forum.views.previewthread', name='forum_preview_thread'),

    url(r'^(?P<forum>[-\w]+)/(?P<thread>[-\w]+)/$', PostList.as_view(), name='forum_view_thread'),

    url(r'^([-\w/]+/)(?P<forum>[-\w]+)/new/$', 'forum.views.newthread'),
    url(r'^([-\w/]+/)(?P<forum>[-\w]+)/preview/$', 'forum.views.previewthread'),
    #url(r'^([-\w/]+/)(?P<slug>[-\w]+)/$', 'forum.views.forum', name='forum_subforum_thread_list'),

    (r'^sitemap.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemap_dict}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap_dict}),
)
