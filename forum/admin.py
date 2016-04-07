from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from forum.models import Forum, Thread, Category
from forum.signals import thread_moved
from subscription.models import Subscription


class ForumAdmin(admin.ModelAdmin):
    list_display = ('title', '_parents_repr')
    ordering = ['ordering', 'parent', 'title']
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ['allowed_users']
    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("allowed users",is_stacked=False) },
    }

    def save_model(self, request, obj, form, change):
        if 'allowed_users' in form.changed_data:
            if obj.restricted or form.cleaned_data.get('restricted'):
                for user in form.cleaned_data['allowed_users']:
                    Subscription.objects.subscribe(user, obj)
        super(ForumAdmin, self).save_model(request, obj, form, change)


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'latest_post','comment')
    raw_id_fields = ('comment',)
    list_filter = ('forum',)

    def save_model(self, request, obj, form, change):
        if 'forum' in form.changed_data:
            thread_moved.send(sender=Thread, instance=obj, user=request.user)
        super(ThreadAdmin, self).save_model(request, obj, form, change)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    forums = forms.ModelMultipleChoiceField(queryset=Forum.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['forums'].initial = self.instance.forum_set.all()

    def save(self, *args, **kwargs):
        instance = super(CategoryForm, self).save(commit=False)
        instance.save()
        self.fields['forums'].initial.update(category=None)
        self.cleaned_data['forums'].update(category=instance)
        return instance


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm


admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
