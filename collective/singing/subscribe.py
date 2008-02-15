import pprint

import persistent
import persistent.dict
import persistent.list
from zope import interface
from zope import component

from collective.singing import interfaces

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

      >>> Channel.composers = {}
      >>> has_single_composer(channel) # doctest: +ELLIPSIS
      Traceback (most recent call last):
      ...
      AssertionError...

      >>> Channel.composers = {'sms': None, 'email': None}
      >>> has_single_composer(channel) is None
      True
    """
    composers = channel.composers.keys()
    assert len(composers) >= 1

    if len(composers) == 1:
        return composers[0]

class SimpleSubscriptions(persistent.dict.PersistentDict):
    """A dict that makes sure that when you access an element that it
    doesn't have, you get a nice list back:

      >>> d = SimpleSubscriptions()
      >>> 'bar' in d
      False
      >>> d['bar']
      []
      >>> d['bar'].append('spam')
      >>> d['bar']
      ['spam']
    """
    interface.implements(interfaces.ISubscriptions)

    def __getitem__(self, key):
        if key not in self:
            self[key] = persistent.list.PersistentList()
        return super(SimpleSubscriptions, self).__getitem__(key)

class SimpleSubscription(persistent.Persistent):
    interface.implements(interfaces.ISubscription)
    
    def __init__(self, channel, secret,
                 composer_data, collector_data, metadata):
        self.channel = channel
        self.secret = secret
        self.composer_data.update(composer_data)
        self.collector_data.update(collector_data)
        self.metadata.update(metadata)

    @property
    def composer_data(self):
        return interfaces.IComposerData(self)

    @property
    def collector_data(self):
        return interfaces.ICollectorData(self)

    @property
    def metadata(self):
        return interfaces.ISubscriptionMetadata(self)
        
    def __repr__(self):
        def dict_format(data):
            return pprint.pformat(dict(data)).replace('\n', '')

        data = dict(channel=self.channel)
        for attr in ('composer_data', 'collector_data', 'metadata'):
            data[attr] = dict_format(getattr(self, attr))

        fmt_str = "<SimpleSubscription to %(channel)r with composerdata: %(composer_data)s, collectordata: %(collector_data)s, and metadata: %(metadata)s>"
        return fmt_str % data

def _data_dict(subscription, name):
    data = getattr(subscription, name, None)
    if data is None:
        data = persistent.dict.PersistentDict()
        setattr(subscription, name, data)
    return data

@interface.implementer(interfaces.IComposerData)
@component.adapter(SimpleSubscription)
def SimpleComposerData(subscription):
    return _data_dict(subscription, '_composer_data')

@interface.implementer(interfaces.ICollectorData)
@component.adapter(SimpleSubscription)
def SimpleCollectorData(subscription):
    return _data_dict(subscription, '_collector_data')

@interface.implementer(interfaces.ISubscriptionMetadata)
@component.adapter(SimpleSubscription)
def SimpleMetadata(subscription):
    return _data_dict(subscription, '_metadata')
