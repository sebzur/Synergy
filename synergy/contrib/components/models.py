from django.db import models

class Component(models.Model):
    name = models.SlugField(unique=True, verbose_name="Component machine name", help_text="This is slug field")
    verbose_name = models.CharField(max_length=255, verbose_name="Component verbose name")

    class Meta:
        ordering = ('name', 'verbose_name')
        verbose_name = "Component"
        verbose_name_plural = "Components"

class ComponentProspectVariant(models.Model):
    module = models.ForeignKey('Submodule', related_name='prospect_variants')
    prospect_variant = models.OneToOneField('prospects.ProspectVariant')

    class Meta:
        verbose_name = "Component Prospect Variant"
        verbose_name_plural = "Component Prospect Variants"

class ComponentRecord(models.Model):
    module = models.ForeignKey('Submodule', related_name='records')
    records = models.OneToOneField('records.RecrodSetup')

    class Meta:
        verbose_name = "Component Record"
        verbose_name_plural = "Component Records"

class ComponentMenu(models.Model):
    component = models.ForeignKey('Component', related_name='menus')
    menu = models.OneToOneField('menu.Menu', limit_choices_to={'category': 's'})

    class Meta:
        verbose_name = "Component Menu"
        verbose_name_plural = "Component Menus"
