import forms
import datetime

from django.db.models import get_model
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from synergy.templates.regions.views import RegionViewMixin
from django.core.urlresolvers import reverse
from django.forms import models as model_forms
from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from models import get_parent_field, get_parent_for_instance

class ProtectedView(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProtectedView, self).dispatch(*args, **kwargs)


class ObjectViewMixin(object):
    def get_model_setup(self):
        return get_model('records', 'RecordSetup').objects.get(name=self.kwargs.get('name'))

    def get_model(self):
        return self.get_model_setup().model.model_class()

    def get_queryset(self):
        return self.get_model()._default_manager.all()


class CreateObjectView(ProtectedView, RegionViewMixin, ObjectViewMixin, CreateView):

    def get_form_class(self, *args, **kwargs):
        setup = self.get_model_setup()
        return forms.createform_factory(setup.model.model_class(), setup.related_models.all())

    def get_success_url(self):
        #obj = self.get_parent() or self.object
        obj =  self.object
        # self.object jest ustawiany przy zapisie
        return reverse('detail', args=[self.get_model_setup().object_detail.variant.name, obj.id])

    def get_parent(self):
        parent = get_parent_field(self.get_model()._meta)
        if self.kwargs.get('pk'):
            return parent.rel.to.objects.get(id=self.kwargs.get('pk'))
        return None

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(CreateObjectView, self).get_form_kwargs(*args, **kwargs)
        kwargs['parent'] = self.get_parent()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(CreateObjectView, self).get_context_data(*args, **kwargs)
        ctx['title'] = 'Nowy pacjent'
        return  ctx


class UpdateObjectView(ProtectedView, RegionViewMixin, UpdateView, ObjectViewMixin):

    def get_object(self):
        return self.get_model().objects.get(pk=self.kwargs.get('pk'))

    def get_form_class(self, *args, **kwargs):
        setup = self.get_model_setup()
        return forms.createform_factory(setup.model.model_class(), setup.related_models.all())

    def get_success_url(self):
        return reverse('detail', args=[self.get_model_setup().object_detail.variant.name, self.object.id])

    def get_context_data(self, *args, **kwargs):
        ctx = super(UpdateObjectView, self).get_context_data(*args, **kwargs)
        ctx['title'] = 'Nowy pacjent'
        return  ctx

    def form_valid(self, form):
        if '_delete' in self.request.POST:
            parent = get_parent_for_instance(self.object)
            redirect_to = ('/')
            if parent:
                setup = get_model('records', 'RecordSetup').objects.get(model__model=parent._meta.object_name.lower())
                redirect_to =  reverse('detail', args=[setup.object_detail.variant.name, parent.id])
            self.get_object().delete()
            return HttpResponseRedirect(redirect_to)
        return super(UpdateObjectView, self).form_valid(form)            
