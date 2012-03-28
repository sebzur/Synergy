from django import template
from django.template.loader import render_to_string
from django.conf import settings

register = template.Library()

@register.filter(name='teaser')
def teaser(obj):
    app_label = obj._meta.app_label
    model = obj._meta.object_name.lower()
    tpl = '%s/teasers/%s.html' % (obj._meta.app_label, obj._meta.object_name.lower())
    try:
        if settings.DEBUG:
            print tpl
        return render_to_string(tpl, {model: obj})
    except template.TemplateDoesNotExist:
        tpl = 'synergy/contrib/prospects/teaser.html'
        return render_to_string(tpl, {'object': obj})

