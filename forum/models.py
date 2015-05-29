""" 
A basic forum model with corresponding thread/post models.

Just about all logic required for smooth updates is in the save() 
methods. A little extra logic is in views.py.
"""

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib import comments
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from django.contrib.comments.signals import comment_was_posted

from enuff.managers import EnuffManager

Comment = comments.get_model()
def update_thread(sender, request, **kwargs):
    instance = kwargs.get('comment')
    if instance.content_object.__class__ == Thread:
        x = instance.content_object
        x.latest_post = instance
        x.posts += 1
        x.save()
        x.forum.posts += 1
        x.forum.save()
        Thread.nonrel_objects.push_to_list("%s-latest-threads" % x.forum.slug, x, trim=25)

comment_was_posted.connect(update_thread,sender=Comment)

from forum.managers import ForumManager

class Forum(models.Model):
    """
    Very basic outline for a Forum, or group of threads. The threads
    and posts fielsd are updated by the save() methods of their
    respective models and are used for display purposes.

    All of the parent/child recursion code here is borrowed directly from
    the Satchmo project: http://www.satchmoproject.com/
    """
    allowed_users = models.ManyToManyField('auth.User',blank=True,related_name="allowed_forums",help_text="Ignore if non-restricted")
    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(_("Slug"))
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child')
    description = models.TextField(_("Description"))
    threads = models.IntegerField(_("Threads"), default=0, editable=False)
    posts = models.IntegerField(_("Posts"), default=0, editable=False)
    ordering = models.IntegerField(_("Ordering"), blank=True, null=True)
    site = models.ForeignKey('sites.Site')
    only_staff_posts = models.BooleanField(default=False)
    only_staff_reads = models.BooleanField(default=False)

    objects = ForumManager()

    def latest_threads(self, limit=10):
        return Thread.nonrel_objects.get_list('%s-latest-threads' % self.slug, limit=limit)

    def _get_forum_latest_post(self):
        """This gets the latest post for the forum"""
        if not hasattr(self, '__forum_latest_post'):
            Post = comments.get_model()
        ct = ContentType.objects.get_for_model(Forum)
        try:
            self.__forum_latest_post = Post.objects.filter(content_type=ct,object_pk=self.id).latest("submit_date")
        except Post.DoesNotExist:
            self.__forum_latest_post = None
        return self.__forum_latest_post
    forum_latest_post = property(_get_forum_latest_post)

    def _recurse_for_parents_slug(self, forum_obj):
        #This is used for the urls
        p_list = []
        if forum_obj.parent_id:
            p = forum_obj.parent
            p_list.append(p.slug)
            more = self._recurse_for_parents_slug(p)
            p_list.extend(more)
        if forum_obj == self and p_list:
            p_list.reverse()
        return p_list

    def get_absolute_url(self):
        p_list = self._recurse_for_parents_slug(self)
        p_list.append(self.slug)
        return '%s%s/' % (reverse('forum_list'), '/'.join (p_list))

    def _recurse_for_parents_name(self, forum_obj):
        #This is used for the visual display & save validation
        p_list = []
        if forum_obj.parent_id:
            p = forum_obj.parent
            p_list.append(p.title)
            more = self._recurse_for_parents_name(p)
            p_list.extend(more)
        if forum_obj == self and p_list:
            p_list.reverse()
        return p_list

    def get_separator(self):
        return ' &raquo; '

    def _parents_repr(self):
        p_list = self._recurse_for_parents_name(self)
        return self.get_separator().join(p_list)
    _parents_repr.short_description = _("Forum parents")

    def _recurse_for_parents_name_url(self, forum__obj):
        #Get all the absolute urls and names (for use in site navigation)
        p_list = []
        url_list = []
        if forum__obj.parent_id:
            p = forum__obj.parent
            p_list.append(p.title)
            url_list.append(p.get_absolute_url())
            more, url = self._recurse_for_parents_name_url(p)
            p_list.extend(more)
            url_list.extend(url)
        if forum__obj == self and p_list:
            p_list.reverse()
            url_list.reverse()
        return p_list, url_list

    def get_url_name(self):
        #Get a list of the url to display and the actual urls
        p_list, url_list = self._recurse_for_parents_name_url(self)
        p_list.append(self.title)
        url_list.append(self.get_absolute_url())
        return zip(p_list, url_list)

    def __unicode__(self):
        return u'%s' % self.title
    
    class Meta:
        ordering = ['ordering', 'title',]
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')

    def save(self, force_insert=False, force_update=False):
        self.site = self.site or Site.objects.get_current()
        p_list = self._recurse_for_parents_name(self)
        if (self.title) in p_list:
            raise validators.ValidationError(_("You must not save a forum in itself!"))
        super(Forum, self).save(force_insert, force_update)

    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]): return [L]
        if L == []: return L
        return self._flatten(L[0]) + self._flatten(L[1:])

    def _recurse_for_children(self, node):
        children = []
        children.append(node)
        for child in node.child.all():
            children_list = self._recurse_for_children(child)
            children.append(children_list)
        return children

    def get_all_children(self):
        """
        Gets a list of all of the children forums.
        """
        children_list = self._recurse_for_children(self)
        flat_list = self._flatten(children_list[1:])
        return flat_list

class Thread(models.Model):
    """
    A Thread belongs in a Forum, and is a collection of posts.

    Threads can be closed or stickied which alter their behaviour 
    in the thread listings. Again, the posts & views fields are 
    automatically updated with saving a post or viewing the thread.
    """
    forum = models.ForeignKey(Forum)
    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=105)
    sticky = models.BooleanField(_("Sticky?"), blank=True, default=False)
    closed = models.BooleanField(_("Closed?"), blank=True, default=False)
    posts = models.IntegerField(_("Posts"), default=0)
    views = models.IntegerField(_("Views"), default=0)
    comment = models.ForeignKey('comments_app.TappedComment',null=True,blank=True,related_name="commentthread_set") # Two way link
    latest_post = models.ForeignKey('comments_app.TappedComment',editable=False,null=True,blank=True)
    site = models.ForeignKey('sites.Site')

    objects = models.Manager()
    nonrel_objects = EnuffManager()

    class Meta:
        ordering = ('-id',)
        verbose_name = _('Thread')
        verbose_name_plural = _('Threads')

    def save(self, *args,**kwargs):
        from slugify import SlugifyUniquely
        if not self.slug:
            self.slug = SlugifyUniquely(self.title, Thread)
        f = self.forum
        f.threads = f.thread_set.count()
        f.save()
        self.site = Site.objects.get_current()
        if not self.sticky:
            self.sticky = False
        super(Thread, self).save(*args,**kwargs)

    def delete(self):
        super(Thread, self).delete()
        f = self.forum
        f.threads = f.thread_set.count()
        Post = comments.get_model()
        ct = ContentType.objects.get_for_model(Forum)
        f.posts = Post.objects.filter(content_type=ct,object_pk=f.id).count()
        f.save()
    
    def get_absolute_url(self):
        return reverse('forum_view_thread', args=[self.forum.slug,self.slug])
    
    def __unicode__(self):
        return u'%s'% self.title.replace('[[','').replace(']]','')
