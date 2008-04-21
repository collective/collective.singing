import unittest
from zope.testing import doctest

from zope.component import testing
import z3c.form.testing
import plone.z3cform.tests

from collective.singing import subscribe


def setup_defaults():
    # Set up z3c.form defaults
    z3c.form.testing.setupFormDefaults()

    # And plone.z3cform
    plone.z3cform.tests.setup_defaults()

def test_suite():
    return unittest.TestSuite([

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

        ])
