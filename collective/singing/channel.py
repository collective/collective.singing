from zope import component
from interfaces import IChannelLookup

def channel_lookup():
    """Lookup all channels.

    This method looks up all ``IChannelLookup`` utilities and returns
    a combined list of available channels.
    """
    
    channels = []
    
    for utility in component.getAllUtilitiesRegisteredFor(IChannelLookup):
        result = utility()
        channels.extend(result)

    return channels

