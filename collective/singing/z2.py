from zope import interface
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError
from Products.Five.browser import decode
import z3c.form.interfaces

from collective.singing import interfaces

# XXX This is ripped from zope.publisher.http.HTTPRequest; we should
# move this into Five
def setup_locale(request):
    envadapter = IUserPreferredLanguages(request, None)
    if envadapter is None:
        return None
    
    langs = envadapter.getPreferredLanguages()
    for httplang in langs:
        parts = (httplang.split('-') + [None, None])[:3]
        try:
            return locales.getLocale(*parts)
        except LoadLocaleError:
            # Just try the next combination
            pass
    else:
        # No combination gave us an existing locale, so use the default,
        # which is guaranteed to exist
        return locales.getLocale(None, None, None)

# XXX Add a getURL method on the request object; we should move this
# into Five
def add_getURL(request):
    def getURL(level=0, path_only=False):
        assert level == 0 and path_only == False
        return request['ACTUAL_URL']
    request.getURL = getURL

def switch_on(view, request_layer=interfaces.IFormLayer):
    request = view.request
    if not request_layer.providedBy(request):
        interface.alsoProvides(request, request_layer)
        request.locale = setup_locale(request)
        add_getURL(request)
        decode.processInputs(request)
