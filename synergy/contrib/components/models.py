from django.db import models

class Component(models.Model):
    name = models.SlugField(unique=True, verbose_name="Component machine name", help_text="This is slug field")
    verbose_name = models.CharField(max_length=255, verbose_name="Component verbose name", unique=True)

    site = models.ForeignKey('sites.Site', null=True, blank=True, related_name="components")

    flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="components")

    record_flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Records access flag", related_name="components_by_record")
    prospect_flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Prospects access flag", related_name="components_by_prospect")

    list_flag =  models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="List access flag", related_name="components_by_list")
    detail_flag =  models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Detail access flag", related_name="components_by_detail")
    create_flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Create access flag", related_name="components_by_create")
    update_flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Update access flag", related_name="components_by_update")
    delete_flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Delete access flag", related_name="components_by_delete")

    def __unicode__(self):
        return self.verbose_name

    class Meta:
        ordering = ('name', 'verbose_name')
        verbose_name = "Component"
        verbose_name_plural = "Components"

class ComponentProspectVariant(models.Model):
    component = models.ForeignKey('Component', related_name='prospect_variants')
    prospect_variant = models.OneToOneField('prospects.ProspectVariant', related_name="component_assignment")

    flag = models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="General access flag", related_name="component_variants")
    list_flag =  models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Detail access flag", related_name="list_access_component_variants")
    detail_flag =  models.ForeignKey('flags.Flag', null=True, blank=True, verbose_name="Detail access flag", related_name="detail_access_component_variants")

    class Meta:
        unique_together = (('component', 'prospect_variant'),)
        verbose_name = "Component Prospect Variant"
        verbose_name_plural = "Component Prospect Variants"

class ComponentRecord(models.Model):
    component = models.ForeignKey('Component', related_name='records')
    records = models.OneToOneField('records.RecordSetup', related_name="component_assignment")

    flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="component_records")
    create_flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="create_accsss_component_records")
    update_flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="update_accsss_component_records")
    delete_flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="delete_accsss_component_records")

    class Meta:
        unique_together = (('component', 'records'),)
        verbose_name = "Component Record"
        verbose_name_plural = "Component Records"


class ComponentMenu(models.Model):
    """ Component Menu -- the set of menu objects related the component displayed.
    If the user has component access the menu access is also granted.  For granural
    flag-bassed menu please referer to the BlockMenu class.

    """

    component = models.ForeignKey('Component', related_name='menus')
    menu = models.OneToOneField('menu.Menu', limit_choices_to={'category': 's'}, related_name="component_assignment")

    class Meta:
        verbose_name = "Component Menu"
        verbose_name_plural = "Component Menus"

# ------------------------------------------
# Regions
# ------------------------------------------

class Region(models.Model):
    verbose_name = models.CharField(max_length=100, verbose_name="Region verbose name")
    name = models.SlugField(unique=True, verbose_name="Region machine name")

    def __unicode__(self):
        return self.verbose_name

    class Meta:
        ordering = ('name',)

class Block(models.Model):
    region = models.ForeignKey('Region', related_name='elements')
    flag = models.ForeignKey('flags.Flag', null=True, blank=True, related_name="blocks")    

    weight = models.IntegerField(verbose_name="Weight")

    title = models.CharField(max_length=100, verbose_name="Title", help_text="Use {{ object, user, request }} tags for dynamic title")
    body = models.TextField(verbose_name="Block body", blank=True, help_text="Use {{ object, user, request }} tags for dynamic content")
    
    ACL_MODES = (('r', 'List rejected'), ('a', 'List allowed'))
    acl_mode = models.CharField(max_length=1, choices=ACL_MODES, verbose_name="Vew ACL list mode", default='r')

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('weight',)
       
class BlockMenu(models.Model):
    block = models.ForeignKey('Block', related_name='menus')
    menu = models.ForeignKey('menu.Menu', limit_choices_to={'category': 's'}, related_name="blocks")
    weight = models.IntegerField(verbose_name="Weight")

class BlockACLItem(models.Model):
    block = models.ForeignKey('Block', related_name="acl")
    VIEWS = (('c', 'component'), ('p', 'prospect'), ('r', 'record'))
    view_type = models.CharField(max_length=1, choices=VIEWS)
    view_name = models.SlugField(verbose_name="View name")

    class Meta:
        unique_together = (('block', 'view_type', 'view_name'),)

    

