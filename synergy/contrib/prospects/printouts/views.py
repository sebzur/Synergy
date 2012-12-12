from django import template, http
from synergy.contrib.prospects.views import DetailView

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
        return pdf_template.get_pdf(context)

    def get_pdf_template_obj(self, context):
        pass


class PDFDetailView(PDFResponseMixin, DetailView):
    def get_pdf_template_obj(self, context):
        return context['objectdetail'].variant.pdf.detail_tpl

    
