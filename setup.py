# -*- coding: utf-8 -*-
"""
documentation
"""

from setuptools import setup, find_packages


setup(
    name='tunable',
    version='0.0.1.dev6',
    description='tunable manager',
    long_description='A little library allowing to set parameters. Please see https://github.com/csachs/tunable for more information.',
    author='Christian C. Sachs',
    author_email='sachs.christian@gmail.com',
    url='https://github.com/csachs/tunable',
    install_requires=['pyasn1', 'pyyaml'],
    packages=find_packages(),
    data_files=[('asn1schema', ['tunable/schema/tunable_schema.asn'])],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)
