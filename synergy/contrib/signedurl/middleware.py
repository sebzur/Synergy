from django.conf import settings
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect
import hashlib
from django.http import Http404
from synergy.contrib.signedurl.urlresolvers import get_sign

class RequireSignedURLMiddleware(object):
    def __init__(self):
        self.require_login_path = getattr(settings, 'REQUIRE_LOGIN_PATH', '/login/')
    
    def process_request(self, request):
        if request.path not in settings.OPEN_URLS:
            if not request.GET.has_key('sign'):
                raise Http404
            proper_hash = get_sign(request.path)
            if proper_hash != request.GET.get('sign'):
                raise Http404



