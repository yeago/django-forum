from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from forum.models import Forum, Thread, Category


class ForumAdmin(admin.ModelAdmin):
    list_display = ('title', '_parents_repr')
    ordering = ['ordering', 'parent', 'title']
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ['allowed_users']
    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("allowed users",is_stacked=False) },
    }
    #raw_id_fields = ['allowed_users']


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'latest_post','comment')
    raw_id_fields = ('user',)
    list_filter = ('forum',)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category

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
