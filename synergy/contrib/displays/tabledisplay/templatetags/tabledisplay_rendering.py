from django import template
from django.template.loader import render_to_string

register = template.Library()

class TableRowNode(template.Node):
    def __init__(self, obj, table, columns, kwargs):
        self.obj = template.Variable(obj)
        self.table = template.Variable(table)
        self.kwargs = template.Variable(kwargs)
        self.columns = template.Variable(columns)

    def render(self, context):
        obj = self.obj.resolve(context)
        table = self.table.resolve(context)
        kwargs = self.kwargs.resolve(context)
        columns = self.columns.resolve(context)
        c = []
        tpl = 'tabledisplay/td.html'
        for column in columns:
            link = column.is_url(obj)
            value = column.get_value(obj, **kwargs)
            c.append(render_to_string(tpl, {'object': obj, 'value': value, 'column': column, 'link': link}))
        tpl = 'tabledisplay/tr.html'
        return render_to_string(tpl, {'obj': obj, 'table': table, 'columns': c})

@register.tag('table_row')
def table_row(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, obj, table, columns, kwargs = token.contents.split(None, 4)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    return TableRowNode(obj, table, columns,  kwargs)

@register.filter
def css_styles(column, value):
    styles = column.get_styles(value)
    return ' '.join('%s=%s' % (style, styles.get(style)) for style in styles if styles.get(style))
