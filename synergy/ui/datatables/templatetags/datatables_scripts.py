from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.tag('simple_table')
def default_table(parser, token):
    contents = token.split_contents()
    if len(contents) > 6:
        raise template.TemplateSyntaxError("%r tag requires at maximum six arguments" % contents[0])
    extract_map = [not (var[0] == var[-1] and var[0] in ('"', "'")) for var in contents[1:]]
    return LoadPluginNode(extract_map, *contents[1:])


class LoadPluginNode(template.Node):
    # order matters!
    DEFAULT_OPTIONS = (('selector', '.datatable'), ('lang', 'en'), ('is_filtered', True), ('is_paginated', True), ('page_rows', 100))

    def __init__(self, extract_map, *args):
        self.extract_map = extract_map
        self.args = args

    def map_args(self, extract_map, *args):
        options = {}
        defaults = {}

        i = 0 # in case no args provided
        for i, arg in enumerate(args):
            handler = self.DEFAULT_OPTIONS[i]
            options[handler[0]] = template.Variable(arg) if extract_map[i] else arg.strip("'").strip('"')
        
        for arg in self.DEFAULT_OPTIONS[i+1:]:
            defaults[arg[0]] = arg[1]

        return options, defaults

    def render(self, context):
        try:
            # resolving values
            options, defaults = self.map_args(self.extract_map, *self.args)

            for option, value in options.iteritems():
                if hasattr(value, 'resolve'):
                    options[option] = value.resolve(context)
                else:
                    options[option] = value

            # processing translation file info
            lang = options.get('lang') or defaults.get('lang')
            transfiles = {'pl': "/static/datatables/language/pl_PL.txt",
                          'en': None}
            options['transfile'] = transfiles[lang]
            
            # updating with defaults
            options.update(defaults)

            return render_to_string('datatables/init_default.js', options)
        except template.VariableDoesNotExist, error:
            return ''

