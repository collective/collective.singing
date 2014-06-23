import os
import logging
from DateTime import DateTime
from zope.schema import ValidationError
from zope.tales.tales import CompilerError
from Products.CMFCore.Expression import Expression
from dateutil.parser import parse
from collective.singing import MessageFactory as _

logger = logging.getLogger('collective.singing')

TIMEZONE = os.environ.get('TZ', None)
if TIMEZONE:
    from DateTime import Timezones
    if TIMEZONE not in Timezones():
        logger.info('Specified timezone not recognized: %s, '
            'defaulting to local timezone.' % TIMEZONE)
        TIMEZONE = None
if not TIMEZONE:
    from DateTime import DateTime
    TIMEZONE = DateTime().timezone()


class InvalidTAL(ValidationError):
    __doc__ = _("""TALES Compile Error""")


def validate_tal(value):
    """ Find compile bugs in tal """
    try:
        Expression(value)
    except CompilerError as e:
        raise InvalidTAL(value)
    return True


def date_hook(json_dict):
    if '<datetime>' in json_dict:
        # 2013-10-18T20:35:18+07:00
        if 'datetime' not in json_dict:
            return json_dict

        try:
            dt = parse(json_dict['datetime'])
        except ValueError, e:
            # XXX: Just let DateTime guess.
            dt = parse(DateTime(json_dict['datetime']).ISO())
            logger.info('StringToDate> %s, %s, guessed: %s' % (
                str(json_dict['datetime']),
                repr(e),
                repr(dt)))
        return DateTime(dt).toZone(TIMEZONE)
    return json_dict
