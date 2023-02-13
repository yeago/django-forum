import datetime
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe

from forum.models import Thread

try:
    from django.contrib import comments
except ImportError:
    import django_comments as comments


class ThreadForm(forms.ModelForm):
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))
    banned_users = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.forum = kwargs.pop('forum', None)

        super(ThreadForm, self).__init__(*args, **kwargs)

        if not self.user.is_staff and not self.user.is_superuser:
            del self.fields['sticky']

        if self.instance and self.instance.pk:
            banned_users_string = ", ".join((i.username for i in self.instance.banned_users.all()))
            self.initial.update({'body': self.instance.comment.comment,
                                 'banned_users': banned_users_string})

    def clean(self):
        if not self.instance or not self.instance.pk:
            try:
                latest = Thread.objects.filter(comment__user=self.user).latest('comment__submit_date')
                if latest.comment.submit_date > datetime.datetime.now() - datetime.timedelta(minutes=5):
                    raise forms.ValidationError("You may not create threads on this site that often.")
            except Thread.DoesNotExist:
                pass
        return self.cleaned_data

    def clean_title(self):
        if not self.instance or not self.instance.pk:
            duplicates = Thread.objects.filter(comment__user=self.user,
                                               title=self.cleaned_data['title'])

            # avoid the same Thread created multiple times
            if duplicates.count():
                raise forms.ValidationError(mark_safe('%s <a href="%s">%s</a>' % (
                    _("Possible duplicate submission. Your post may already be posted. Please see "),
                    duplicates[0].get_absolute_url(),
                    duplicates[0].title)))

        return self.cleaned_data['title']

    def clean_banned_users(self):
        for item in (self.cleaned_data.get("banned_users") or "").split(","):
            if not item.strip():
                continue
            try:
                User.objects.get(username=item.strip())
            except User.DoesNotExist:
                raise forms.ValidationError("User not found: %s" % item)
        return self.cleaned_data.get("banned_users")

    def save(self, *args, **kwargs):
        instance = super(ThreadForm, self).save(commit=False)
        instance.forum = self.forum
        if not instance.comment:
            instance.save()
            Post = comments.get_model()
            ct = ContentType.objects.get_for_model(Thread)
            instance.comment = Post.objects.create(
                content_type=ct,
                object_pk=instance.pk,
                user=self.user,
                submit_date=datetime.datetime.now(),
                site=Site.objects.get_current(),
                comment=self.cleaned_data['body'],
            )
            instance.latest_post = instance.comment

        instance.comment.comment = self.cleaned_data['body']
        instance.comment.save()
        instance.save()

        instance.banned_users.clear()
        for item in self.cleaned_data.get("banned_users", "").split(","):
            if item.strip():
                instance.banned_users.add(User.objects.get(username=item.strip()))
        return instance

    class Meta:
        fields = ['title', 'sticky']
        model = Thread


class ReplyForm(forms.Form):
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))
