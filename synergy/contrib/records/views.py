import datetime
import forms
import re
import urlparse

from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import get_model
from django.forms import models as model_forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from django.utils.encoding import smart_str 
from django.template import RequestContext
from models import get_parent_field, get_parent_for_instance
from synergy.templates.regions.views import RegionViewMixin
from synergy.contrib.components.views import RecordComponentViewMixin



class RecordViewMixin(RecordComponentViewMixin):

    def get_record_setup(self, **kwargs):
        db_name = 'default'
        if settings.FRONTEND_DB:
            db_name = { True: settings.FRONTEND_DB,
                        False: 'default',
                        }.get(kwargs.get('name').startswith(settings.FRONTEND_PREFIX))
        return get_model('records', 'RecordSetup').objects.using(db_name).get(name=kwargs.get('name'))

    def get_model(self):
        return self.get_record_setup(**self.kwargs).model.model_class()

    def get_queryset(self):
        return self.get_model()._default_manager.all()

    def get_excluded_fields(self):
        setup = self.get_record_setup(**self.kwargs)
        if setup.only_registered_fields:
            fields = setup.fields.all().values_list('field', flat=True)
            return filter(lambda x: x not in fields, setup.model.model_class()._meta.get_all_field_names())
        return []

    def get_hidden_fields(self):
        setup = self.get_record_setup(**self.kwargs)
        return setup.fields.filter(is_hidden=True).values_list('field', flat=True)

    def get_action_setup(self):
        return self.get_record_setup(**self.kwargs).get_action_setup(action=self.action_code)
    

class MessagesMixin(object):

    def get_success_message(self, **kwargs):
        action_setup = self.get_action_setup()
        std_msg = self.success_message % {'object': self.object}
        if action_setup:
            return action_setup.get_success_message(**kwargs) or std_msg
        return std_msg

    def get_error_message(self, **kwargs):
        action_setup = self.get_action_setup()
        std_msg = self.error_message % {'object': self.object}

        if action_setup:
            return action_setup.get_error_message(**kwargs) or std_msg
        return std_msg

    def handle_success(self, handler, *args, **kwargs):
        return self.handle('success', handler, *args, **kwargs)

    def handle_error(self, handler, *args, **kwargs):
        return self.handle('error', handler, *args, **kwargs)

    def handle(self, tag, handler, *args, **kwargs):
        handler_output = handler(*args, **kwargs)
        getattr(messages, tag)(self.request, getattr(self, 'get_%s_message' % tag)(**kwargs), fail_silently=True)
        return handler_output



class CUMessagesMixin(MessagesMixin):
    def form_valid(self, *args, **kwargs):
        return self.handle_success(super(CUMessagesMixin, self).form_valid, *args, **kwargs)
  
    def form_invalid(self, *args, **kwargs):
        return self.handle_error(super(CUMessagesMixin, self).form_invalid, *args, **kwargs)

class DMessagesMixin(MessagesMixin):
    def delete(self, *args, **kwargs):
        return self.handle_success(super(DMessagesMixin, self).delete, *args, **kwargs)

