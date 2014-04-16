#!/usr/bin/env python

import os
import sys
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


_install_requires = [
    "tempman>=0.1.2,<0.2",
    "mayo>=0.2.5,<0.3",
]

if sys.version_info[:2] <= (2, 6):
    _install_requires.append("argparse>=1.1,<2.0")


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
    install_requires=_install_requires,
    keywords="deploy deployment",
)
