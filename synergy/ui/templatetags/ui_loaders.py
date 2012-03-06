from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.tag
def load_plugin(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, plugin_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return LoadPluginNode(plugin_name)


class LoadPluginNode(template.Node):
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name

    def render(self, context):
        try:
            print 'Loading', self.plugin_name
            return render_to_string('%s/load_plugin.html' % self.plugin_name, {})
        except template.VariableDoesNotExist:
            return ''
        except Exception, error:
            print error

