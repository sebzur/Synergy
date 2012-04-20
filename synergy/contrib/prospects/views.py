# -*- coding: utf-8 -*-
from django.views.generic import DetailView, FormView
from django.db.models import get_model
from django.shortcuts import get_object_or_404

from synergy.templates.regions.views import RegionViewMixin

from django.core.urlresolvers import reverse

from synergy.contrib.prospects.forms import prospectform_factory, build_query


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import signals


class ProspectView(RegionViewMixin, FormView):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProspectView, self).dispatch(*args, **kwargs)

    def get_prospect_variant(self):
        return get_model('prospects', 'ProspectVariant').objects.get(pk=self.kwargs.get('pk'), name=self.kwargs.get('variant'))

    def get_prospect(self):
        return self.get_prospect_variant().prospect

    def get_form_class(self):
        return prospectform_factory(self.get_prospect(), self.kwargs.get('variant'))

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(ProspectView, self).get_form_kwargs(*args, **kwargs)
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(ProspectView, self).get_context_data(*args, **kwargs)
        ctx['title'] = u"%s" % self.get_prospect().verbose_name
        ctx['prospect'] = self.get_prospect()

        if self.get_prospect_variant().displays.filter(display_type__model="custompostfixdisplay").exists():
            display = self.get_prospect_variant().displays.filter(display_type__model="custompostfixdisplay").get().display
            postfixes = {'prospect': display.postfix,}
            if display.use_posthead:
                postfixes['posthead'] = display.postfix
            ctx['region_postfixes'] = postfixes
        results = []
        if kwargs['form'].is_valid():
            results = self.get_results(self.kwargs.get('variant'), **dict(kwargs['form'].cleaned_data))
        ctx['results'] = results
        return ctx

    def get_results(self, variant, *args, **kwargs):
        results = self.get_prospect_variant().filter(**build_query(kwargs))
        signals.prospect_results_created.send(sender=self.get_prospect(), results=results, request=self.request)
        return results

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


