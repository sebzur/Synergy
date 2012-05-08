import django.dispatch

prospect_form_created = django.dispatch.Signal(providing_args=["form", "request"])

prospect_results_created = django.dispatch.Signal(providing_args=["results", "request"])
