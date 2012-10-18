import django.dispatch

thread_created = django.dispatch.Signal(providing_args=["instance", "author"])
