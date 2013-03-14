import hashlib
from django.conf import settings
from synergy.contrib import signedurl
import re

class OpenURL(object):
    _regex = re.compile('|'.join(settings.OPEN_URLS), re.UNICODE)

    def __init__(self):
        if settings.DEBUG:
            self._regex = re.compile('|'.join(settings.OPEN_URLS + (settings.MEDIA_URL, settings.STATIC_URL)), re.UNICODE)

    def match(self, url):
        return self._regex.search(url)

open_url_match = OpenURL()

def get_sign(url):
    try:
        user = signedurl.middleware.get_current_user()
        return hashlib.md5("%s:%s:%s" % (url, settings.SECRET_KEY, user.id)).hexdigest()
    except Exception, error:
        return hashlib.md5("%s:%s" % (url, settings.SECRET_KEY)).hexdigest()
