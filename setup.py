# -*- coding: utf-8 -*-
"""
documentation
"""

from setuptools import setup


setup(
    name='tunable',
    version='0.0.1',
    description='tunable manager',
    long_description='A little library allowing to set parameters.',
    author='Christian C. Sachs',
    author_email='sachs.christian@gmail.com',
    url='https://github.com/csachs/tunable',
    packages=[
        'tunable'
    ],
    #requires=['numpy', 'scipy', 'matplotlib'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)
