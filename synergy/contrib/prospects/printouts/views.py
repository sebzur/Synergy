from django import template, http
from django.db.models import get_model
from django.views import generic
from synergy.contrib.prospects.views import DetailView, ListView
from pyPdf import PdfFileReader, PdfFileWriter
import cStringIO as StringIO
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile


class PDFResponseMixin(object):
    def render_to_response(self, context):
        content = self.convert_context_to_pdf(context)
        return self.get_pdf_response(context, content)

    def get_pdf_response(self, context, content, **httpresponse_kwargs):
        # w content siedzi wygenerowany PDF
        response = http.HttpResponse(content.getvalue(), 
                                mimetype='application/pdf',
                                **httpresponse_kwargs)
        response['Content-Disposition'] = 'attachement; filename=%s' % self.get_pdf_template_obj(context).get_filename(context)
        return response

    def convert_context_to_pdf(self, context):
        pdf_template = self.get_pdf_template_obj(context)
        return pdf_template.get_pdf(context,self.get_variant_pdf())

    def get_pdf_template_obj(self, context):
        pass

    def get_variant_pdf(self):
        return get_model('printouts', 'VariantPDF').objects.get(name=self.kwargs.get('variant_pdf'))

    def get_context_data(self, *args, **kwargs):
        ctx = super(PDFResponseMixin, self).get_context_data(*args, **kwargs)
        ctx['request'] = self.request
        return ctx


class PDFDetailView(PDFResponseMixin, DetailView):
    def get_pdf_template_obj(self, context, **kwargs):
        return self.get_variant_pdf().tpl

    
class PDFListView(PDFResponseMixin, ListView):
    def get_pdf_template_obj(self, context):
        return self.get_variant_pdf().tpl


class PDFDetailListView(PDFResponseMixin, ListView):
    def get_pdf_template_obj(self, context):
        return self.get_variant_pdf().tpl

    def convert_context_to_pdf(self, context):
        results = self.get_results()
        pdf_template = self.get_pdf_template_obj(context)
        output = PdfFileWriter()
        for result in results:
            stream = PdfFileReader( pdf_template.get_pdf({'object': result,},self.get_variant_pdf()) )
            for page_num in range(stream.getNumPages()):
                output.addPage( stream.getPage(page_num) )
        strIO = StringIO.StringIO() 
        output.write(strIO)
        return strIO


class StoredPDFView(generic.DetailView):
    def get_object(self):
        return get_model('printouts','PDFFile').objects.get(uuid=self.kwargs.get('uuid'))

    def render_to_response(self,context, **httpresponse_kwargs):
        content = open(self.get_object().pdf.file.name)
        response = http.HttpResponse(content.read(),
                                mimetype='application/pdf',
                                **httpresponse_kwargs)
        response['Content-Disposition'] = 'attachement; filename=%s.pdf' % self.get_object().uuid
        return response    
