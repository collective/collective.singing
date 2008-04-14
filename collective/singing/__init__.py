import zope.i18nmessageid

from collective.singing import patch

MessageFactory = zope.i18nmessageid.MessageFactory('collective.singing')

patch.do()
