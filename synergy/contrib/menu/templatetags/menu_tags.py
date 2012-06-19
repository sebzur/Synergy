from django import template
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_model
import re
from django.utils.encoding import smart_str, smart_unicode

from django.utils.datastructures import SortedDict

from synergy.contrib.prospects.models import resolve_lookup

register = template.Library()
kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")


@register.tag
def menu(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (menu name)" % bits[0])
    menu_name = bits[1]
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    # process them as template vars
    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to menu tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))


    return MenuNode(menu_name, args, kwargs, asvar)

class MenuNode(template.Node):
    def __init__(self, menu_name, args, kwargs, asvar):
        self.menu_name = template.Variable(menu_name)
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        menu_name = self.menu_name.resolve(context)
        #menu_name = self.menu_name#.resolve(context)

        if self.asvar:
            context[self.asvar] = menu_name
            return ''
        else:
            tpl = 'menu/menu.html'
            menu_obj = get_model('menu', 'Menu').objects.get(name=menu_name)
            context = {'menu': menu_obj, 'items': SortedDict()}

            for item in menu_obj.items.filter(is_enabled=True):
                #if not all(trigger.callable(kwargs.get(trigger.argument_provided.name)) for trigger in item.triggers.all()):
                #if not all((resolve_lookup(kwargs.get(trigger.argument.name), trigger.trigger_lookup) for trigger in item.triggers.all())):
                if not item.is_triggered(**kwargs):
                    continue
                context['items'][item] = item.get_url(*args, **kwargs)
            return render_to_string(tpl, context)


@register.tag
def secondary_menu(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (user)" % bits[0])
    user = parser.compile_filter(bits[1])
    return SecondaryMenuNode(user)

class SecondaryMenuNode(template.Node):
    def __init__(self, user):
        self.user = user

    def render(self, context):
        menus = get_model('menu', 'Menu').objects.filter(category='s', is_enabled=True)
        tpl = 'menu/secondary_menu.html'
        context = {'menus': menus, 'user': self.user}
        return render_to_string(tpl, context)
