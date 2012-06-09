from django.db import models


class Menu(models.Model):
    name = models.SlugField(unique=True)
    verbose_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.verbose_name

    class Meta:
        unique_together = (('name', 'verbose_name'),)


# To wydaje sie byc niespecjalnie potrzebne
# bo teoretycznie mozna wygenerowac liste wszystkich
# argumentw przegladajc itemsy, ale chcemy to znac z gory,
# mozemy do tego podawac defaultsy, etc
class MenuArgument(models.Model):
    menu = models.ForeignKey('Menu', related_name="arguments")
    name = models.CharField(max_length=255)
    default_value = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField()

    class Meta:
        unique_together = (('menu', 'weight'),)
        ordering = ('weight',)

    
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


    def get_url(self, *args, **kwargs):
        from django.template import Context, Template
        if self.reverse_url:

            bits = self.url.split()
            if bits[0] == 'create':
                t = Template("{%% load records_tags %%} {%% create %s %%}" % " ".join(bits[1:]))
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
