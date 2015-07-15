import django.dispatch

thread_created = django.dispatch.Signal(providing_args=["instance", "author"])
thread_moved = django.dispatch.Signal(providing_args=["instance", "user"])
