from collective.singing import MessageFactory as _
from zope.schema import ValidationError
from zope.tales.tales import CompilerError
from Products.CMFCore.Expression import Expression


class InvalidTAL(ValidationError):
    __doc__ = _("""TALES Compile Error""")


def validate_tal(value):
    """ Find compile bugs in tal """
    try:
        Expression(value)
    except CompilerError as e:
        raise InvalidTAL(value)
    return True
