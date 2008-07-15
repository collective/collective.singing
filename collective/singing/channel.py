from zope import component
from interfaces import IChannelLookup

def channel_lookup(only_subscribeable=False):
    """Lookup all channels.

    This method looks up all ``IChannelLookup`` utilities and returns
    a combined list of available channels.
    """
    
    channels = []
    
    for utility in component.getAllUtilitiesRegisteredFor(IChannelLookup):
        result = utility()
        channels.extend(result)

    if only_subscribeable:
        return [c for c in channels if c.subscribeable]
    return channels

def lookup(name):
    for channel in channel_lookup():
        if channel.name == name:
            return channel

    raise ValueError('Unable to lookup channel with name "%s".' % name)

