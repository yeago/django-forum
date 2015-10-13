from django.template import Library, Node, TemplateSyntaxError, Variable
from forum.models import Thread
import django_comments

register = Library()
Post = django_comments.get_model()


def forum_latest_thread_activity(parser, token):
    """
    {% forum_latest_thread_activity [number] as [context_var] %}
    """
    bits = token.contents.split()
    if len(bits) not in (1, 2, 4):
        raise TemplateSyntaxError('%s tag requires none, one or three arguments' % bits[0])
    if bits[2] != 'as':
        raise TemplateSyntaxError("Second argument to %s tag must be 'as'" % bits[0])
    if not bits[1]:
        bits[1] = 5 # Default number of items
    if not bits[3]:
        bits[3] = 'latest_thread_activity'
    return ForumLatestThreadsNode(bits[1], bits[3])

class ForumLatestThreadsNode(Node):
    def __init__(self, number, context_var):
        self.number = int(number) - 1
        self.context_var = context_var
    
    def render(self, context):
        context[self.context_var] = Thread.objects.select_related().order_by('-latest_post_time')[:self.number]
        return ''

def forum_latest_posts(parser, token):
    """
    {% forum_latest_posts [number] as [context_var] %}
    """
    bits = token.contents.split()
    if len(bits) not in (1, 2, 4):
        raise TemplateSyntaxError('%s tag requires none, one or three arguments' % bits[0])
    if bits[2] != 'as':
        raise TemplateSyntaxError("Second argument to %s tag must be 'as'" % bits[0])
    if not bits[1]:
        bits[1] = 5 # Default number of items
    if not bits[3]:
        bits[3] = 'latest_posts'
    return ForumLatestPostsNode(bits[1], bits[3])

class ForumLatestPostsNode(Node):
    def __init__(self, number, context_var):
        self.number = int(number) - 1
        self.context_var = context_var
    
    def render(self, context):
        context[self.context_var] = Post.objects.select_related().order_by('-time')[:self.number]
        return ''


def forum_latest_user_posts(parser, token):
    """
    {% forum_latest_user_posts user [number] as [context_var] %}
    """
    bits = token.contents.split()
    if len(bits) not in (2, 3, 5):
        raise TemplateSyntaxError('%s tag requires one, two or four arguments' % bits[0])
    if bits[3] != 'as':
        raise TemplateSyntaxError("Second argument to %s tag must be 'as'" % bits[0])
    if not bits[2]:
        bits[2] = 5 # Default number of items
    if not bits[3]:
        bits[4] = 'latest_user_posts'
    return ForumLatestUserPostsNode(bits[1], bits[2], bits[4])

class ForumLatestUserPostsNode(Node):
    def __init__(self, user, number, context_var):
        self.user = Variable(user)
        self.number = int(number) - 1
        self.context_var = context_var
    
    def render(self, context):
        user = self.user.resolve(context)
        context[self.context_var] = Post.objects.select_related().filter(author=user).order_by('-time')[:self.number]
        return ''


@register.filter(name='can_post_in')
def can_post_in(user, forum):
    if forum.only_staff_posts:
        return user.is_authenticated and user.is_staff
    return user.is_authenticated


@register.filter(name='can_read_in')
def can_read_in(user, forum):
    if forum.only_staff_reads:
        return user.is_authenticated and user.is_staff
    return True

register.tag('forum_latest_posts', forum_latest_posts)
register.tag('forum_latest_thread_activity', forum_latest_thread_activity)
register.tag('forum_latest_user_posts', forum_latest_user_posts)
