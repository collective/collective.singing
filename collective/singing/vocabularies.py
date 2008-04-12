import sha

from zope import interface
from zope import component
import zope.schema.interfaces
import zope.schema.vocabulary
from zope.schema.interfaces import ISource, IContextSourceBinder
from zope.schema.interfaces import ITitledTokenizedTerm
from zope.app.form.browser.interfaces import ISourceQueryView, ITerms

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

class SubscriptionTerm(object):
    interface.implements(ITitledTokenizedTerm)
    component.adapts(interfaces.ISubscription)
    
    def __init__(self, subscription):
        self.subscription = subscription

    @property
    def value(self):
        return self.subscription

    @property
    def token(self):
        salt = repr(self.subscription)
        return sha.sha(salt).hexdigest()
 
    @property
    def title(self):
        """XXX: This is just a prototype implementation."""
        
        data = self.subscription.composer_data
        if not data:
            raise ValueError("Subscription has no data.")
        
        format = self.subscription.metadata['format']
        composer = self.subscription.channel.composers[format]

        # by default, choose first composer data value as label
        label = data.values()[0]
        for name in composer.schema:
            if interfaces.ISubscriptionLabel.providedBy(composer.schema[name]):
                label = getattr(data, name)
                break

        return "%s (%s)" % (label, self.subscription.channel.name)

class SubscriptionQuerySource(object):
    """Subscription query source.

    This source supports text-queries for subscriptions registered for
    a channel.

      >>> source = SubscriptionQuerySource(None)
      >>> source # doctest: +ELLIPSIS
      <collective.singing.vocabularies.SubscriptionQuerySource object at ...>
    """
    
    interface.implements(ISource)
    interface.classProvides(IContextSourceBinder)

    def __init__(self, context, channels=None):
        self.context = context
        self.channels = channels

    def __contains__(self, term):
        """Return whether the value is available in this source.

        For now, we'll just verify that ``value`` is a subscription.
        """
        return interfaces.ISubscription.providedBy(term.value)

    def search(self, query_string):
        if self.channels is None:
            channels = component.getUtility(interfaces.IChannelLookup)()
        else:
            channels = self.channels

        results = []
        for channel in channels:
            for subscriptions in channel.subscriptions.values():
                results.extend(
                    [s for s in subscriptions if query_string in repr(s)])
        return results

class SubscriptionQuerySourceBinder(object):
    interface.implements(IContextSourceBinder)

    def __init__(self, channels=None):
        self.channels = channels
    
    def __call__(self, context):
        return SubscriptionQuerySource(context, self.channels)
