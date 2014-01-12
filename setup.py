#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='beach',
    version='0.1.0',
    description='Deploy applications',
    long_description=read("README"),
    author='Michael Williamson',
    author_email='mike@zwobble.org',
    url='https://github.com/mwilliamson/beach',
    packages=['beach'],
    scripts=['scripts/beach'],
    install_requires=[
    ],
    keywords="deploy deployment",
)
