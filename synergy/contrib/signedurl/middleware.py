from django.conf import settings
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect
import hashlib
from django.http import Http404
from synergy.contrib.signedurl import signer

# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_path():
    return getattr(_thread_locals, 'path', None)

def get_current_request():
    return getattr(_thread_locals, 'request', None)


class RequireSignedURLMiddleware(object):
    def __init__(self):
        self.require_login_path = getattr(settings, 'REQUIRE_LOGIN_PATH', '/login/')
    
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.path = getattr(request, 'path', None)
        _thread_locals.request = request
        if request.path not in settings.OPEN_URLS:
            if not request.GET.has_key('sign'):
                raise Http404
            proper_hash = signer.get_sign(request.path)
            if proper_hash != request.GET.get('sign'):
                raise Http404

# USAGE:
# from yourproject.middleware import threadlocals
# threadlocals.get_current_user()
