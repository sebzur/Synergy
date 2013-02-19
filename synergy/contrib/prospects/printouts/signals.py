import django.dispatch

pdf_done = django.dispatch.Signal(providing_args=['instance','pdf_content', 'uuid'])
