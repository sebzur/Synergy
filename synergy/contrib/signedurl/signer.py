import hashlib
from django.conf import settings
from synergy.contrib import signedurl

def get_sign(url):
    try:
        user = signedurl.middleware.get_current_user()
        return hashlib.md5("%s:%s:%s" % (url, settings.SECRET_KEY, user.id)).hexdigest()
    except Exception, error:
        return hashlib.md5("%s:%s" % (url, settings.SECRET_KEY)).hexdigest()
