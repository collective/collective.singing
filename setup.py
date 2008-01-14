from setuptools import setup, find_packages

version = '0.1'

setup(name='collective.singing',
      version=version,
      description="",
      long_description="""\
""",

      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Plone Foundation',
      author_email='',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,

      # If the dependency to z3c.form gives you trouble within a Zope
      # 2 environment, try the `fakezope2eggs` recipe
      install_requires=[
          'setuptools',
          'z3c.form==1.7.1dev',
      ],
      dependency_links=[
          'http://svn.zope.de/zope.org/z3c.form/trunk#egg=z3c.form-1.7.1dev',
      ],
      
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
