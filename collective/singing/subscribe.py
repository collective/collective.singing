import pprint

import persistent
import persistent.dict
import persistent.list
from zope import interface
from zope import component
import zope.event
import zope.lifecycleevent
import zope.index.text.interfaces
import zope.app.catalog.catalog
import zope.app.catalog.field
import zope.app.catalog.text
import zope.app.intid.interfaces
import zope.app.container.btree

from collective.singing import interfaces
import collective.singing.subscribe
from collective.singing import MessageFactory as _

def secret(channel, composer, data, request):
    """Look up an appropriate secret.

    Looks for a IRequestBasedSecret first, and falls back to an
    IComposerBasedSecret if none is available or if the
    IRequestBasedSecret component returns None.
    """
    try:
        rbs = component.getUtility(interfaces.IRequestBasedSecret)
    except component.ComponentLookupError, e:
        pass
    else:
        secret = rbs(request)
        if secret is not None:
            return secret
    
    cbs = interfaces.IComposerBasedSecret(composer)
    return cbs.secret(data)

def has_single_format(channel):
    """Returns format of a given channel's single composer, if the
    channel has only one composer; otherwise returns None.
    
      >>> class channel:
      ...     composers = {'sms': object()}
      >>> has_single_format(channel) == 'sms'
      True

      >>> channel.composers = {}
      >>> has_single_format(channel) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      AssertionError...

      >>> channel.composers = {'sms': None, 'email': None}
      >>> has_single_format(channel) is None
      True
    """
    composers = channel.composers.keys()
    assert len(composers) >= 1

    if len(composers) == 1:
        return composers[0]

class SimpleSubscription(persistent.Persistent):
    """
      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(interfaces.ISubscription, SimpleSubscription)
      True
    """
    interface.implements(interfaces.ISubscription)

    def __init__(self, channel, secret,
                 composer_data, collector_data, metadata):
        self.channel = channel
        self.secret = secret

        self.composer_data = persistent.dict.PersistentDict()
        self.collector_data = persistent.dict.PersistentDict()
        self.metadata = persistent.dict.PersistentDict()
        self.composer_data.update(composer_data)
        self.collector_data.update(collector_data)
        self.metadata.update(metadata)

    def __repr__(self):
        def dict_format(data):
            return pprint.pformat(dict(data)).replace('\n', '')

        data = dict(channel=self.channel)
        for attr in ('composer_data', 'collector_data', 'metadata'):
            data[attr] = dict_format(getattr(self, attr))

        fmt_str = "<SimpleSubscription to %(channel)r with composerdata: %(composer_data)s, collectordata: %(collector_data)s, and metadata: %(metadata)s>"
        return fmt_str % data

class ISubscriptionCatalogData(interface.Interface):
    """Extract metadata from subscription for use in catalog.
    """
    format = interface.Attribute(u"Format")
    key = interface.Attribute(u"Key")
    label = interface.Attribute(u"Label")

@interface.implementer(ISubscriptionCatalogData)
@component.adapter(interfaces.ISubscription)
def catalog_data(subscription):
    class Metadata(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    metadata = subscription.metadata
    composer_data = subscription.composer_data
    cschema = subscription.channel.composers[metadata['format']].schema

    def _find_field(schema, interface):
        for name in schema:
            if interface.providedBy(cschema[name]):
                return cschema[name]
        else:
            return cschema[cschema.names()[0]]

    key_field = _find_field(cschema, interfaces.ISubscriptionKey)
    label_field = _find_field(cschema, interfaces.ISubscriptionLabel)

    return Metadata(format=metadata['format'],
                    key=composer_data[key_field.__name__],
                    label=composer_data[label_field.__name__])

class SubscriptionSearchableText(object):
    component.adapts(interfaces.ISubscription)
    interface.implements(zope.index.text.interfaces.ISearchableText)

    def __init__(self, subscription):
        self.subscription = subscription

    def getSearchableText(self):
        return u' '.join(
            unicode(v) for v in self.subscription.composer_data.values())

class Subscriptions(zope.app.container.btree.BTreeContainer):
    """An ISubscriptions implementation that's based on ZODB and uses
    a zope.app.catalog Catalog to provide the query interface.

      >>> from zope.interface.verify import verifyObject
      >>> verifyObject(interfaces.ISubscriptions, Subscriptions())
      True
    """
    interface.implements(interfaces.ISubscriptions)

    subscription_factory = SimpleSubscription

    def __init__(self):
        super(Subscriptions, self).__init__()
        self._catalog = zope.app.catalog.catalog.Catalog()

        fulltext = zope.app.catalog.text.TextIndex(
            interface=zope.index.text.interfaces.ISearchableText,
            field_name='getSearchableText',
            field_callable=True)

        secret = zope.app.catalog.field.FieldIndex(
            interface=interfaces.ISubscription,
            field_name='secret',
            )

        format = zope.app.catalog.field.FieldIndex(
            interface=ISubscriptionCatalogData,
            field_name='format',
            )

        key = zope.app.catalog.field.FieldIndex(
            interface=ISubscriptionCatalogData,
            field_name='key',
            )

        label = zope.app.catalog.text.TextIndex(
            interface=ISubscriptionCatalogData,
            field_name='label',
            )

        self._catalog[u'fulltext'] = fulltext
        self._catalog[u'secret'] = secret
        self._catalog[u'format'] = format
        self._catalog[u'key'] = key
        self._catalog[u'label'] = label

    def query(self, **kwargs):
        query = {}
        for key, value in kwargs.items():
            index = self._catalog[key]
            if isinstance(index, zope.app.catalog.field.FieldIndex):
                value = (value, value)
            query[key] = value
        return self._catalog.searchResults(**query)

    def add_subscription(
        self, channel, secret, composerd, collectord, metadata):
        subscription = self.subscription_factory(
            channel, secret, composerd, collectord, metadata)

        data = ISubscriptionCatalogData(subscription)
        contained_name = u'%s-%s' % (data.key, data.format)
        if contained_name in self:
            raise ValueError(_("There's already a subscription for ${name}",
                               mapping=dict(name=contained_name)))
        self[contained_name] = subscription
        return self[contained_name]

    def remove_subscription(self, subscription):
        data = ISubscriptionCatalogData(subscription)
        del self[u'%s-%s' % (data.key, data.format)]

def subscriptions_data(channel):
    """ Get the actual subscriptions of a channel,
    in case the 'subscriptions' attribute is a property decorated
    function."""
    if hasattr(channel, '_subscriptions'):
        return channel._subscriptions
    return channel.subscriptions

def _catalog_subscription(subscription):
    intids = component.getUtility(zope.app.intid.interfaces.IIntIds)
    subscriptions_data(subscription.channel)._catalog.index_doc(
        intids.getId(subscription), subscription)

@component.adapter(collective.singing.interfaces.ISubscription,
                   zope.app.container.interfaces.IObjectAddedEvent)
def subscription_added(obj, event):
    intids = component.getUtility(zope.app.intid.interfaces.IIntIds)
    intids.register(obj)
    _catalog_subscription(obj)

@component.adapter(collective.singing.interfaces.ISubscription,
                   zope.lifecycleevent.IObjectModifiedEvent)
def subscription_modified(obj, event):
    _catalog_subscription(obj)

@component.adapter(collective.singing.interfaces.ISubscription,
                   zope.app.intid.interfaces.IIntIdRemovedEvent)
def subscription_removed(obj, event):
    intids = component.getUtility(zope.app.intid.interfaces.IIntIds)
    subscriptions_data(obj.channel)._catalog.unindex_doc(intids.getId(obj))
