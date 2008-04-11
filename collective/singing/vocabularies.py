from zope import interface
from zope import component

from zope.app.schema.vocabulary import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from collective.singing.interfaces import IChannel

class ChannelVocabularyFactory(object):
    """Channel vocabulary.

    >>> from zope import interface, component
    >>> from collective.singing.interfaces import IChannel
    
    >>> class MockChannel(object):
    ...     interface.implements(IChannel)
    ...     name = 'mock'; title = u'Mock'
    
    >>> component.provideUtility(MockChannel())

    Look up channels.
    
    >>> ChannelVocabulary(None) # doctest: +ELLIPSIS
    <zope.schema.vocabulary.SimpleVocabulary object at ...>
    
    """
    
    interface.implements(IVocabularyFactory)

    def __call__(self, context):
        utilities = component.getUtilitiesFor(IChannel)
        items = [SimpleTerm(channel, name, channel.title) \
                 for name, channel in utilities]
        
        return SimpleVocabulary(items)

ChannelVocabulary = ChannelVocabularyFactory()
