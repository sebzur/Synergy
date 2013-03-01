import hashlib
from django.utils.encoding import iri_to_uri
from django.conf import settings

def get_sign(url):
    return hashlib.md5("%s:%s" % (url, settings.SECRET_KEY)).hexdigest()

def signed_reverse(prefix, url):
    full_url = u'%s%s' % (prefix, url)
    if full_url not in settings.OPEN_URLS:
        return  "%s?sign=%s" % (iri_to_uri(full_url), get_sign(full_url))
    return iri_to_uri(full_url)
