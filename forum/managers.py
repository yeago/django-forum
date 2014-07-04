from django.db import models
from django.db.models import Q


class ForumManager(models.Manager):
    def for_user(self, user):
        if user.is_staff:
            return self.all()
        return self.filter(only_staff_reads=False)

    def for_groups(self, groups):
        return self.all()
        if groups:
            public = Q(groups__isnull=True)
            user_groups = Q(groups__in=groups)
            return self.filter(public|user_groups).distinct()
        return self.filter(groups__isnull=True)
    
    def has_access(self, forum, user):
        return True
        return forum in self.for_user(user)

