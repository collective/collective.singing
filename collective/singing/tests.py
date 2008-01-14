import unittest
from zope.testing import doctest

from zope.component import testing

def test_suite():
    return unittest.TestSuite([

        doctest.DocFileSuite(
           'README.txt'),

        doctest.DocTestSuite(
           'collective.singing.mail',
           setUp=testing.setUp, tearDown=testing.tearDown,
           ),
        ])
