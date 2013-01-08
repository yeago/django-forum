from django.db import models
from django.db.models import Q

class ForumManager(models.Manager):
    def for_user(self, u):
        return self.all()
        if u and u.is_authenticated():
            public = Q(allowed_users__isnull=True)
            user = Q(allowed_users=u)
            return self.filter(public|user).distinct()
        return self.filter(allowed_users__isnull=True)

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
