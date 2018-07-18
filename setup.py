import os
from setuptools import setup, find_packages
import sys


sys.path.insert(0, os.path.abspath('lib'))

exec(open('src/kubernetes_validate/version.py').read())

setup(
    name='kubernetes-validate',
    version=__version__,
    description=('validates kubernetes resource definitions against schemas'),
    keywords='kubernetes, schema, validate, validator',
    author='Will Thames',
    url='https://github.com/willthames/kubernetes-validate',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        '': ['kubernetes-json-schema/*-local/*.json', 'kubernetes-json-schema/*-local-strict/*.json']
    },
    zip_safe=False,
    install_requires=['PyYAML', 'jsonschema'],
    entry_points={
        'console_scripts': [
             'kubernetes-validate=kubernetes_validate.__main__:main'
        ]
    },
    license='Apache',
    test_suite="test"
)
