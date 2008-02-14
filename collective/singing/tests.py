import unittest
from zope.testing import doctest
from zope.component import testing
from zope import component
from zope import interface

def create_eventlog(event=interface.Interface):
    value = []
    @component.adapter(event)
    def log(event):
        value.append(event)
    component.provideHandler(log)
    return value

def test_suite():
    return unittest.TestSuite([

        doctest.DocFileSuite('README.txt'),

        doctest.DocFileSuite(
           'message.txt',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocFileSuite(
            'scheduler.txt',
            setUp=testing.setUp, tearDown=testing.tearDown,
        ),

        doctest.DocTestSuite(
           'collective.singing.mail',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        doctest.DocTestSuite(
           'collective.singing.mail',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),

        ])
