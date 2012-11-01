import datetime
import forms
import re
import urlparse

from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.forms import models as model_forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from django.utils.encoding import smart_str 
from models import get_parent_field, get_parent_for_instance
from synergy.templates.regions.views import RegionViewMixin
from synergy.contrib.components.views import RecordComponentViewMixin


class RecordViewMixin(RecordComponentViewMixin):

    def get_record_setup(self, **kwargs):
        return get_model('records', 'RecordSetup').objects.get(name=kwargs.get('name'))

    def get_model(self, **kwargs):
        return self.get_record_setup(**kwargs).model.model_class()

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


class CreateRecordView(RegionViewMixin, RecordViewMixin, CreateView):
    access_prefix = 'record.create'

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
        ctx.update(setup.get_context_elements(ctx, 'c'))
        return  ctx

    def get_success_url(self):
        tmp = self.get_arguments().copy()
        tmp.update({'object': self.object})
        print 'Got succses url:', [self.get_record_setup(**self.kwargs).get_success_url(**tmp)]
        return self.get_record_setup(**self.kwargs).get_success_url(**tmp)

class UpdateRecordView(RecordViewMixin, RegionViewMixin, UpdateView):
    access_prefix = 'record.update'

    def get_object(self):
        return self.get_model(**self.kwargs).objects.get(pk=self.kwargs.get('pk'))

    def get_form_class(self, *args, **kwargs):
        setup = self.get_record_setup(**self.kwargs)
        return forms.createform_factory(setup.model.model_class(), setup.related_o2m_models.all(), setup.related_m2m_models.all(), setup.use_model_m2m_fields, excluded_fields=self.get_excluded_fields(), hidden_fields=self.get_hidden_fields())

    def get_context_data(self, *args, **kwargs):
        ctx = super(UpdateRecordView, self).get_context_data(*args, **kwargs)
        setup = self.get_record_setup(**self.kwargs)
        ctx['cancel_url'] = self.get_success_url()
        ctx['setup'] = setup

        ctx['delete_enabled'] = setup.is_delete_enabled()

        ctx.update(setup.get_context_elements(ctx, 'u'))
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

class DeleteRecordView(RecordViewMixin, RegionViewMixin, DeleteView):
    access_prefix = 'record.delete'

    def get_object(self):
        return self.get_model(**self.kwargs).objects.get(pk=self.kwargs.get('pk'))

    def get_context_data(self, *args, **kwargs):
        ctx = super(DeleteRecordView, self).get_context_data(*args, **kwargs)
        ctx['cancel_url'] = self.get_record_setup(**self.kwargs).get_success_url(**{'object': self.object})
        setup = self.get_record_setup(**self.kwargs)
        ctx.update(setup.get_context_elements(ctx, 'd'))
        return  ctx

    def get_success_url(self):
        return self.get_record_setup(**self.kwargs).get_generic_url(**{'object': self.object})
