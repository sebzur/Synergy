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
    def __init__(self, menu, args, kwargs, asvar):
        self.menu = template.Variable(menu)
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        menu_obj = self.menu.resolve(context)
        #menu_name = self.menu_name#.resolve(context)

        if self.asvar:
            context[self.asvar] = menu_obj
            return ''
        else:
            tpl = 'menu/menu.html'
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
    if len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' takes two arguments"
                                  " (user, component)" % bits[0])
    return SecondaryMenuNode(bits[1], bits[2])

class SecondaryMenuNode(template.Node):
    def __init__(self, user, component):
        self.user = template.Variable(user)
        self.component = template.Variable(component)

    def render(self, context):
        component = self.component.resolve(context)
        #ids = []
	#db = 'default'
        menus = get_model('menu', 'Menu').objects.none()
        if component:
            ids = component.menus.all().values_list('menu', flat=True)
	    #db = ids.db
            menus = get_model('menu', 'Menu').objects.using(ids.db).filter(id__in=ids)

        user = self.user.resolve(context)
        excluded = []
        for menu in menus:
            for perm_name in menu.permissions.values_list('perm', flat=True):
                if not user.has_perm(perm_name):
                    excluded.append(menu.id)
        menus = menus.exclude(id__in=excluded)
        
        tpl = 'menu/secondary_menu.html'
        context = {'menus': menus, 'user': self.user}
        return render_to_string(tpl, context)
