from setuptools import setup, find_packages

version = '0.3'

setup(name='collective.singing',
      version=version,
      description="A Zope library for sending notifications and newsletters",
      long_description="""\
""",

      classifiers=[
        "Framework :: Plone",
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
          'zope.app.catalog',
          'zc.queue',
          'zc.lockfile',
          'plone.z3cform',
      ],
      dependency_links=[
      ],
      
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
