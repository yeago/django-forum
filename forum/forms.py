from django import forms
from django.utils.translation import ugettext as _


class CreateThreadForm(forms.Form):
    title = forms.CharField(label=_("Title"), max_length=100,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))


class ReplyForm(forms.Form):
    body = forms.CharField(label=_("Body"),
                           widget=forms.Textarea(attrs={'rows': 8, 'cols': 50, 'class': 'form-control'}))
