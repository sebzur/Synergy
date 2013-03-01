import hashlib
from django.utils.encoding import iri_to_uri
from django.conf import settings
from synergy.contrib.signedurl import signer

def signed_reverse(prefix, url):
    full_url = u'%s%s' % (prefix, url)
    if full_url not in settings.OPEN_URLS:
        return  "%s?sign=%s" % (iri_to_uri(full_url), signer.get_sign(full_url))
    return iri_to_uri(full_url)
