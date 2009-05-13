import datetime
import logging

import persistent

from zope import interface
from zope import component
from zope.deprecation.deprecation import deprecate

from collective.singing import interfaces
from collective.singing import MessageFactory as _

from plone.memoize import request

logger = logging.getLogger('collective.singing')

class UnicodeFormatter(object):
    interface.implements(interfaces.IFormatItem)

    def __init__(self, item, request):
        self.item = item

    def __call__(self):
        return unicode(self.item)

@request.cache(get_key=lambda fun, obj, req, format: (obj, format))
def format_item(obj, request, format):
    logger.info('Formatting item: (%s, %s, %s)' % (obj, request, format))
    return getIFormatAdapter(obj, request, format)()

def getIFormatAdapter(obj, request, format):
    """Return item formatter for the specified format.

    If a formatter for the specified format is not found, an
    attempt to look up an unspecified formatter is made.
    """
    
    formatter = component.queryMultiAdapter(
        (obj, request), interfaces.IFormatItem, name=format)

    if formatter is not None:
        return formatter

    return component.getMultiAdapter((obj, request), interfaces.IFormatItem)

class MessageAssemble(object):
    interface.implements(interfaces.IMessageAssemble)
    component.adapts(interfaces.IChannel)

    use_cue = True
    update_cue = True

    def __init__(self, channel):
        self.channel = channel

    def render_message(self, request, subscription,
                       items=(), use_collector=True, override_vars=None):
        channel = self.channel
        collector = channel.collector
        composers = channel.composers
        if override_vars is None:
            override_vars = {}

        subscription_metadata = subscription.metadata
        if subscription_metadata.get('pending'):
            return None

        # Collect items for subscription
        if collector is not None and use_collector:

            # Optionally use and set cue
            if self.use_cue:
                use_cue = subscription_metadata.get(
                    'cue', subscription_metadata.get('date'))
            else:
                use_cue = None

            collector_items, cue = collector.get_items(use_cue, subscription)
            if self.update_cue:
                subscription_metadata['cue'] = cue

            # If there was a collector but no items, we'll skip
            # this subscription:
            if not items and len(collector_items) == 0:
                return None
        else:
            # If there's no collector, we go on with an empty
            # items list:
            collector_items = ()

        raw_items = tuple(items) + tuple(collector_items)

        # First format all items...
        format = subscription_metadata['format']
        formatted_items = [format_item(item, request, format)
                           for item in raw_items]

        # ... then transform them ...
        transformed_items = []
        for formatted_item, raw_item in zip(formatted_items, raw_items):
            for name, transform in component.getAdapters(
                (raw_item,), interfaces.ITransform):
                formatted_item = transform(formatted_item, subscription)
            transformed_items.append(formatted_item)

        # ... and finally render using the right composer. Note
        # that the message is already queued when we render it.
        composer = composers[format]
        return composer.render(subscription, zip(transformed_items, raw_items), override_vars)

    def __call__(self, request, items=(), use_collector=True, override_vars=None):
        if override_vars is None:
            override_vars = {}
        queued_messages = 0
        for subscription in self.channel.subscriptions.values():
            logger.debug("Rendering message for %r." % subscription)
            message = self.render_message(
                request, subscription, items, use_collector, override_vars)
            if message is not None:
                queued_messages +=1
        return queued_messages


@deprecate("""\
render_message has become IMessageAssemble.render_message in version
0.6.  Please update your code to use the IMessageAssemble adapter on
IChannel instead.
""")
def render_message(channel, request, subscription, items, use_collector):
    return interfaces.IMessageAssemble(channel).render_message(
        request, subscription, items, use_collector)

@deprecate("""\
assemble_messages has become IMessageAssemble.__call__ in version 0.6.
Please update your code to use the IMessageAssemble adapter on
IChannel instead.
""")
def assemble_messages(channel, request, items=(), use_collector=True):
    return interfaces.IMessageAssemble(channel)(request, items, use_collector)

