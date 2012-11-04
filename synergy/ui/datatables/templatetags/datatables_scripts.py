from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.tag('simple_table')
def default_table(parser, token):
    contents = token.split_contents()
    print contents
    if len(contents) > 6:
        raise template.TemplateSyntaxError("%r tag requires at maximum six arguments" % contents[0])
    if len(contents) < 2:        
        raise template.TemplateSyntaxError("%r tag requires at least selector defined" % contents[0])
    tag_name, selector = contents[:2]
    return LoadPluginNode(selector, *contents[2:])


class LoadPluginNode(template.Node):
    # order matters!
    DEFAULT_OPTIONS = (('lang', 'en'), ('is_filtered', True), ('is_paginated', True), ('page_rows', 100))

    def __init__(self, selector, *args):
        self.options = {}
        self.defaults = {'selector': selector.strip("'")}

        i = 0 # in case no args provided
        for i, arg in enumerate(args):
            handler = self.DEFAULT_OPTIONS[i]
            self.options[handler[0]] = template.Variable(arg)
        
        for arg in self.DEFAULT_OPTIONS[i:]:
            self.defaults[arg[0]] = arg[1]

    def render(self, context):
        try:
            # resolving values
            for option, value in self.options.iteritems():
                self.options[option] = value.resolve(context)

            # processing translation file info
            print self.options.get('lang'), self.defaults.get('lang')
            print self.defaults
            lang = self.options.get('lang') or self.defaults.get('lang')
            transfiles = {'pl': "/static/datatables/language/pl_PL.txt",
                          'en': None}
            self.options['transfile'] = transfiles[lang]
            
            # updating with defaults
            self.options.update(self.defaults)
            return render_to_string('datatables/init_default.js', self.options)
        except template.VariableDoesNotExist, error:
            return ''

