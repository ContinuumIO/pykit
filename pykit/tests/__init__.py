# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
import collections

from pykit import from_c, environment, types, pipeline
from pykit.ir import *
from pykit.analysis import cfa
from pykit.utils import *

# ______________________________________________________________________

State = collections.namedtuple('State', 'm f b entry env')

def pykitcompile(source, funcname=None, cfanalyze=True):
    m = from_c(source)
    verify(m)
    if cfanalyze:
        for function in m.functions.values():
            cfa.run(function)
            verify(function)
        verify(m)

    if len(m.functions) == 1:
        funcname, = m.functions

    if funcname:
        f = m.get_function(funcname)
        b = Builder(f)
        entry = f.startblock
    else:
        f, b, entry = None, None, None

    env = environment.fresh_env()
    return State(m, f, b, entry, env)

# ______________________________________________________________________

class SourceTestCase(unittest.TestCase):

    source = None
    funcname = None
    cfa = True

    def setUp(self):
        self.state = pykitcompile(self.source, self.funcname, self.cfa)
        self.m, self.f, self.b, self.entry, self.env = self.state
        self.eq = self.assertEqual


class TestFunction(object):

    def __init__(self, source, **substitutions):
        source = "#include <pykit_ir.h>\n" + source
        for name, value in substitutions.iteritems():
            if isinstance(value, types.Type):
                substitutions[name] = types.typename(value)
        source = substitute(source, **substitutions)
        self.state = pykitcompile(source)
        self.m, self.f, self.b, self.entry, self.env = self.state

    def convert_args(self, args):
        return [types.convert(arg, argtype)
                    for arg, argtype in zip(args, self.f.type.argtypes)]

    def run(self, codegen, *args):
        state = self.state

        ### Compile
        codegen.install(state.env)
        lfunc, env = pipeline.codegen(state.f, state.env)
        # print(lfunc)
        codegen.verify(lfunc, state.env)
        codegen.optimize(lfunc, state.env)

        ### Run
        return codegen.execute(lfunc, state.env, *self.convert_args(args))

    def interp(self, *args):
        from pykit.ir import interp
        return interp.run(self.f, self.env, args=self.convert_args(args))

# ______________________________________________________________________

def mark_test(f, argtuples=None, suite=None):
    """Mark a function-based set as a test"""
    suite = suite or unittest.TestSuite()
    for argstuple in argtuples:
        def partial_f(argstuple=argstuple):
            return f(*argstuple)
        partial_f.__name__ = '%s[%s]' % (f.__name__, argstuple)
        suite.addTest(unittest.FunctionTestCase(partial_f))
    return suite

def parametrize(argtuples):
    """Create a suite containing parameterized function test cases."""
    def decorator(f):
        if 'load_tests' not in f.func_globals:
            def load_tests(*args):
                return suite
            f.func_globals['load_tests'] = load_tests
            f.func_globals['__suite'] = unittest.TestSuite()
        suite = f.func_globals['__suite']
        mark_test(f, argtuples, suite)
        return f
    return decorator