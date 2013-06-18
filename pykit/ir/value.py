# -*- coding: utf-8 -*-

"""
In-memory data structures to hold the IR. We use a flow-graph of Operations.
An operation is
"""

from __future__ import print_function, division, absolute_import
import collections
import itertools
from pykit import types
from pykit.ir import ops

# ______________________________________________________________________

def make_temper():
    temps = collections.defaultdict(int)

    def temper(name):
        count = temps[name]
        temps[name] += 1
        if name and count == 0:
            return name
        elif name:
            return '%s_%d' % (name, count)
        else:
            return str(count)

    return temper

# ______________________________________________________________________

class Module(object):
    """
    A module containing global values and functions. This defines the scope
    of functions that can see each other.

        globals:    { global_name: GlobalValue }
        functions:  { func_name : Function }
    """

    def __init__(self, globals=None, functions=None, temper=None):
        self.globals = globals or {}
        self.functions = functions or {}
        self.mktemp = temper or make_temper()

        for value in itertools.chain(globals.values(), functions.values()):
            assert value.parent is None, (value, value.parent)
            value.parent = self

    def add_function(self, function):
        assert function.name not in self.functions, function.name
        self.functions[function.name] = function
        function.module = self

    def add_global(self, globalvalue):
        assert globalvalue.name not in self.globals, globalvalue.name
        self.globals[globalvalue.name] = globalvalue
        globalvalue.module = self

    def get_function(self, funcname):
        return self.functions[funcname]

    def get_global(self, gvname):
        return self.globals[gvname]


class Function(object):
    """
    Function consisting of basic blocks.

        name: name of the function
        blocks: List of basic blocks in topological order
        values: { op_name: Operation }
        uses:   { op_name: { op_name } }
        mktemp: allocate a temporary name
    """

    def __init__(self, name, type=None, args=None, blocks=None, temper=None):
        self.module = None
        self.name = name
        self.type = type
        self.args = args or []
        self.blocks = blocks or []
        self.values = {}
        self.uses = {}       # { op_name : [ op_name ] }
        self.mktemp = temper or make_temper()

    def addblock(self, label, ops=None):
        self.blocks.append(Block(label, self, ops))

    def __repr__(self):
        return "FunctionGraph(%s)" % self.blocks


class GlobalValue(object):
    """
    GlobalValue in a Module.
    """

    def __init__(self, name, type, external=False, address=None):
        self.module = None
        self.name = name
        self.type = type
        self.external = external
        self.address = address


class Value(object):
    """
    First-class Value in the IR.

        parent: owner of this value, e.g. Block owns Operation
        name: name of this value
    """

    __slots__ = ("parent", "name")


class Block(Value):
    """
    Basic block of Operations.
    """

    def __init__(self, name, parent=None, targets=None):
        self.name = name             # unique label
        self.parent = parent         # FunctionGraph that owns us
        self.targets = targets or [] # [targets]

    def __iter__(self):
        return iter(self.ops)

    def insert_at(self, pos, op):
        self.ops.insert(pos, op)
        op.parent = self

    def append(self, op):
        self.ops.append(op.result)
        self.parent.values[op.result] = op

    def extend(self, ops):
        for op in ops:
            self.append(op)

    def __repr__(self):
        return "Block(%s, %s)" % (self.name,)


class Operation(Value):
    """
    Typed n-ary operation with a result. E.g.

        %0 = add(%a, %b)

    Attributes:

        opcode:     ops.* opcode, e.g. "getindex"
        type:       types.* type instance
        operands:   symbolic operands, e.g. ['%0']
        result:     symbol result, e.g. '%0'
        args:       Operand values, e.g. [Operation("getindex", ...)
    """

    __slots__ = ("opcode", "type", "operands", "result") + Value.__slots__

    def __init__(self, opcode, type, operands, result=None):
        self.opcode = opcode
        self.type = type
        self.operands = operands
        self.result = result

    def __iter__(self):
        return iter((self.result, self.type, self.opcode, self.args))

    def replace(self, opcode, operands, type=None):
        """Rewrite this operation"""
        self.opcode = opcode
        self.operands = operands
        if type is not None:
            self.type = type

    def replace_with(self, op):
        """
        Replace each use of this operation with a new operation.
        """
        assert op.result is not None

        dst = op.result
        src = self.result
        if src == dst:
            return self.replace(op.opcode, op.operands, op.type)

        f = self.function
        f.values[src] = op # Update values, e.g. { '%0' : Op('%1', ...) }
        f.uses[dst].update(f.uses[src])
        self.delete()

    def insert_before(self, op, other):
        block = other.parent
        idx = block.ops.index(other.result)
        block.insert_at(idx, op)

    def insert_after(self, op, other):
        block = other.parent
        idx = block.ops.index(other.result) + 1
        block.insert_at(idx, op)

    def delete(self):
        uselist = self.function.uses[self.result]
        assert not uselist, uselist
        del self.function.values[self.result]
        self.block.ops.remove(self.result)

    @property
    def args(self):
        values = self.block.parent.values
        return [values[argname] for argname in self.operands]

    @property
    def function(self):
        return self.parent.parent

    @property
    def block(self):
        return self.parent

    @property
    def uses(self):
        return self.function.uses

    def __repr__(self):
        args = [arg.result for arg in self.args]
        return "%s(%s)" % (self.opcode, ", ".join(args))


class Constant(Value):
    """
    Constant value.
    """

    def __init__(self, pyval, type=None):
        self.opcode = ops.constant
        self.type = type or types.typeof(pyval)
        self.args = [pyval]
        self.result = None

    def replace(self, opcode, args):
        raise RuntimeError("Constants cannot be replaced")

    @property
    def const(self):
        const, = self.args
        return const

    def __repr__(self):
        return "constant(%s)" % (self.const,)

Op = Operation
Const = Constant