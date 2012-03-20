# -*- coding: utf-8 -*-
from django.views.generic import DetailView, FormView
from django.db.models import get_model
from django.shortcuts import get_object_or_404

from synergy.templates.regions.views import RegionViewMixin

from django.core.urlresolvers import reverse

from synergy.contrib.prospects.forms import prospectform_factory

class ProspectView(RegionViewMixin, FormView):

    def get_prospect(self):
        return get_model('prospects', 'Prospect').objects.get(pk=self.kwargs.get('pk'))

    def get_form_class(self):
        return prospectform_factory(self.get_prospect())

    def get_context_data(self, *args, **kwargs):
        ctx = super(ProspectView, self).get_context_data(*args, **kwargs)
        ctx['title'] = u"%s" % self.get_prospect().verbose_name
        ctx['prospect'] = self.get_prospect()

        results = []
        if kwargs['form'].is_valid():

            results = self.get_results(**dict(self._filter_empty(kwargs['form'].cleaned_data)))
        ctx['results'] = results

        return ctx

    def _filter_empty(self, data):
        for k, v in data.iteritems():
            if v:
                yield (k, v)

    def get_results(self, *args, **kwargs):
        query = dict([(field.split('aspect_')[1], {'operator': 'exact', 'value': value}) for field, value in kwargs.iteritems()])
        return self.get_prospect().filter(**query)

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


