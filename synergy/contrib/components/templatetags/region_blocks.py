from django import template
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_model

from django.utils.datastructures import SortedDict
register = template.Library()

@register.tag(name='region-blocks')
def region_blocks(parser, token):
    try:
        # Splitting by None == splitting by spaces.
        tag_name, region, user = token.contents.split(None, 2)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    return RegionBlocksNode(region, user)

class RegionBlocksNode(template.Node):
    def __init__(self, region, user):
        self.region = region
        self.user = template.Variable(user)

    def render(self, context):
        user = self.user.resolve(context)
        blocks = context['blocks'][self.region]
        tpl = 'components/region/blocks.html'
        return render_to_string(tpl, {'blocks': blocks})


