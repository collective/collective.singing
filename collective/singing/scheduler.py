import datetime
import logging
import json
import sets
import persistent
import urllib2

from zope import interface
from zope import component
from zope.deprecation.deprecation import deprecate
from Products.CMFCore.Expression import Expression, getExprContext
from DateTime import DateTime

from collective.singing import interfaces
from collective.singing import MessageFactory as _
from collective.singing import subscribe
from utils import date_hook

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
        return composer.render(subscription, zip(transformed_items, raw_items),
                               override_vars)

    def __call__(self, request, items=(), use_collector=True,
                 override_vars=None):
        if override_vars is None:
            override_vars = {}
        queued_messages = 0
        # if the channel use external subscriptions, get the list
        # from script and generate the subscription object list
        subscriptions_list = self.channel.subscriptions.values()
        if getattr(self.channel, 'external_subscriptions_path', '') and \
                self.channel.external_subscriptions_path:

            #external_subscriptions_string = \
            #    '{"pine": ' \
            #    '[{"email": "ivan.teoh@gmail.com", '\
            #    '"secret": "secret", ' \
            #    '"selected_collectors": ["Newsletter Content (newsletter-content)"], '\
            #   '"metadata": {"date": "2012-10-28T21:36:57.799Z", "format": "html"} }]}'
            # new format
            # '[{"secret": "wXQwBI5xVRqIPNw2VYL0NfrRtfVpS4DXTfyLXlj6Ahfea3sUqL", 
            # "creationDate": {"<datetime>": true, "datetime": "2014-06-20T12:56:13-04:00"}, 
            # "emailAddress": "iva@mail.com", 
            # "section": ["news", "publications", "forums"]},
            expression = Expression(self.channel.external_subscriptions_path)
            expression_context = getExprContext(self.channel, self.channel)
            val = expression(expression_context)
            response = urllib2.urlopen(val)
            external_subscriptions_string = response.read()
            print external_subscriptions_string

            channel_fields = json.loads(external_subscriptions_string, object_hook=date_hook)
            subscriptions_list = []

            #if self.channel.id not in external_subscriptions_objects:
            #    return queued_messages
            optional_collectors = self.channel.collectors[self.channel.collector.id].get_optional_collectors()
            collectors_dict_title = {}
            collectors_dict_id = {}
            for optional_collector in optional_collectors:
                collectors_dict_title[optional_collector.title] = optional_collector
                collectors_dict_id[optional_collector.id] = optional_collector

            #channel_fields = external_subscriptions_objects[self.channel.id]
            for channel_field in channel_fields:

                if 'secret' not in channel_field:
                    continue
                secret = channel_field['secret']

                if 'emailAddress' not in channel_field:
                    continue
                composer_data = dict([('email', channel_field['emailAddress'])])

                if 'externalComposer' in channel_field:
                    for k, v in channel_field['externalComposer'].items():
                        composer_data[k] = v

                if 'section' not in channel_field:
                    continue
                sections_data = channel_field['section']
                new_section_data = []
                for section_data in sections_data:
                    if section_data.split(' ')[-1][1] == '(' and section_data.split(' ')[-1][-1] == ')':
                        # use id
                        # check if title (id)
                        section_id = section_data.split(' ')[-1][1:-1]
                        if section_id in collectors_dict_id:
                            new_section_data.append(collectors_dict_id[section_id])
                    else:
                        # use title
                        # section data format is "title"
                        if section_data in collectors_dict_title:
                            new_section_data.append(collectors_dict_title[section_data])
                collector_data = dict([('selected_collectors', sets.Set(new_section_data))])

                if 'creationDate' not in channel_field:
                    continue
                # getting metadata from script too
                # pending: is False after email confirmation
                # cue:
                # date: creation date
                # format: html plaintext
                # languages:
                # metadata['date].tzinfo to get timezone info
                metadata = {}
                if isinstance(channel_field['creationDate'], DateTime):
                    metadata['date'] = channel_field['creationDate'].asdatetime()
                else:
                    metadata['date'] = datetime.datetime.now()
                
                metadata['format'] = 'html'

                logger.info('ExternalSubscription: (%s, %s, %s, %s)' % (secret, composer_data, collector_data, metadata))

                subscription = subscribe.ExternalSubscription(
                    self.channel, secret, composer_data, collector_data, metadata)
                subscriptions_list.append(subscription)

        for subscription in subscriptions_list:
            logger.debug("Rendering message for %r." % subscription)
            message = self.render_message(
                request, subscription, items, use_collector, override_vars)
            if message is not None:
                queued_messages += 1
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

Trigging a manual scheduler (with no delta) always sets it's
triggered_last to now.

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

    def __cmp__(self, other):
        """ Don't ask me the exact reason why, but sometimes
        equality between schedulers does not work with only
        __eq__ defined.
        This issue has only been observed under python2.6, and
        is seems to depend on argument order. """
        if not interfaces.IScheduler.providedBy(other):
            return 1
        return cmp(self.delta, other.delta)


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
                        count += assembler(request,
                                           override_vars=override_vars)
        return count

    def __eq__(self, other):
        return isinstance(other, TimedScheduler)

    def __ne__(self, other):
        return not self == other

schedulers = (WeeklyScheduler, DailyScheduler, ManualScheduler, TimedScheduler)
