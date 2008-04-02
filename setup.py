from setuptools import setup, find_packages

version = '0.1'

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
      author_email='daniel.nouri@gmail.com',
      url='http://pypi.python.org/pypi/collective.singing',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,

      # If the dependency to z3c.form gives you trouble within a Zope
      # 2 environment, try the `fakezope2eggs` recipe
      install_requires=[
          'setuptools',
          'z3c.form',
          'zc.queue',
      ],
      dependency_links=[
      ],
      
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
