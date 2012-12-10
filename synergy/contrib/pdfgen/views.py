from django import template, http
from synergy.contrib.prospects.views import DetailView
import xhtml2pdf.pisa as pisa
import cStringIO as StringIO

class PDFResponseMixin(object):
    def render_to_response(self, context):
        return self.get_pdf_response(self.convert_context_to_pdf(context))

    def get_pdf_response(self, content, **httpresponse_kwargs):
        return http.HttpResponse(content, 
                                mimetype='application/pdf',
                                **httpresponse_kwargs)

    def convert_context_to_pdf(self, context):
        pdf_template = self.get_pdf_template_obj(context)
        tpl = pdf_template.get_template()
        html = tpl.render(template.Context(context))
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)
        return result.getvalue()

    def get_pdf_template_obj(self, context):
        pass


class PDFDetailView(PDFResponseMixin, DetailView):
    def get_pdf_template_obj(self, context):
        return context['objectdetail'].variant.pdf.detail_tpl

    
