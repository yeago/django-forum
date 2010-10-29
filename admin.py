from django.contrib import admin
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from forum.models import Forum, Thread

def convert_thread(modeladmin,request,qs):
	from django.contrib.contenttypes.models import ContentType
	comment_model = comments.get_model()
	from stack.models import Question
	old_ct = ContentType.objects.get_for_model(Thread)

	from django.contrib import comments

	comment_model = comments.get_model()

	for thread in qs:
		first_comment = comment_model.objects.filter(content_type=old_ct,object_pk=thread.pk).order_by('submit_date')[0]

		question = Question.objects.create(title=thread.title,comment=first_comment)
		ct = ContentType.objects.get_for_model(question)
		comment_model.objects.filter(content_type=old_ct,object_pk=thread.pk).update(content_type=ct,object_pk=question.pk)

		from former_url.models import FormerURL
		FormerURL.objects.create(current=question.get_absolute_url(),former=thread.get_absolute_url())

		thread.delete()

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
    raw_id_fields = ('comment',)
    list_filter = ('forum',)

admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
