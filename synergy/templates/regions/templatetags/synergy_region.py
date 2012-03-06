from django import template
from django.template.loader import render_to_string
from django.conf import settings

register = template.Library()

@register.tag
def region(parser, token):
     try:
         # split_contents() knows not to split quoted strings.
         tag_name, region_name = token.split_contents()
     except ValueError:
         raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

     nodelist = parser.parse(('endregion',))
     parser.delete_first_token()
     return RegionNode(region_name, nodelist)

class RegionNode(template.Node):

    def __init__(self, region_name, nodelist):
        self.nodelist = nodelist
        self.region_name = region_name

    def render(self, context):
         region_postfixes = context.get('region_postfixes', {})
         if region_postfixes.has_key(self.region_name):
              postfix = region_postfixes[self.region_name]
         else:
              postfix = ''

         if context.get('region_info'):
              for tpl in context.get('region_info').get_template_names(self.region_name, postfix):
                   try:
                        if settings.DEBUG:
                             print tpl
                        return render_to_string(tpl, context)
                   except template.TemplateDoesNotExist:
                        continue
         if postfix:
              raise template.TemplateDoesNotExist('You should provided template with "%s" postfix' % postfix)
         return self.nodelist.render(context)

