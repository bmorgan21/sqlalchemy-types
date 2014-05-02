from distutils.core import setup

setup(
    name='SQLAlchemyTypes',
    version='0.1.0',
    author='Brian S Morgan',
    author_email='brian.s.morgan@gmail.com',
    packages=['sqlalchemy_types'],
    url='https://github.com/bmorgan21/sqlalchemy-types',
    description='More detailed types for model definitions.',
    install_requires=[
        'validation>=0.1.0'
    ]
)
