from zope import interface
from zope import component
import zope.schema.interfaces
import zope.schema.vocabulary

from collective.singing import interfaces

def channel_vocabulary(context):
    terms = []
    for channel in component.getUtility(interfaces.IChannelLookup)():
        terms.append(
            zope.schema.vocabulary.SimpleTerm(
                value=channel,
                token=channel.name,
                title=channel.title))
    return zope.schema.vocabulary.SimpleVocabulary(terms)
interface.alsoProvides(channel_vocabulary,
                       zope.schema.interfaces.IVocabularyFactory)
