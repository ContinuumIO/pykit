# -*- coding: utf-8 -*-

"""
Load and define the Python C API in a Module.
"""

from __future__ import print_function, division, absolute_import
from os.path import abspath, dirname, join
import re
import collections

from pykit.types import parse_type, Function
from pykit import ir

root = dirname(abspath(__file__))

Py_Function = collections.namedtuple('Py_Function', ['name', 'signature',
                                                     'maybe', 'badval'])

def parse_capi(lines):
    """
    Parse a 'capi' file (given as a list of lines) and return a list of
    Py_Function
    """
    pattern = r'(\w+)\s+(\**)\s*(\w+)\((.*)\)' # Float32 *sin(...)
    pexcept = r'except (\??)(.*)'

    functions = []
    for line in lines:
        if line.strip():
            m = re.match(pattern, line)
            restype, stars, fname, argtypes = m.groups()
            rest = line[len(m.group(0)):].strip()
            if rest:
                maybe, badval = re.match(pexcept, rest).groups()
            else:
                maybe, badval = None, None

            restype = parse_type("%s %s" % (restype, " ".join(stars)))
            argtypes = map(parse_type, argtypes.split(','))
            signature = Function(restype, argtypes)
            functions.append(Py_Function(fname, signature, maybe, badval))

    return functions

def make_globals(py_c_api):
    """Create a module of global Python C API functions"""
    for fn in py_c_api:
        gv = ir.GlobalValue(fn.name, fn.signature, external=True)
        if gv.badval: gv.add_metadata(badval=ir.Const(gv.badval))
        if gv.maybe:  gv.add_metadata(cpy_occurred=True)
        yield fn.name, gv

py_c_api = parse_capi(open(join(root, 'capi')))
py_c_api_module = ir.Module(make_globals(py_c_api))