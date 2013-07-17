# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from pykit.tests import *
from pykit import types, environment, pipeline

try:
    import llvm.core
except ImportError, e:
    llvm_codegen = None
else:
    from pykit.codegen import llvm as llvm_codegen

class TestCodegen(SourceTestCase):

    source = """
        float plus(float a) {
            return (float) add(a, a);
        }
    """

    def setparam(self, param):
        self.name, self.codegen = param # llvm, ...

    def setUp(self):
        super(TestCodegen, self).setUp()
        getattr(self, 'setup_' + self.name)()

    def setup_llvm(self):
        environment.install_llvm_codegen(self.env)
        llvm_codegen.init(self.f, self.env)

    def test_codegen(self):
        lfunc = self.codegen.run(self.f, self.env)
        self.codegen.verify(lfunc, self.env)
        self.codegen.optimize(lfunc, self.env)
        result = self.codegen.execute(lfunc, self.env, 2.0)
        self.eq(result, 4.0)


def load_tests(*args):
    return parametrize(TestCodegen, ('llvm', llvm_codegen))