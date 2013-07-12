import unittest

import nose
import numpy as np


class Op(object):
    def __init__(self):
        pass


class Type(object):
    def __init__(self):
        pass

    def __call__(self):
        return Variable(self)


class Variable(object):
    def __init__(self, type, owner=None):
        self.type = type
        self.owner = owner

    def __add__(self, other):
        return Apply(Add(), [self, other], [self.type()]).outputs[0]

    def __mul__(self, other):
        assert self.type.dtype == other.type.dtype, "TODO dtype upcast"

        # Compute the output broadcast flag.
        if len(other.type.broadcastable) > len(self.type.broadcastable):
            n = len(other.type.broadcastable) - len(self.type.broadcastable)
            self_br = [True] * n + self.type.broadcastable
        else:
            self_br = self.type.broadcastable
        if len(self.type.broadcastable) > len(other.type.broadcastable):
            n = len(self.type.broadcastable) - len(other.type.broadcastable)
            other_br = [True] * n + other.type.broadcastable
        else:
            other_br = other.type.broadcastable
        assert len(other_br) == len(self_br)
        out_br = list(other_br)
        for i in range(len(other_br)):
            if not self_br[i] or not other_br[i]:
                out_br[i] = False

        outtype = TensorType(self.type.dtype, out_br)
        return Apply(Mul(), [self, other], [outtype()]).outputs[0]


class Apply(object):
    def __init__(self, op, inputs, outputs):
        self.op = op
        self.inputs = inputs
        self.outputs = outputs
        for out in outputs:
            out.owner = self


class Add(Op):
    def compute(self, a, b):
        return a + b


class Mul(Op):
    def compute(self, a, b):
        return a * b


class Dot(Op):
    def compute(self, a, b):
        return np.dot(a, b)


def dot(a, b):
    return Apply(Dot(), [a, b], [a.type()]).outputs[0]


class TensorType(Type):
    def __init__(self, dtype, broadcastable):
        self.dtype = dtype
        self.broadcastable = broadcastable


class Function(object):
    def __init__(self, inputs, outputs, updates=()):
        self.inputs = inputs
        self.outputs = outputs
        self.updates = updates

    def __call__(self, *args):
        memo = {}
        for var, arg in zip(self.inputs, args):
            memo[var] = arg

        def compute(var):
            if var not in memo:
                input_vals = map(compute, var.owner.inputs)
                memo[var] = var.owner.op.compute(*input_vals)
            return memo[var]

        return map(compute, self.outputs)


def test_theano_like_1():
    fvector = TensorType('int', [False])

    x = Variable(fvector)
    y = Variable(fvector)
    z = Variable(fvector)

    a = Apply(Mul(), [x, y], [z])
    z.owner = a

    f = Function([x, y], [z])
    xval = np.asarray([1, 2, 3])
    yval = np.asarray([4, 5, 6])
    zval = np.asarray([4, 10, 18])

    assert np.all(f(xval, yval)[0] == zval)


def test_multiple_apply():
    fvector = TensorType('int', [False])

    x = Variable(fvector)
    y = Variable(fvector)
    z = Variable(fvector)
    w = Variable(fvector)
    u = Variable(fvector)

    a0 = Apply(Mul(), [x, y], [z])
    z.owner = a0
    a1 = Apply(Add(), [z, w], [u])
    u.owner = a1

    f = Function([x, y, w], [u])
    xval = np.asarray([1, 2, 3])
    yval = np.asarray([4, 5, 6])
    wval = np.asarray([4, 10, 18])
    uval = np.asarray([8, 20, 36])

    assert np.all(f(xval, yval, wval)[0] == uval)


# TODO: test broadcasting
# TODO: test Op with multiple outputs
# TODO: test with updates

#===------------------------------------------------------------------===
# Theano -> Pykit
#===------------------------------------------------------------------===

from pykit import ir, types

def map_type(type):
    """ Theano type -> pykit type"""
    if isinstance(type, TensorType):
        # array of any order
        dtype = map_type(type.dtype)
        return types.Array(dtype, len(type.broadcastable), 'A')
    else:
        return getattr(types, type.capitalize())

def type_from_outputs(outputs):
    """
    :param outputs: [ Theano Variable ]
    :returns:       pykit return type
    """
    result_types = [map_type(v.type) for v in outputs]
    if len(outputs) > 1:
        result_type = types.Tuple(result_types)
    else:
        result_type, = result_types

    return result_type

listify = lambda x: x if isinstance(x, list) else [x]

