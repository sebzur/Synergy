import datetime
import itertools
import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.db.models import get_model, ObjectDoesNotExist, Q

class ProtectedView(object):
    access_prefix = None
    # access prefix is defined as a pair 'prospect.variant', 
    # 'prospect.detail', 'records.create', etc.

    def dispatch(self, request, *args, **kwargs):
        perm = self.get_perm_name(**kwargs)
        PERM_MISSING = perm and not request.user.has_perm(perm, self.get_obj(**kwargs))
        STRICT_AUTH_MISSING = settings.COMPONENTS_STRICT_AUTH and not request.user.is_authenticated()
        if PERM_MISSING or STRICT_AUTH_MISSING:
            return self.login_redirect(request)
        return super(ProtectedView, self).dispatch(request, *args, **kwargs)

    def login_redirect(self, request, login_url=settings.LOGIN_URL, redirect_field_name=REDIRECT_FIELD_NAME):
        path = request.build_absolute_uri()
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse.urlparse(login_url)[:2]
        current_scheme, current_netloc = urlparse.urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
            (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        return redirect_to_login(path, login_url, redirect_field_name)
        
    def get_perm_name(self, **kwargs):
        flag = self.get_access_flag(**kwargs)
        if flag:
            return "%s.%s" % (self.get_perm_prefix(**kwargs), flag.name)
        return None

    def get_access_flag(self, **kwargs):
        """ Returns view access flag. To have this working it is required to register
        the view with the components system.

        If the view is not registered, it is open to the public.

        """

        if not self.access_prefix:
            raise ValueError("Access prefix has to be defined!")
        assignment = self.get_component_assignment(**kwargs)
        if assignment:
            return self._get_func_flag(assignment, self.access_prefix) or assignment.flag or assignment.component.flag

    def _get_func_flag(self, assignment, access_prefix):
        app, func = access_prefix.split('.')

        assignment_func_flag = getattr(assignment, '%s_flag' % func)
        component_func_flag = getattr(assignment.component, '%s_flag' % func)
        app_flag = getattr(assignment.component, '%s_flag' % app)
        return assignment_func_flag or component_func_flag or app_flag


class AuthBase(object):

    def get_custom_access_flag(self, **kwargs):
        return None

    def get_obj(self, **kwargs):
        return None

    def get_perm_prefix(self, **kwargs):
        raise NotImplementedError
    

class ComponentViewMixin(ProtectedView, AuthBase):

    def get_component(self, **kwargs):
        assignment = self.get_component_assignment(**kwargs)
        if assignment: 
            return assignment.component
        return None

    def get_component_assignment(self, **kwargs):
        item = self.get_component_item(**kwargs)
        try:
            return item.component_assignment
        except ObjectDoesNotExist:
            return None

    def get_blocks(self):
        regions = dict( (region, None) for region in get_model('components', 'region').objects.values_list('name', flat=True))

        app, func = self.access_prefix.split('.')
        component_item =  self.get_component_item(**self.kwargs)
        component = self.get_component(**self.kwargs)

        for region in regions:
            # No ACL tested
            blocks = [get_model('components', 'block').objects.filter(region__name=region, acl__isnull=True).values_list('id', flat=True)]
            
            # ACL tests
            component_acl_query = Q(view_type='c') & Q(view_name=component.name)
            func_acl_query = Q(view_type=app[0]) & Q(view_name=component_item.name)

            acl = get_model('components', 'BlockACLItem').objects.filter(component_acl_query|func_acl_query)

            query_action = {'r': 'exclude', 'a': 'filter'}
            for mode in ('a', 'r'):
                _b = get_model('components', 'block').objects.filter(region__name=region, acl_mode=mode, acl__isnull=False)
                blocks.append(getattr(_b, query_action[mode])(acl__in=acl).values_list('id', flat=True))

                
            regions[region] = get_model('components', 'block').objects.filter(id__in=itertools.chain(*blocks)).order_by('weight',)
        return regions


    def get_context_data(self, *args, **kwargs):
        ctx = super(ComponentViewMixin, self).get_context_data(*args, **kwargs)
        ctx['component'] = self.get_component(**self.kwargs)

        ctx['blocks'] = []
        if ctx['component']:
            ctx['blocks'] = self.get_blocks()

        return ctx


class RecordComponentViewMixin(ComponentViewMixin):

    def get_component_item(self, **kwargs):
        return self.get_record_setup(**kwargs)

    # -------------------------
    # Auth-related methods
    # -------------------------
    def get_perm_prefix(self, **kwargs):
        return 'records.recordsetup'


class ProspectComponentViewMixin(ComponentViewMixin):

    def get_component_item(self, **kwargs):
        return self.get_prospect_variant(**kwargs)

    # -------------------------
    # Auth-related methods
    # -------------------------
    def get_perm_prefix(self, **kwargs):
        return 'prospects.prospectvariant'




