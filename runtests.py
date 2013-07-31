#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from os.path import abspath, dirname, join
import sys
import pykit

kwds = {}
if len(sys.argv) > 1:
    kwds["pattern"] = '*' + sys.argv[1] + '*'

root = dirname(abspath(pykit.__file__))
order = ['parsing', 'ir', 'adt', 'utils', 'analysis', 'transform', 'lower',
         'codegen', join('codegen', 'llvm')]
dirs = [join(root, pkg, 'tests') for pkg in order]
sys.exit(pykit.run_tests(dirs, **kwds))