from django.db import models

class VariantPDF(models.Model):
    variant = models.OneToOneField('prospects.ProspectVariant', related_name="pdf",null=True,blank=True)
    detail_tpl = models.ForeignKey('pdfgen.PDFTemplate', related_name='detail_pdfs',null=True,blank=True)
    list_tpl = models.ForeignKey('pdfgen.PDFTemplate', related_name='list_pdfs',null=True,blank=True)

    class Meta:
        verbose_name = "PDF"

