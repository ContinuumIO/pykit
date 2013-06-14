# -*- coding: utf-8 -*-

"""
In-memory data structures to hold the IR. We use a flow-graph of Operations.
An operation is
"""

from __future__ import print_function, division, absolute_import
import collections
import itertools
from pykit import ir

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

    def add_global(self, globalvalue):
        assert globalvalue.name not in self.globals, globalvalue.name
        self.functions[globalvalue.name] = globalvalue


class Function(object):
    """
    Function consisting of basic blocks.

        name: name of the function
        blocks: List of basic blocks in topological order
        values: { instr_name: Operation }
        uses:   { instr_name: { instr_name } }
        mktemp: allocate a temporary name
    """

    def __init__(self, name, type=None, args=None, blocks=None, temper=None):
        self.parent = None
        self.name = name
        self.type = type
        self.args = args or []
        self.blocks = blocks or []
        self.values = {}
        self.uses = {}       # { instr_name : [ instr_name ] }
        self.mktemp = temper or make_temper()

    def __repr__(self):
        return "FunctionGraph(%s)" % self.blocks


class GlobalValue(object):
    """
    GlobalValue in a Module.
    """

    def __init__(self, name, type, parent=None, external=False, address=None):
        self.parent = parent
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

    def __init__(self, name, parent=None, instrs=None):
        self.name = name            # unique label
        self.parent = parent        # FunctionGraph that owns us
        self.instrs = instrs or []  # [instr_name]

    def __iter__(self):
        return iter(self.instrs)

    def insert_at(self, pos, instr):
        self.instrs.insert(pos, instr)
        instr.parent = self

    def append(self, instr):
        self.instrs.append(instr.result)
        self.parent.values[instr.result] = instr

    def extend(self, instrs):
        for instr in instrs:
            self.append(instr)

    def __repr__(self):
        return "Block(%s, %s)" % (self.name,)


class Operation(Value):
    """
    Typed n-ary operation with a result. E.g.

        %0 = add(%a, %b)
    """

    __slots__ = ("opcode", "type", "args", "result") + Value.__slots__

    def __init__(self, opcode, type, args, result=None):
        self.opcode = opcode
        self.type = type
        self.args = args
        self.result = result

    def replace(self, opcode, args):
        """Rewrite this operation"""
        self.opcode = opcode
        self.args = args

    def replace_with(self, operation):
        """
        Replace each use of this operation with a new operation.
        """
        uses = self.function.uses
        values = self.function.values
        dst = operation.result
        src = self.result

        def replace(arg):
            if arg == src:
                uses[dst].add(arg)
                return dst
            return src

        for use in self.uses[src]:
            value = values[use]
            for i, arg in enumerate(value.args):
                if isinstance(arg, list):
                    use.args[i] = [replace(v) for v in arg]
                else:
                    use.args[i] = replace(arg)

        del uses[src]
        self.delete()

    def insert_before(self, instr, other):
        block = other.parent
        idx = block.instrs.index(other.result)
        block.insert_at(idx, instr)

    def insert_after(self, instr, other):
        block = other.parent
        idx = block.instrs.index(other.result) + 1
        block.insert_at(idx, instr)

    def delete(self):
        uselist = self.function.uses[self.result]
        assert not uselist, uselist
        del self.function.values[self.result]
        self.block.instrs.remove(self.result)

    @property
    def ops(self):
        values = self.block.parent.values
        return [values[argname] for argname in self.args]

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

    def __init__(self, pyval):
        self.opcode = ir.constant
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

op = Operation
const = Constant