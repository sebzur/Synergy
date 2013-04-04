# -*- coding: utf-8 -*-
import signals
import urllib 
import re

from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.encoding import smart_str 
from django.views import generic
from django.shortcuts import get_object_or_404
from django.conf import settings

from djangorestframework.views import View
from djangorestframework import status, permissions

from synergy.templates.regions.views import RegionViewMixin
from synergy.contrib.prospects.forms import prospectform_factory, build_query
from synergy.contrib.components.views import ProspectComponentViewMixin


class ProspectMixin(ProspectComponentViewMixin):

    def dispatch(self, request, *args, **kwargs):
        expressions = []
        for argument in self.get_variant_arguments(**kwargs):
            expressions.append("(?P<%s>%s)" % (argument.name, argument.regex))
        regex = "/".join(expressions)
        path = kwargs.get('arguments')
        if path:
            _kwargs = self.resolve(regex, path)
            if not _kwargs:
                raise Http404
            str_converted = dict(((smart_str(k), v) for k, v in _kwargs.iteritems()))
            kwargs.update(str_converted)
        return super(ProspectMixin, self).dispatch(request, *args, **kwargs)


    def resolve(self, regex, path):
        _regex = re.compile(regex, re.UNICODE)
        match = _regex.search(path)
        if match:
            return match.groupdict()


    def get_prospect_variant(self, **kwargs):
        db_name = 'default'
        if settings.FRONTEND_DB:
            db_name = { True: settings.FRONTEND_DB,
                        False: 'default',
                        }.get(kwargs.get('variant').startswith(settings.FRONTEND_PREFIX))
        return get_model('prospects', 'ProspectVariant').objects.using(db_name).get(name=kwargs.get('variant'))

    def get_prospect(self, **kwargs):
        return self.get_prospect_variant(**kwargs).prospect

    def get_representation(self, **kwargs):
        return self.get_prospect_variant(**kwargs).listrepresentation.representation

    def get_query_dict(self):
        kwgs = dict([(smart_str(k), v.encode('utf8')) for k, v in self.request.GET.iteritems() if k.split('__')[0] in ('aspect', 'lookup') ])
        return kwgs

    def get_context_data(self, *args, **kwargs):
        ctx = super(ProspectMixin, self).get_context_data(*args, **kwargs)
        prospect_variant = self.get_prospect_variant(**self.kwargs)
        ctx['title'] = u"%s" % prospect_variant.verbose_name
        ctx['prospect'] = prospect_variant.prospect
        ctx['variant'] = prospect_variant
        ctx['arguments'] = self.get_arguments()
        ctx['encoded'] = urllib.urlencode(self.get_query_dict())
        ctx['query'] = build_query(self.get_query_dict())
        return ctx


