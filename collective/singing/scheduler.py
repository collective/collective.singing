import datetime

import persistent
from zope import interface

from collective.singing import interfaces
from collective.singing import MessageFactory as _

def assemble_messages(channel):
    collector = channel.collector
    composers = channel.composers

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
            composer = composers[subscription_metadata['format']]
            message = composer.render(sub, items)

class AbstractPeriodicScheduler(object):
    interface.implements(interfaces.IScheduler)

    triggered_last = datetime.datetime(1, 1, 1, 0, 0)
    active = False
    delta = None

    def tick(self, channel):
        now = datetime.datetime.now()
        if self.active and now - self.triggered_last >= self.delta:
            assemble_messages(channel)
            self.triggered_last = now

class DailyScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Daily scheduler")
    delta = datetime.timedelta(days=1)

class WeeklyScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Weekly scheduler")
    delta = datetime.timedelta(weeks=1)