# Due to MRO it is important to keep CUMessagexMixin priori to CreateView
class CreateRecordView(RegionViewMixin, RecordViewMixin, CUMessagesMixin, CreateView):
    access_prefix = 'record.create'
    action_code = 'c'
    success_message = _("Object %(object)s has been created!")                
    error_message = _("Form errors have been detected! Object has not been created. Please refer to the form fields for the detail errors log.")                

    def get_object(self):
        # required for proper dispatch in components
        return None

    def dispatch(self, request, *args, **kwargs):
        setup = self.get_record_setup(**kwargs)
        expressions = []
        for argument in setup.arguments.all():
            expressions.append("(?P<%s>%s)" % (argument.name, argument.regex))
        regex = "/".join(expressions)
        path = kwargs.get('arguments')

        if path:
            _kwargs = self.resolve(regex, path)
            if not _kwargs:
                raise Http404
            str_converted = dict(((smart_str(k), v) for k, v in _kwargs.iteritems()))
            kwargs.update(str_converted)

        return super(CreateRecordView, self).dispatch(request, *args, **kwargs)

    def resolve(self, regex, path):
        _regex = re.compile(regex, re.UNICODE)
        match = _regex.search(path)
        if match:
            return match.groupdict()

    def get_form_class(self, *args, **kwargs):
        setup = self.get_record_setup(**self.kwargs)
        return forms.createform_factory(setup.model.model_class(), setup.related_o2m_models.all(), setup.related_m2m_models.all(), setup.use_model_m2m_fields, excluded_fields=self.get_excluded_fields(), hidden_fields=self.get_hidden_fields())

    def get_arguments(self):
        _kwargs = self.kwargs.copy()
        _kwargs.pop('name') # remove record name
        _kwargs.update({'request': self.request})
        return _kwargs

    def get_initial(self):
        return self.get_record_setup(**self.kwargs).get_initial(**self.get_arguments())

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(CreateRecordView, self).get_form_kwargs(*args, **kwargs)
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateRecordView, self).get_context_data(*args, **kwargs)
        setup = self.get_record_setup(**self.kwargs)
        ctx['initial'] = self.get_initial()
        ctx['cancel_url'] = setup.get_cancel_url(**self.get_arguments())
        ctx.update(setup.get_context_elements(ctx, self.action_code))
        return ctx

    def get_success_url(self):
        tmp = self.get_arguments().copy()
        tmp.update({'object': self.object})
        return self.get_record_setup(**self.kwargs).get_success_url(**tmp)

    
# Due to MRO it is important to keep CUMessagexMixin priori to UpdateMixin
class UpdateRecordView(RecordViewMixin, RegionViewMixin, CUMessagesMixin, UpdateView):
    access_prefix = 'record.update'
    action_code = 'u'
    success_message = _("Object %(object)s has been updated!")                
    error_message = _("Form errors have been detected! Object has not been updated. Please refer to the form fields for the detail errors log.")                

    def get_object(self):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))

    def get_form_class(self, *args, **kwargs):
        setup = self.get_record_setup(**self.kwargs)
        return forms.createform_factory(setup.model.model_class(), setup.related_o2m_models.all(), setup.related_m2m_models.all(), setup.use_model_m2m_fields, excluded_fields=self.get_excluded_fields(), hidden_fields=self.get_hidden_fields())

    def get_context_data(self, *args, **kwargs):
        ctx = super(UpdateRecordView, self).get_context_data(*args, **kwargs)
        setup = self.get_record_setup(**self.kwargs)
        ctx['cancel_url'] = self.get_success_url()
        ctx['setup'] = setup

        ctx['delete_enabled'] = setup.is_delete_enabled()

        ctx.update(setup.get_context_elements(ctx, self.action_code))
        return  ctx

#    def get_arguments(self):
#        _kwargs = self.kwargs.copy()
#        _kwargs.pop('name') # remove record name
#        _kwargs.update({'request': self.request})
#        return _kwargs

#    def get_initial(self):
#        return self.get_record_setup(**self.kwargs).get_initial(**self.get_arguments())

    def form_valid(self, form):
        return super(UpdateRecordView, self).form_valid(form)            

    def get_success_url(self):
        return self.get_record_setup(**self.kwargs).get_success_url(**{'object': self.get_object()})

class DeleteRecordView(RecordViewMixin, RegionViewMixin, DMessagesMixin, DeleteView):
    access_prefix = 'record.delete'
    action_code = 'd'
    success_message = _("Object %(object)s has been deleted!")                
    error_message = _("Form errors have been detected! Object has not been deleted. Please refer to the form fields for the detail errors log.")                

    def get_object(self):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))

    def get_context_data(self, *args, **kwargs):
        ctx = super(DeleteRecordView, self).get_context_data(*args, **kwargs)
        ctx['cancel_url'] = self.get_record_setup(**self.kwargs).get_success_url(**{'object': self.object})
        setup = self.get_record_setup(**self.kwargs)
        ctx.update(setup.get_context_elements(ctx, self.action_code))
        return  ctx

    def get_success_url(self):
        return self.get_record_setup(**self.kwargs).get_generic_url(**{'object': self.object})
