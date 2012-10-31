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

         # troche ugly-hack
         # potrzebujemy [''] przy klejeniu defaultowych
         postfixes = [] if self.mode == FIRST else ['']

         if region_postfixes.has_key(self.region_name):
              for pstfx in region_postfixes[self.region_name]:
                   if not pstfx in postfixes:
                        postfixes.append(pstfx)
         else:
              postfixes = ['']

         contents = []
         if context.get('region_info'):
              for postfix in postfixes:
                   for tpl in context.get('region_info').get_template_names(self.region_name, postfix):

                        if settings.DEBUG:
                             # just for debug: print out the template name we're looking for
                             print tpl

                        try:
                             content = render_to_string(tpl, context)
                        except template.TemplateDoesNotExist:
                             continue


                        # only first template is used, so if we're in FIRST
                        # mode we return the content here
                        if self.mode == FIRST:
                             return content
                        #otherwise we append the content to the list and break the postifxes loop
                        contents.append(content)
                        break

         
         # If we're in STACKED mode the contents elements are merged and the result is returned
         merged_content = ''.join(contents)
         if merged_content:
              return merged_content

         # if we're still here and there's something beside [''] in postfixes, this is an error
         if len(postfixes) > 1:
              raise template.TemplateDoesNotExist('You should provided templates with `%s` postfixes' % ",".join(postfixes))

         # otherwise, theres no custom template provided and it is not required, so simply return the original {% region %} content
         return self.nodelist.render(context)

