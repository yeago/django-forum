import datetime
from django import forms
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from forum.models import Thread


class CreateThreadForm(forms.Form):
    title = forms.CharField(label=_("Title"), max_length=100,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))
    sticky = forms.BooleanField(label=_("Sticky"), required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.is_edit = kwargs.pop('is_edit', False)

        super(CreateThreadForm, self).__init__(*args, **kwargs)

    def clean(self):
        try:
            latest = Thread.objects.filter(comment__user=self.user).latest('comment__submit_date')
            if latest.comment.submit_date < datetime.datetime.now() - datetime.timedelta(minutes=5):
                raise forms.ValidationError("You may not create threads on this site that often.")
        except Thread.DoesNotExist:
            pass

        data = self.cleaned_data
        if not self.is_edit and 'title' in data:
            duplicates = Thread.objects.filter(comment__user=self.user,
                                               title=data['title'])

            # avoid the same Thread created multiple times
            if duplicates.count():
                raise forms.ValidationError(mark_safe('%s <a href="%s">%s</a>' % (
                    _("Possible duplicate submission. Your post may already be posted. Please see "),
                    duplicates[0].get_absolute_url(),
                    duplicates[0].title)))

        return data


class ReplyForm(forms.Form):
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))
