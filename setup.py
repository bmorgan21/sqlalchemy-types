from distutils.core import setup

setup(
    name='SQLAlchemyTypes',
    packages=['sqlalchemy_types'],
    version='0.2.2',
    description='More detailed types for model definitions.',
    author='Brian S Morgan',
    author_email='brian.s.morgan@gmail.com',
    url='https://github.com/bmorgan21/sqlalchemy-types',
    install_requires=[
        'SQLAlchemy>=1.0.8',
        'validation21>=0.2.1'
    ]
)
