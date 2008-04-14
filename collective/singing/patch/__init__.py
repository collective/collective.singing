import zope.i18nmessageid
import zope.app.i18n

def do():
    # We have to do this because Zope 2 decides not to include
    # zope.app.catalog!
    zope.i18nmessageid.ZopeMessageFactory = zope.app.i18n.ZopeMessageFactory
    import BTrees__init__
