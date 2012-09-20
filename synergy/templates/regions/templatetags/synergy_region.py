from django import template
from django.template.loader import render_to_string
from django.conf import settings

register = template.Library()

FIRST = 'first'
STACKED = 'stacked'

@register.tag
def region(parser, token):
     try:
         # split_contents() knows not to split quoted strings.
         tag_name, region_name, mode = token.contents.split(None, 3)
     except ValueError:
         tag_name, region_name = token.contents.split(None, 2)
         mode = FIRST
     except ValueError:
         raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

     if not mode in (FIRST, STACKED):
        raise template.TemplateSyntaxError("%r tag's `mode` argument should be `%s` or `%s`." % (tag_name, FIRST, STACKED))

     nodelist = parser.parse(('endregion',))
     parser.delete_first_token()
     return RegionNode(region_name, nodelist, mode)

class RegionNode(template.Node):

    def __init__(self, region_name, nodelist, mode):
        self.nodelist = nodelist
        self.region_name = region_name
        self.mode = mode

    def render(self, context):
       
         region_postfixes = context.get('region_postfixes', {})
         if region_postfixes.has_key(self.region_name):
              postfix = region_postfixes[self.region_name]
         else:
              postfix = ''
    


         if context.get('region_info'):
              contents = []
              for tpl in context.get('region_info').get_template_names(self.region_name, postfix):
                   try:
                        content = render_to_string(tpl, context)
                        if settings.DEBUG:
                             print tpl, '*' if content else ''
                        if self.mode == FIRST:
                             return content
                        contents.append(render_to_string(tpl, context))
                   except template.TemplateDoesNotExist:
                        continue

         merged_content =  ''.join(contents)
         if merged_content:
              return merged_content

         if postfix:
              raise template.TemplateDoesNotExist('You should provided template with "%s" postfix' % postfix)

         return self.nodelist.render(context)

