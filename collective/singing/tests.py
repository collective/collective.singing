import unittest
from zope.testing import doctest
from zope.component import testing

from collective.singing import subscribe
import queue
from zc.queue.tests import ConflictResolvingMappingStorage
count = 0
root = None


def setUp(test):
    testing.setUp(test)

    # Register adapters and handlers:
    # This query interface relies on a zope.app.catalog to
    # do the job.  Before we can use this catalog, we'll need to register an
    # IIntIds utility and wire in a couple of adatpers defined in the
    # subscribe module.  This is what 'create_subscriptions' does for us:
    from zope.component import provideUtility, provideAdapter, provideHandler
    for adapter in (subscribe.catalog_data,
                    subscribe.SubscriptionSearchableText):
        provideAdapter(adapter)

    from zope.component.event import objectEventNotify
    for handler in (subscribe.subscription_modified,
                    subscribe.subscription_removed,
                    objectEventNotify):
        provideHandler(handler)

    # Set up an IIntIds utility:
    try:
        from zope.intid import IntIds
        from zope.intid.interfaces import IIntIds
        IntIds, IIntIds  # pyflakes
    except ImportError:
        # BBB Plone 4.0 and earlier.
        from zope.app.intid import IntIds
        from zope.app.intid.interfaces import IIntIds
    intids = IntIds()
    provideUtility(intids, IIntIds)

    # We'll register a slight variation of the subscription_added
    # handler that commits the transaction, so that a later lookup of
    # IKeyReference for our subscription will work:
    from ZODB.DemoStorage import DemoStorage
    from ZODB import DB
    global root
    db = DB(DemoStorage())
    root = db.open().root()

    subscription_added.__component_adapts__ = (
        subscribe.subscription_added.__component_adapts__)
    provideHandler(subscription_added)

    # As a last step, we'll register the IKeyReference adapter for all
    # persistent objects:
    from zope.keyreference.persistent import KeyReferenceToPersistent
    from persistent.interfaces import IPersistent
    provideAdapter(KeyReferenceToPersistent, adapts=(IPersistent,))

    provideAdapter(subscribe.get_subscription_label)
    provideAdapter(subscribe.get_subscription_key)

def subscription_added(obj, event):
    global count
    count += 1
    root[str(count)] = obj
    from transaction import commit; commit()
    subscribe.subscription_added(obj, event)

def test_suite():
    return unittest.TestSuite([

        doctest.DocFileSuite('README.txt'),

        doctest.DocFileSuite(
            'async.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
        ),

        doctest.DocFileSuite(
            'collector.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
        ),

        doctest.DocFileSuite(
           'message.txt',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocFileSuite(
            'scheduler.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
        ),

        doctest.DocFileSuite(
            'subscribe.txt',
            setUp=setUp, tearDown=testing.tearDown,
        ),

        doctest.DocFileSuite(
            'browser/converters.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
        ),

        doctest.DocFileSuite(
            'queue.txt',
            globs={'Queue':lambda: queue.CompositeQueue(2)}
        ),

       doctest.DocTestSuite(
           'collective.singing.mail',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocTestSuite(
           'collective.singing.subscribe',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocTestSuite(
           'collective.singing.scheduler',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        ])
