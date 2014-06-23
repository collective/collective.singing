import os
from setuptools import setup, find_packages

version = '0.7.2'

def read(*pathnames):
    return open(os.path.join(os.path.dirname(__file__), *pathnames)).read()

setup(name='collective.singing',
      version=version,
      description="A Zope 3 library for sending notifications and newsletters",
      long_description='\n'.join([
          read('docs', 'README.txt'),
          read('docs', 'HISTORY.txt'),
          ]),
      classifiers=[
        "Framework :: Plone",
        'Framework :: Plone :: 3.2',
        'Framework :: Plone :: 3.3',
        'Framework :: Plone :: 4.0',
        'Framework :: Plone :: 4.1',
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='zope plone notification newsletter',
      author='Daniel Nouri, Thomas Clement Mogensen and contributors',
      author_email='singing-dancing@googlegroups.com',
      url='http://pypi.python.org/pypi/collective.singing',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'setuptools',
          'zope.sendmail',
          'zope.keyreference>=3.6.2',
          'zope.app.keyreference==3.6.1',
          'zope.app.catalog',
          'zope.app.i18n',
          'zc.queue',
          'zc.lockfile',
          'plone.z3cform>=0.5.1',
          'python-dateutil>=1.5',
      ],

      entry_points="""
      # -*- Entry points: -*-
      """,
      )
