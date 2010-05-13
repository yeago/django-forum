from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from forum.models import Forum, Thread

class ForumAdmin(admin.ModelAdmin):
    list_display = ('title', '_parents_repr')
    ordering = ['ordering', 'parent', 'title']
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
		    models.ManyToManyField: {'widget': FilteredSelectMultiple("allowed users",is_stacked=False) },
    }

class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'latest_post')
    list_filter = ('forum',)

admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
