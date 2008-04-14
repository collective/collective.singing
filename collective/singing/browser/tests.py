import unittest
from zope.testing import doctest

from zope import component
import zope.traversing.adapters
import zope.traversing.namespace
from zope.component import testing
import zope.publisher.interfaces.browser
import z3c.form.testing

from collective.singing import subscribe
from collective.singing.browser import macros

def setup_defaults():
    # Set up z3c.form defaults
    z3c.form.testing.setupFormDefaults()
    
    # Make traversal work; register both the default traversable
    # adapter and the ++view++ namespace adapter
    component.provideAdapter(
        zope.traversing.adapters.DefaultTraversable, [None])
    component.provideAdapter(
        zope.traversing.namespace.view, (None, None), name='view')

    # Setup singing macros
    component.provideAdapter(
        macros.Macros,
        (None, None),
        zope.publisher.interfaces.browser.IBrowserView,
        name='singing-macros')

def test_suite():
    return unittest.TestSuite([

        doctest.DocFileSuite(
           'crud.txt',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocFileSuite(
           'wizard.txt',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocFileSuite(
           'subscribe.txt',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocTestSuite(
           'collective.singing.browser.subscribe',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocTestSuite(
           'collective.singing.browser.crud',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),
        ])