class AbstractPeriodicScheduler(object):

    """
      >>> from datetime import datetime, date, time, timedelta

      >>> class TestScheduler(AbstractPeriodicScheduler):
      ...     @property
      ...     def now(self):
      ...         return self._now
      ...     def assemble_messages(self, channel, request):
      ...         return self.triggered_last

      >>> def reset(scheduler):
      ...     scheduler.active = True
      ...     scheduler.delta = timedelta(days=7)
      ...     scheduler.triggered_last = datetime(2009, 3, 1, 17, 0)

      >>> scheduler = TestScheduler()
      >>> reset(scheduler)

Delta not reached, triggered_last stays the same.

      >>> last = scheduler.triggered_last
      >>> scheduler._now = datetime(2009, 3, 1, 17, 15)
      >>> scheduler.tick(None, None)
      >>> last == scheduler.triggered_last
      True
      
      >>> scheduler._now = datetime(2009, 3, 4, 17, 0)
      >>> scheduler.tick(None, None)
      >>> last == scheduler.triggered_last
      True

      >>> scheduler._now = datetime(2009, 3, 8, 16, 59)
      >>> scheduler.tick(None, None)
      >>> last == scheduler.triggered_last
      True

Delta reached.

      >>> scheduler._now = datetime(2009, 3, 8, 17, 15)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 8, 17, 0)

      >>> reset(scheduler)
      >>> scheduler._now = datetime(2009, 3, 8, 17, 0)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 8, 17, 0)

Only the date changes when sending.

      >>> reset(scheduler)
      >>> scheduler._now = datetime(2009, 3, 9, 18, 15)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 8, 17, 0)

      >>> reset(scheduler)
      >>> scheduler._now = datetime(2009, 3, 12, 18, 15)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 8, 17, 0)

If last call is more the delta ago, the interveening sends will
of course  be skipped.

      >>> reset(scheduler)
      >>> scheduler._now = datetime(2009, 3, 26, 18, 15)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 22, 17, 0)

Trigging a manual scheduler (with no delta) always sets it's triggered_last to now.

      >>> reset(scheduler)
      >>> scheduler.delta = timedelta()
      >>> scheduler._now = datetime(2009, 3, 26, 18, 15)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 26, 18, 15)
      
      >>> scheduler._now = datetime(2009, 3, 26, 18, 16)
      >>> scheduler.tick(None, None)
      datetime.datetime(2009, 3, 26, 18, 16)

    """
    interface.implements(interfaces.IScheduler)

    triggered_last = datetime.datetime(1970, 1, 1)
    active = False
    delta = None

    def tick(self, channel, request):
        if self.active and (self.now - self.triggered_last >= self.delta):
            return self.trigger(channel, request)

    @property
    def now(self):
        return datetime.datetime.now()

    def trigger(self, channel, request):
        now = self.now
        
        if self.delta:
            # triggered_last will be set in steps of delta
            while now - self.triggered_last >= self.delta:
                self.triggered_last = self.triggered_last + self.delta
        else:
            self.triggered_last = now
        
        return self.assemble_messages(channel, request)

    def assemble_messages(self, channel, request):
        return interfaces.IMessageAssemble(channel)(request)        

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

class ManualScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Manual scheduler")
    delta = datetime.timedelta()

    def tick(self, channel, request):
        pass

class TimedScheduler(persistent.Persistent, AbstractPeriodicScheduler):
    title = _(u"Timed scheduler")
    active = True
    triggered_last = datetime.datetime(1970, 1, 1)

    def __init__(self):
        super(TimedScheduler, self).__init__()
        self.items = persistent.list.PersistentList()

    def tick(self, channel, request):
        return self.trigger(channel, request, manual=False)

    def trigger(self, channel, request, manual=True):
        count = 0
        now = datetime.datetime.now()
        assembler = interfaces.IMessageAssemble(channel)
        if self.active or manual:
            self.triggered_last = now
            for when, content, override_vars in tuple(self.items):
                if manual or when < now:
                    self.items.remove((when, content, override_vars))
                    if content is not None:
                        count += assembler(request, (content(),),
                                           override_vars=override_vars)
                    else:
                        count += assembler(request, override_vars=override_vars)
        return count

    def __eq__(self, other):
        return isinstance(other, TimedScheduler)

    def __ne__(self, other):
        return not self == other

schedulers = (WeeklyScheduler, DailyScheduler, ManualScheduler, TimedScheduler)
