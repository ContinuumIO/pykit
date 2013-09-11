# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import sys
from distutils.core import setup, Extension

if sys.version_info[:2] < (2, 6):
    raise Exception('pykit requires Python 2.6 or greater.')

from setup_helpers import find_packages, run_2to3, setup_args

exclude_packages = ()
cmdclass = {}

if sys.version_info[0] >= 3:
    run_2to3(cmdclass)

#===------------------------------------------------------------------===
# setup
#===------------------------------------------------------------------===

setup(
    name="pykit",
    version='0.1',
    author="Continuum Analytics, Inc.",
    license="BSD",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Utilities",
        ],
    description="IR optimizer and lowerer",
    packages=find_packages(exclude=exclude_packages),
    package_data={
        '': ['*.md', '*.cfg'],
        'pykit': ['*.txt'],
        'pykit.ir': ['*.h'],
        },
    ext_modules=[],
    cmdclass=cmdclass,
    **setup_args
)
