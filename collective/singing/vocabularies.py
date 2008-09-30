from zope import interface
from zope import component
import zope.schema.interfaces
import zope.schema.vocabulary

from collective.singing import interfaces
from collective.singing.channel import channel_lookup

def channel_vocabulary(context):
    terms = []
    for channel in channel_lookup():
        terms.append(
            zope.schema.vocabulary.SimpleTerm(
                value=channel,
                token=channel.name,
                title=channel.title))
    return zope.schema.vocabulary.SimpleVocabulary(terms)
interface.alsoProvides(channel_vocabulary,
                       zope.schema.interfaces.IVocabularyFactory)

def subscribeable_channel_vocabulary(context):
    terms = []
    for channel in channel_lookup(only_subscribeable=True):
        terms.append(
            zope.schema.vocabulary.SimpleTerm(
                value=channel,
                token=channel.name,
                title=channel.title))
    return zope.schema.vocabulary.SimpleVocabulary(terms)
zope.interface.alsoProvides(subscribeable_channel_vocabulary,
                            zope.schema.interfaces.IVocabularyFactory)

def sendable_channel_vocabulary(context):
    terms = []
    for channel in channel_lookup(only_sendable=True):
        terms.append(
            zope.schema.vocabulary.SimpleTerm(
                value=channel,
                token=channel.name,
                title=channel.title))
    return zope.schema.vocabulary.SimpleVocabulary(terms)
zope.interface.alsoProvides(sendable_channel_vocabulary,
                            zope.schema.interfaces.IVocabularyFactory)