class Codegen(object):
    """ Theano expression DAG -> pykit IR """

    def __init__(self, function):
        self.theano = function

        argnames = ["arg%d" % i for i in range(len(function.inputs))]
        argtypes = [map_type(i.type) for i in function.inputs]

        restype = type_from_outputs(function.outputs)
        signature = types.Function(restype, argtypes)

        # Setup up pykit function
        self.func = ir.Function("theano_func", argnames, signature)
        self.builder = ir.Builder(self.func)
        self.builder.position_at_end(self.func.add_block('entry'))

        # Theano Variable -> PyKit Operation
        self.values = {}

        self.update_dict = {} # Z_new[...] = Z_old[...]

    # ______________________________________________________________________

    def run(self):
        self.initialize()
        for output_var in self.theano.outputs:
            self.visit(output_var)
        self.finalize()
        return self.func

    def initialize(self):
        for input_var, argname in zip(self.theano.inputs, self.func.args):
            self.values[input_var] = self.func.get_arg(argname)

    def finalize(self):
        outs = self.readvars(*self.theano.outputs)
        if len(outs) > 1:
            out = self.builder.new_tuple(self.func.type.restype, outs)
        else:
            out, = outs

        self.builder.ret(out)

    # ______________________________________________________________________

    def readvars(self, *vars):
        return [self.values[var] for var in vars]

    def visit(self, var):
        assert isinstance(var, Variable)
        apply = var.owner

        # Recurse ...
        for input_var in apply.inputs:
            if input_var not in self.values:
                self.visit(input_var)

        # Gather input values
        inputs = [self.values[input_var] for input_var in apply.inputs]
        output_types = [map_type(v.type) for v in apply.outputs]

        # Apply operation
        opname = type(apply.op).__name__
        if not hasattr(self, opname):
            raise RuntimeError("Cannot convert operation " + opname)
        result = getattr(self, opname)(inputs, output_types)

        # Update value map
        result = listify(result)
        assert len(result) == len(apply.outputs)
        for theano_var, pykit_result in zip(apply.outputs, result):
            theano_var = self.update_dict.get(theano_var, theano_var)
            self.values[theano_var] = pykit_result

    # ______________________________________________________________________

    def Add(self, inputs, output_types):
        return self.builder.add(output_types[0], inputs)

    def Mul(self, inputs, output_types):
        return self.builder.mul(output_types[0], inputs)

    def Dot(self, inputs, output_types):
        out_t, = output_types
        op = ir.Operation("dot", out_t, inputs)
        self.builder.emit(op)
        return op


to_pykit = lambda theano_function: Codegen(theano_function).run()

# __________________________________________________________________________

expected = """
function Array(base=Real(bits=64), ndim=1, order='A') theano_func(Array(base=Real(bits=64), ndim=1, order='A') %arg0, Array(base=Real(bits=64), ndim=1, order='A') %arg1, Array(base=Real(bits=64), ndim=1, order='A') %arg2) {
entry:
    %0 = (Array(base=Real(bits=64), ndim=1, order='A')) mul(%arg0, %arg1)
    %1 = (Array(base=Real(bits=64), ndim=1, order='A')) add(%0, %arg2)
    %2 = (Void) ret(%1)

}
""".strip()

class TestPykitMapping(unittest.TestCase):
    def test_pykit_mapping(self):
        fvector = TensorType('float64', [False])

        x = Variable(fvector)
        y = Variable(fvector)
        z = Variable(fvector)
        w = Variable(fvector)
        u = Variable(fvector)

        a0 = Apply(Mul(), [x, y], [z])
        z.owner = a0
        a1 = Apply(Add(), [z, w], [u])
        u.owner = a1

        f = Function([x, y, w], [u])

        pykit_func = to_pykit(f)
        self.assertEqual(str(pykit_func).strip(), expected)

# __________________________________________________________________________
# Test gemm

gemm_unopt_expected = """
function Array(base=Real(bits=32), ndim=2, order='A') theano_func(Array(base=Real(bits=32), ndim=0, order='A') %arg0, Array(base=Real(bits=32), ndim=0, order='A') %arg1, Array(base=Real(bits=32), ndim=2, order='A') %arg2, Array(base=Real(bits=32), ndim=2, order='A') %arg3, Array(base=Real(bits=32), ndim=2, order='A') %arg4) {
entry:
    %0 = (Array(base=Real(bits=32), ndim=2, order='A')) mul(%arg1, %arg4)
    %1 = (Array(base=Real(bits=32), ndim=2, order='A')) dot(%arg2, %arg3)
    %2 = (Array(base=Real(bits=32), ndim=2, order='A')) mul(%arg0, %1)
    %3 = (Array(base=Real(bits=32), ndim=2, order='A')) add(%0, %2)
    %4 = (Void) ret(%3)

}
""".strip()

gemm_opt_expected = """
function Array(base=Real(bits=32), ndim=2, order='A') theano_func(arg0 %arg0, arg1 %arg1, arg2 %arg2, arg3 %arg3, arg4 %arg4) {
entry:
    %0 = (Array(base=Real(bits=32), ndim=2, order='A')) gemm(%arg0, %arg2, %arg3, %arg1, %arg4)
    %1 = (Void) ret(%0)
}
""".strip()

class TestDot(unittest.TestCase):
    def test_gemm(self):
        fmatrix = TensorType('float32', [False, False])
        fscalar = TensorType('float32', [])

        alpha = Variable(fscalar)
        beta = Variable(fscalar)

        X = Variable(fmatrix)
        Y = Variable(fmatrix)
        Z = Variable(fmatrix)

        Z_new = beta * Z + alpha * dot(X, Y)

        f = Function([alpha, beta, X, Y, Z], [Z_new])

        # XXX how to get dot instruction into IR ?
        pykit_func = to_pykit(f)
        self.assertEqual(str(pykit_func).strip(), gemm_unopt_expected.strip())

        # pykit_func.do_gemm_optimization() # XXX does not exist
        # assert str(pykit_func).strip() == gemm_opt_expected

    def test_gemm_update(self):
        #TODO: optimize to single gemm instruction
        fmatrix = TensorType('float32', [False, False])
        fscalar = TensorType('float32', [])

        alpha = Variable(fscalar)
        beta = Variable(fscalar)

        X = Variable(fmatrix)
        Y = Variable(fmatrix)
        Z = Variable(fmatrix)

        Z_new = beta * Z + alpha * dot(X, Y)

        f = Function([alpha, beta, X, Y, Z], [Z_new], updates=[[Z, Z_new]])

        # XXX how to get dot instruction into IR ?
        pykit_func = to_pykit(f)
        assert str(pykit_func).strip() == gemm_unopt_expected

        # pykit_func.do_gemm_optimization() # XXX does not exist
        # assert str(pykit_func).strip() == gemm_opt_expected
