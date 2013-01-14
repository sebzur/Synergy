from django.db import models
from django.utils.translation import ugettext_lazy as _

class VariantPDF(models.Model):
    CHOICES = ( ('d','detail'), ('l','list') )
    variant = models.ForeignKey('prospects.ProspectVariant', related_name="pdfs")
    tpl = models.ForeignKey('pdfgen.PDFTemplate', related_name='variant_pdfs')
    mode = models.CharField(max_length=1, verbose_name="Template mode", choices=CHOICES)
    is_variant_action = models.BooleanField(verbose_name="Is variant action")
    custom_action_name = models.CharField(max_length=50, blank=True, verbose_name="Custom action name")

    def get_action_name(self):
        if self.custom_action_name:
            return self.custom_action_name
        if self.mode == 'l':
            return _("PDF list %s " % self.tpl.verbose_name)
        else:
            return _("PDF detail list %s" % self.tpl.verbose_name)

    def __unicode__(self):
        return self.variant.__unicode__() + ' PDFs'

    class Meta:
        verbose_name = "PDF"
        unique_together = (('variant', 'tpl'), )

