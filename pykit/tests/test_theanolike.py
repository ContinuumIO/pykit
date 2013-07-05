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
