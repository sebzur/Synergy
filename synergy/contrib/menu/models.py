from django.db import models
from synergy.contrib.prospects.models import fields, resolve_lookup


class Menu(models.Model):
    CATEGORY = (('p', 'Primary Menu'), ('s', 'Secondary Menu'), ('c', 'Context Menu'))

    name = models.SlugField(unique=True)
    verbose_name = models.CharField(max_length=255)
    weight = models.IntegerField()

    category = models.CharField(max_length=1, choices=CATEGORY)

    is_enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.verbose_name, self.name)

    class Meta:
        unique_together = (('name', 'verbose_name'),)
        ordering = ('weight', 'name')


class AccessPermission(models.Model):
    menu = models.ForeignKey('Menu', related_name="permissions")
    perm = models.CharField(max_length=100)
    

# To wydaje sie byc niespecjalnie potrzebne
# bo teoretycznie mozna wygenerowac liste wszystkich
# argumentw przegladajc itemsy, ale chcemy to znac z gory,
# mozemy do tego podawac defaultsy, etc
class MenuArgument(models.Model):
    menu = models.ForeignKey('Menu', related_name="arguments")
    name = models.CharField(max_length=255)
    default_value = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField()

    def __unicode__(self):
        return u"%s : %s" % (self.menu, self.name)

    class Meta:
        unique_together = (('menu', 'weight'),)
        ordering = ('weight',)

class MenuItemTrigger(models.Model):
    argument = models.ForeignKey('MenuArgument', related_name='triggers')
    trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the argument that triggers the item to be visible")
    negate_trigger = models.BooleanField()

    item = models.ForeignKey('MenuItem', related_name='triggers')
    weight = models.IntegerField()

    class Meta:
        ordering = ('weight', )

class MenuItem(models.Model):
    menu = models.ForeignKey('Menu', related_name='items')
    name = models.SlugField(unique=True)
    verbose_name = models.CharField(max_length=255)

    weight = models.IntegerField()

    url = models.CharField(max_length=200)
    # if resolve_url is set, Django will try to
    # resolve the value to get the full URL
    reverse_url = models.BooleanField()
    css_class = models.CharField(max_length=255, blank=True)
    prefix_text = models.CharField(max_length=255, blank=True)
    suffix_text = models.CharField(max_length=255, blank=True)
    target = models.CharField(choices=(('_blank', '_blank'), ('_parent', '_parent')), max_length=32, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)

    is_enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s : %s" % (self.menu, self.verbose_name)

    def is_triggered(self, **kwargs):
        triggers = self.triggers.all()
        if triggers.exists():
            return all((trigger.negate_trigger ^ bool(resolve_lookup(kwargs.get(trigger.argument.name), trigger.trigger_lookup)) for trigger in triggers))
        return True

    def get_url(self, *args, **kwargs):
        from django.template import Context, Template
        if self.reverse_url:
            bits = self.url.split()
            if bits[0] in ('create', 'list'):
                t = Template("{%% load records_tags %%} {%% %s %s %%}" % (bits[0], " ".join(bits[1:])))
            else:
                t = Template("{%% url %s %%}" % self.url)

            context = kwargs.copy()
            arguments = self.menu.arguments.all().order_by('weight')
            for i, arg in enumerate(args):
                key = arguments[i].name
                context[key] = arg

            for arg in arguments.exclude(name__in=context.keys()):
                context[arg.name] = arg.default_value
                
            return t.render(Context(context))
        return self.url

    class Meta:
        unique_together = (('menu', 'name'),)
        ordering = ('weight',)
