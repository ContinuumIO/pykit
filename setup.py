# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import os
import sys
from fnmatch import fnmatchcase
from distutils.util import convert_path

# Do not EVER use setuptools, it makes cythonization fail
# Distribute fixes that
from distutils.core import setup, Extension

if sys.version_info[:2] < (2, 6):
    raise Exception('pykit requires Python 2.6 or greater.')

import pykit

#===------------------------------------------------------------------===
# Setup constants and arguments
#===------------------------------------------------------------------===

setup_args = {
    'long_description': open('README.md').read(),
}

root = os.path.dirname(os.path.abspath(__file__))
exclude_packages = ()
cmdclass = {}

#===------------------------------------------------------------------===
# Package finding
#===------------------------------------------------------------------===

def find_packages(where='.', exclude=()):
    out = []
    stack=[(convert_path(where), '')]
    while stack:
        where, prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if ('.' not in name and os.path.isdir(fn) and
                    os.path.isfile(os.path.join(fn, '__init__.py'))
            ):
                out.append(prefix+name)
                stack.append((fn, prefix+name+'.'))

    if sys.version_info[0] == 3:
        exclude = exclude + ('*py2only*', )

    for pat in list(exclude) + ['ez_setup', 'distribute_setup']:
        out = [item for item in out if not fnmatchcase(item, pat)]

    return out

#===------------------------------------------------------------------===
# 2to3
#===------------------------------------------------------------------===

def run_2to3():
    import lib2to3.refactor
    from distutils.command.build_py import build_py_2to3 as build_py
    print("Installing 2to3 fixers")
    # need to convert sources to Py3 on installation
    fixes = 'dict imports imports2 unicode ' \
            'xrange itertools itertools_imports long types'.split()
    fixes = ['lib2to3.fixes.fix_' + fix for fix in fixes]
    build_py.fixer_names = fixes
    cmdclass["build_py"] = build_py

if sys.version_info[0] >= 3:
    run_2to3()

#===------------------------------------------------------------------===
# setup
#===------------------------------------------------------------------===

setup(
    name="llvmmath",
    version=pykit.__version__,
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
        "Topic :: Utilities",
        ],
    description="IR optimizer and lowerer",
    packages=find_packages(exclude=exclude_packages),
    package_data={
        '': ['*.md', '*.cfg'],
        'pykit': ['*.txt'],
        },
    ext_modules=[],
    cmdclass=cmdclass,
    **setup_args
)