import datetime

import persistent
from zope import interface
from zope import component

from collective.singing import interfaces
from collective.singing import MessageFactory as _

class UnicodeFormatter(object):
    interface.implements(interfaces.IFormatItem)

    def __init__(self, item):
        self.item = item

    def __call__(self):
        return unicode(self.item)

def getIFormatAdapter(obj, format):
    format = component.queryAdapter(
        obj, interfaces.IFormatItem, name=format)
    if format is None:
        return component.getAdapter(obj, interfaces.IFormatItem)
    else:
        return format

def assemble_messages(channel):
    collector = channel.collector
    composers = channel.composers

    queued_messages = 0
    for secret, subscriptions in channel.subscriptions.items():
        for sub in subscriptions:
            subscription_metadata = interfaces.ISubscriptionMetadata(sub)

            if subscription_metadata.get('pending'):
                continue

            # Collect items for subscription
            if collector is not None:
                items, cue = collector.get_items(
                    subscription_metadata.get('cue'), sub)
                subscription_metadata['cue'] = cue

                # If there was a collector but no items, we'll skip
                # this subscription:
                if len(items) == 0:
                    continue
            else:
                # If there's no collector, we go on with an empty
                # items list:
                items = ()

            # Use the right composer to render the message.  Note
            # that the message is already queued when we render it.
            format = subscription_metadata['format']
            composer = composers[format]
            items = [getIFormatAdapter(item, format)() for item in items]
            message = composer.render(sub, items)
            queued_messages +=1

    return queued_messages

class AbstractPeriodicScheduler(object):
    interface.implements(interfaces.IScheduler)

    triggered_last = datetime.datetime(1970, 1, 1)
    active = False
    delta = None

    def tick(self, channel):
        now = datetime.datetime.now()
        if self.active and (now - self.triggered_last >= self.delta):
            return self.trigger(channel)

    def trigger(self, channel):
        self.triggered_last = datetime.datetime.now()
        return assemble_messages(channel)

    def __eq__(self, other):
        return (isinstance(other, AbstractPeriodicScheduler) and
                other.delta == self.delta)

    def __ne__(self, other):
        return not self == other

class DailyScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Daily scheduler")
    delta = datetime.timedelta(days=1)

class WeeklyScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Weekly scheduler")
    delta = datetime.timedelta(weeks=1)

schedulers = (WeeklyScheduler, DailyScheduler)
