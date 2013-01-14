from django import template, http
from django.db.models import get_model
from synergy.contrib.prospects.views import DetailView, ListView
from pyPdf import PdfFileReader, PdfFileWriter
import cStringIO as StringIO

class PDFResponseMixin(object):
    def render_to_response(self, context):
        return self.get_pdf_response(context, self.convert_context_to_pdf(context))

    def get_pdf_response(self, context, content, **httpresponse_kwargs):
        response = http.HttpResponse(content, 
                                mimetype='application/pdf',
                                **httpresponse_kwargs)
        response['Content-Disposition'] = 'attachement; filename=%s' % self.get_pdf_template_obj(context).get_filename(context)
        return response

    def convert_context_to_pdf(self, context):
        pdf_template = self.get_pdf_template_obj(context)
        return pdf_template.get_pdf(context).getvalue()

    def get_pdf_template_obj(self, context):
        pass

    def get_context_data(self, *args, **kwargs):
        ctx = super(PDFResponseMixin, self).get_context_data(*args, **kwargs)
        ctx['request'] = self.request
        return ctx


class PDFDetailView(PDFResponseMixin, DetailView):
    def get_pdf_template_obj(self, context, **kwargs):
        return get_model('pdfgen', 'PDFTemplate').objects.get(name=self.kwargs.get('template'))

    
class PDFListView(PDFResponseMixin, ListView):
    def get_pdf_template_obj(self, context):
        return get_model('pdfgen', 'PDFTemplate').objects.get(name=self.kwargs.get('template'))


class PDFDetailListView(PDFResponseMixin, ListView):
    def get_pdf_template_obj(self, context):
        return get_model('pdfgen', 'PDFTemplate').objects.get(name=self.kwargs.get('template'))

    def convert_context_to_pdf(self, context):
        results = self.get_results()
        pdf_template = self.get_pdf_template_obj(context)
        output = PdfFileWriter()
        for result in results:
            stream = PdfFileReader( pdf_template.get_pdf({'object': result,}) )
            for page_num in range(stream.getNumPages()):
                output.addPage( stream.getPage(page_num) )
        strIO = StringIO.StringIO() 
        output.write(strIO)
        return strIO.getvalue()

