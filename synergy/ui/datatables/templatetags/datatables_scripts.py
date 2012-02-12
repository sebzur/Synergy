from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.tag('simple_table')
def default_table(parser, token):
    try:
        tag_name, selector = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return LoadPluginNode(selector)


class LoadPluginNode(template.Node):
    def __init__(self, selector):
        self.selector = selector.strip("'")

    def render(self, context):
        try:
            return render_to_string('datatables/init_default.js', {'selector': self.selector})
        except template.VariableDoesNotExist:
            return ''

