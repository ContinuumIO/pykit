import numpy as np


class Op(object):
    def __init__(self):
        pass


class Type(object):
    def __init__(self):
        pass


class Variable(object):
    def __init__(self, type, owner=None):
        self.type = type
        self.owner = owner


class Apply(object):
    def __init__(self, op, inputs, outputs):
        self.op = op
        self.inputs = inputs
        self.outputs = outputs


class Add(Op):
    def compute(self, a, b):
        return a + b


class Mul(Op):
    def compute(self, a, b):
        return a * b


class TensorType(object):
    def __init__(self, dtype, broadcastable):
        self.dtype = dtype
        self.broadcastable = broadcastable


class Function(object):
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs

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
        # do something actual here
        return types.Float64

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
        argtypes = ["arg%d" % i for i in range(len(function.inputs))]

        restype = type_from_outputs(function.outputs)
        signature = types.Function(restype, argtypes)

        # Setup up pykit function
        self.func = ir.Function("theano_func", argnames, signature)
        self.builder = ir.Builder(self.func)
        self.builder.position_at_end(self.func.add_block('entry'))

        # Theano Variable -> PyKit Operation
        self.values = {}

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
        result = getattr(self, opname)(inputs, output_types)

        # Update value map
        result = listify(result)
        assert len(result) == len(apply.outputs)
        for theano_var, pykit_result in zip(apply.outputs, result):
            self.values[theano_var] = pykit_result

    # ______________________________________________________________________

    def Add(self, inputs, output_types):
        return self.builder.add(output_types[0], inputs)

    def Mul(self, inputs, output_types):
        return self.builder.mul(output_types[0], inputs)


to_pykit = lambda theano_function: Codegen(theano_function).run()

# __________________________________________________________________________

expected = """
function Array(base=Real(bits=64), ndim=1, order='A') theano_func(arg0 %arg0, arg1 %arg1, arg2 %arg2) {
entry:
    %0 = (Array(base=Real(bits=64), ndim=1, order='A')) mul(%arg0, %arg1)
    %1 = (Array(base=Real(bits=64), ndim=1, order='A')) add(%0, %arg2)
    %2 = (Void) ret(%1)

}
""".strip()

def test_pykit_mapping():
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

    pykit_func = to_pykit(f)
    assert str(pykit_func).strip() == expected