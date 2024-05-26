#!/usr/bin/env python3

from setuptools import setup

setup(name='bragi',
    version='0.6',
    packages=['bragi'],
    scripts=['bin/bragi'],
    install_requires=[
        'lark-parser'
    ],

    # Package metadata.
    author='The Managarm Project', # Original implementation by Kacper Słomiński.
    author_email='info@managarm.org',
    license='MIT',
    url='https://github.com/managarm/bragi'
)