class AspectFormMixin(generic.FormView):

    def get_form_class(self):
        return prospectform_factory(self.request, self.get_prospect(**self.kwargs), self.kwargs.get('variant'))

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(AspectFormMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['request'] = self.request
        kwargs['instance'] = self.get_prospect_variant(**self.kwargs)
        return kwargs

    def get_initial(self):
        return self.get_query_dict()

    def form_valid(self, form):
        kwgs = self.get_query_dict()
        kwgs.update(dict((smart_str(key), value) for key, value in form.cleaned_data.iteritems()))
        for context in form.contexts.values():
            kwgs.update(dict((smart_str(key), value) for key, value in context.cleaned_data.iteritems()))

        # some older python version require dict keys to be strings when passed as kwargs
        c_kwgs = kwgs.copy()
        for k, v in c_kwgs.iteritems():
            if hasattr(v, 'id'):
                c_kwgs[k] = v.id
            else:
                try:
                    # urlencode recuire encoded data
                    c_kwgs[k] = v.encode('utf-8')
                except:
                    # sometimes v is not unicode instance
                    pass
        #c_kwgs = dict([(k, v.encode('utf-8')) for k, v in c_kwgs.items()])

        encoded = urllib.urlencode(c_kwgs)
        if self.request.GET.has_key('sign'):
            separator = "&"
        else:
            separator = "?"
        
        return HttpResponseRedirect("%s%s%s" % (self.get_success_url(), separator, encoded))

class ListView(ProspectMixin, RegionViewMixin, AspectFormMixin):
    access_prefix = 'prospect.list'

    def get_variant_arguments(self, **kwargs):
        return self.get_prospect_variant(**kwargs).arguments.all()

    def get_context_data(self, *args, **kwargs):
        ctx = super(ListView, self).get_context_data(*args, **kwargs)
        repr_obj = self.get_representation(**self.kwargs)
        ctx[repr_obj._meta.object_name.lower()] = repr_obj
        ctx.update(repr_obj.get_context_data(*args, **kwargs))
        return ctx

    def get_results(self):
        variant = self.get_prospect_variant( **self.kwargs)
        query = build_query(self.get_query_dict())
        user = self.request.user
        return variant.filter(user, **query)

    def get_arguments(self):
        return self.kwargs

    def get_success_url(self):
        if self.kwargs.has_key('arguments'):
            return reverse('list', args=[self.get_prospect_variant(**self.kwargs).name, self.kwargs.get('arguments')])
        return reverse('list', args=[self.get_prospect_variant(**self.kwargs).name])


class DetailView(ProspectMixin, RegionViewMixin, generic.DetailView):
    access_prefix = 'prospect.detail'

    def get_variant_arguments(self, **kwargs):
        return self.get_prospect_variant(**kwargs).arguments.all()

    def get_queryset(self):
        return self.get_prospect(**self.kwargs).filter(self.get_query_dict(), {})

    def get_query_dict(self):
        return {}

    def get_arguments(self):
        arguments = self.kwargs.copy()

        obj, parent = self.get_object(), self.get_parent()
        for d in self.get_prospect_variant(**self.kwargs).objectdetail.get_variant_contexts():
            arguments.update(d.get_arguments(obj, parent))

        return arguments

    def get_object_detail(self):
        return self.get_prospect_variant(**self.kwargs).objectdetail

    def get_parent(self):
        parent_id = self.kwargs.get('parent')
        if parent_id:
            return self.get_object_detail().parent.variant.get_model_class().objects.get(id=parent_id)

    def get_context_data(self, *args, **kwargs):
        ctx = super(DetailView, self).get_context_data(*args, **kwargs)
        ctx['objectdetail'] = self.get_object_detail()
        ctx['title'] = ctx['objectdetail'].get_title(self.get_object())
        ctx['body'] = ctx['objectdetail'].get_body(self.get_object(), self.request)
        ctx['name'] = self.get_prospect_variant(**self.kwargs).name
        ctx['parent'] = self.get_parent()
        ctx.update(self.get_prospect_variant(**self.kwargs).objectdetail.get_context_data(self.get_object(), self.get_parent(), *args, **kwargs))
        ctx_operator = self.get_prospect_variant(**self.kwargs).objectdetail.context_operator
        if ctx_operator:
            ctx_operator(self.request, self.get_object(), ctx, *args, **kwargs)
        return ctx

class DetailContextView(ProspectMixin, RegionViewMixin, AspectFormMixin, generic.detail.SingleObjectMixin):
    access_prefix = 'prospect.detail'

    def get_variant_arguments(self, **kwargs):
        ids = self.get_variant_context(**kwargs).argument_values.all().values_list('argument', flat=True)
        return self.get_prospect_variant(**kwargs).arguments.exclude(id__in=ids)

    def get_arguments(self):
        arguments = self.kwargs.copy()
        arguments.update(dict((smart_str(arg_val.argument.name), arg_val.value_field.get_value(self.get_object()))  for arg_val in self.get_variant_context(**self.kwargs).argument_values.all()))
        return arguments

    def get_success_url(self):
        return reverse('context', args=[self.kwargs.get('variant'),self.kwargs.get('pk'),self.kwargs.get('context')])

    def get(self, request, **kwargs):
        self.object = self.get_object()
        return super(DetailContextView, self).get(request, **kwargs)

    def get_prospect_variant(self, **kwargs):
        return self.get_variant_context(**kwargs).variant

    def get_variant_context(self, **kwargs):
        return get_model('prospects', 'VariantContext').objects.get(variant__name=kwargs.get('context'), object_detail__variant__name=kwargs.get('variant'))

    def get_object_detail(self):
        return get_model('prospects', 'ProspectVariant').objects.get(name=self.kwargs.get('variant')).objectdetail

    def get_queryset(self):
        return self.get_object_detail().variant.prospect.source.all()

    def get_parent(self):
        # na razie, poki nie obslugujemy argumentu w URLu
        return None

    def get_context_data(self, *args, **kwargs):
        ctx = super(DetailContextView, self).get_context_data(*args, **kwargs)
        ctx['objectdetail'] = self.get_object_detail()
        ctx['object'] = self.get_object()
        ctx['title'] = ctx['objectdetail'].get_title(self.get_object())
        ctx['body'] = ctx['objectdetail'].get_body(self.get_object(), self.request)
        ctx['name'] = self.get_prospect_variant(**self.kwargs).name


        ctx.update(self.get_object_detail().get_context_data(self.get_object(), self.get_parent(), *args, **kwargs))
        ctx.update(self.get_representation(**self.kwargs).get_context_data(*args, **kwargs))

        ctx['detail_context'] = self.get_variant_context(**self.kwargs)

        ctx['query'] = ctx['detail_context'].get_query(self.get_object(), self.get_parent())
        ctx['query'].update(build_query(self.get_query_dict()))
        return ctx


class RESTListView(ProspectMixin, View):
    access_prefix = 'prospect.list'

    permissions = (permissions.IsAuthenticated, )
    """ Provides the API to retrive PUMSREC settings information like countries, programmes, commision members. """
    
    def get(self, request, *args, **kwargs):
        kwgs = dict([(k,v,) for k,v in  self.request.GET.iteritems() if k.split('__')[0] in ('aspect', 'lookup') ])
        return self.get_results(**kwgs)

# --------------------------------------
# Do przeniesienia do indywidualnego modulu
# --------------------------------------

class RESTCalendarView(ProspectMixin, View):
    access_prefix = 'prospect.list'

    def get(self, request, *args, **kwargs):
        kwgs = dict([(k,v,) for k,v in  self.request.GET.iteritems() if k.split('__')[0] in ('aspect', 'lookup') ])

        rpr = self.get_representation()
        data_field = rpr.start_date_field

        for result in self.get_results(**kwgs):
            yield {'id': result.id,
                   'start': data_field.get_value(result),
                   'title': rpr.get_content(result),
                   'url': rpr.get_url(result)
                   }

    def get_results(self, *args, **kwargs):
        try:
            self.get_prospect_variant(**self.kwargs).validate_query(self.request.user, **build_query(kwargs))
            results = self.get_prospect_variant(**self.kwargs).filter(self.request.user, **build_query(kwargs))
            signals.prospect_results_created.send(sender=self.get_prospect_variant(**self.kwargs), results=results, request=self.request)
            return results
        except:
            return None
            
