# -*- coding: utf-8 -*-
# Create your views here.
from djangorestframework.views import View
from djangorestframework import status, permissions
from synergy.contrib.prospects.views import ProspectMixin, build_query
from synergy.contrib.prospects.forms import build_query
from django.db.models import get_model, Q
import urllib

import numpy


class DataTablesMixin(object):
    # http://www.datatables.net/usage/server-side
    global_attrs = ['iDisplayStart', 'iDisplayLength', 'iColumns', 
                    'sSearch', 'bRegex', 'iSortingCols', 'sEcho']

    column_attrs = ['bSearchable', 'sSearch', 'bRegex', 'bSortable',
                    'mDataProp']

    sorting_attrs = ['iSortCol', 'sSortDir']


    def get_attr_type(self, attr):
        # unquote for unicode chars handling
        return {'i': int, 's': urllib.unquote, 'b': bool, 'm': str}[attr[0]]

    def get_global_attrs(self):
        # dosyc wazne, zeby pilnowac czy GET ma klucz
        return dict(((attr, self.get_attr_type(attr)(self.request.GET.get(attr))) for attr in self.global_attrs if self.request.GET.has_key(attr)))

    def get_sorting_attrs(self):
        columns = {}
        for i in range(self.get_global_attrs().get('iSortingCols')):
            columns[int(self.request.GET.get('%s_%d' % (self.sorting_attrs[0], i)))] = self.request.GET.get('%s_%d' % (self.sorting_attrs[1], i))
        return columns

    @property
    def search_phrase(self):
        phrase = self.get_global_attrs().get('sSearch')
        return phrase if phrase != 'None' else u''

    @property
    def results_from(self):
        return self.get_global_attrs().get('iDisplayStart')

    @property
    def results_to(self):
        return self.results_from + self.get_global_attrs().get('iDisplayLength')

    @property
    def echo(self):
        return self.get_global_attrs().get('echo')


class Process(ProspectMixin, DataTablesMixin, View):
    access_prefix = 'prospect.list'
    permissions = (permissions.IsAuthenticated, )
    
    def get_variant_arguments(self, **kwargs):
        return self.get_prospect_variant(**kwargs).arguments.all()

    def get_arguments(self):
        return self.kwargs

    def prepare_data(self, request):
        table = self.get_representation(**self.kwargs)
        # Uwaga -- bardzo ważna jest kolejność ordering
        fields = get_model('prospects', 'field').objects.filter(id__in=table.columns.values_list('field', flat=True)).order_by('column__weight')
        ordering = dict([(fields[field_id], direction) for field_id, direction in self.get_sorting_attrs().iteritems()])
        url_triggers = table.columns.values_list('trigger_lookup', 'negate_trigger')
        return self.get_data(fields, self.get_arguments(), self.results_from, self.results_to, ordering, url_triggers, self.search_phrase)

    def get_data(self, fields, arguments, results_from, results_to, ordering, url_triggers, search_phrase):
        return self.get_prospect_variant(**self.kwargs).get_data(self.request.user, build_query(self.get_query_dict()),
                                                                 fields, arguments, results_from, results_to, ordering, url_triggers, search_phrase)

    def get(self, request, *args, **kwargs):
        data_t = self.prepare_data(request)

        data = {"sEcho": "%s" % self.echo,
                "iTotalRecords": data_t.get('results').count(),
                "iTotalDisplayRecords": data_t.get('filtered_results').count(),
                "aaData": data_t.get('data')
                }
        return data
