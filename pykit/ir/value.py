# -*- coding: utf-8 -*-

"""
In-memory data structures to hold the IR. We use a flow-graph of Operations.
An operation is
"""

from __future__ import print_function, division, absolute_import
import collections
from itertools import chain, islice

from pykit import types
from pykit.adt import LinkedList
from pykit.ir import ops
from pykit.ir.pretty import pretty
from pykit.utils import (flatten, nestedmap, match, Delegate, traits, listify)

# ______________________________________________________________________

def make_temper():
    """Return a function that returns temporary names"""
    temps = collections.defaultdict(int)

    def temper(name=None):
        count = temps[name]
        temps[name] += 1
        if name and count == 0:
            return name
        elif name:
            return '%s%d' % (name, count)
        else:
            return str(count)

    return temper

# ______________________________________________________________________

class Value(object):
    __str__ = pretty

class Module(Value):
    """
    A module containing global values and functions. This defines the scope
    of functions that can see each other.

        globals:    { global_name: GlobalValue }
        functions:  { func_name : Function }
    """

    def __init__(self, globals=None, functions=None, temper=None):
        self.globals = globals or {}
        self.functions = functions or {}
        self.temp = temper or make_temper()

        for value in chain(self.globals.values(), self.functions.values()):
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
        return self.functions.get(funcname)

    def get_global(self, gvname):
        return self.globals.get(gvname)

class Function(Value):
    """
    Function consisting of basic blocks.

        module:     Module owning the function
        name:       name of the function
        args:       [FuncArg]
        argnames:   argument names ([str])
        blocks:     List of basic blocks in topological order
        entry:      The entry basic block
        values:     { op_name: Operation }
        temp:       allocate a temporary name
    """

    def __init__(self, name, argnames, type, temper=None):
        self.module = None
        self.name = name
        self.type = type
        self.temp = temper or make_temper()

        self.blocks = LinkedList()
        self.blockmap = dict((block.label, block) for block in self.blocks)
        self.argnames = argnames
        self.argdict = {}

        # reserve names
        for argname in argnames:
            self.temp(argname)

    @property
    def args(self):
        return [self.get_arg(argname) for argname in self.argnames]

    @property
    def startblock(self):
        return self.blocks.head

    @property
    def exitblock(self):
        return self.blocks.tail

    @property
    def ops(self):
        """Get a flat iterable of all Ops in this function"""
        return chain(*self.blocks)

    def add_block(self, label, ops=None, after=None):
        assert label not in self.blockmap, label
        label = self.temp(label)

        block = Block(label, self, ops)
        self.blockmap[label] = block

        if after is None:
            self.blocks.append(block)
        else:
            self.blocks.insert_after(block, after)

        return block

    def get_block(self, label):
        return self.blockmap[label]

    def get_arg(self, argname):
        """Get argument as a Value"""
        if argname in self.argdict:
            return self.argdict[argname]

        idx = self.argnames.index(argname)
        type = self.type.argtypes[idx]
        arg = FuncArg(self, argname, type)
        self.argdict[argname] = arg
        return arg

    @property
    def result(self):
        """We are a first-class value..."""
        return self.name

    def __repr__(self):
        return "FunctionGraph(%s)" % self.blocks


class FuncArg(Value):
    """
    Argument to the function. Use Function.get_arg()
    """

    def __init__(self, func, name, type):
        self.parent = func
        self.type   = type
        self.result = name

    def __repr__(self):
        return "FuncArg(%%%s)" % self.result


class GlobalValue(Value):
    """
    GlobalValue in a Module.
    """

    def __init__(self, name, type, external=False, address=None, value=None):
        self.module = None
        self.name = name
        self.type = type
        self.external = external
        self.address = address
        self.value = value

    @property
    def result(self):
        """We are a first-class value..."""
        return self.name


@traits
class Block(Value):
    """
    Basic block of Operations.

        name:   Name of block (unique within function)
        parent: Function owning block
    """

    head, tail = Delegate('ops'), Delegate('ops')
    _prev, _next = None, None # LinkedList

    def __init__(self, name, parent=None, ops=None):
        self.name   = name
        self.parent = parent
        self.ops = LinkedList(ops or [])

    @property
    def opcodes(self):
        """Returns [opcode] for all operations in the block"""
        for op in self.ops:
            yield op.opcode

    @property
    def optypes(self):
        """Returns [type] for all operations in the block"""
        for op in self.ops:
            yield op.type

    def __iter__(self):
        return iter(self.ops)

    def append(self, op):
        """Append op to block"""
        self.ops.append(op)
        op.parent = self
        # self.parent.values[op.result] = op

    def extend(self, ops):
        """Extend block with ops"""
        for op in ops:
            self.append(op)

    @property
    def result(self):
        """We are a first-class value..."""
        return self.name

    @property
    @listify
    def leaders(self):
        """
        Return an iterator of basic block leaders
        """
        for op in self.ops:
            if ops.is_leader(op.opcode):
                yield op
            else:
                break

    @property
    def terminator(self):
        """Block Op in block, which needs to be a terminator"""
        assert ops.is_terminator(self.ops.tail.opcode), self.ops.tail
        return self.ops.tail

    def __repr__(self):
        return "Block(%s)" % self.name


class Operation(Value):
    """
    Typed n-ary operation with a result. E.g.

        %0 = add(%a, %b)

    Attributes:

        opcode:     ops.* opcode, e.g. "getindex"
        type:       types.* type instance
        args:       (one level nested) list of argument Values
        operands:   symbolic operands, e.g. ['%0'] (virtual registers)
        result:     symbol result, e.g. '%0'
        args:       Operand values, e.g. [Operation("getindex", ...)
    """

    __slots__ = ("parent", "opcode", "type", "args", "result", "metadata",
                 "_prev", "_next")

    def __init__(self, opcode, type, args, result=None, parent=None):
        self.parent   = parent
        self.opcode   = opcode
        self.type     = type
        self.args     = args
        self.result   = result
        self.metadata = None
        self._prev    = None
        self._next    = None

    def __iter__(self):
        return iter((self.result, self.type, self.opcode, self.args))

    def insert_before(self, op):
        """Insert self before op"""
        assert self.parent is None, op
        self.parent = op.parent
        self.parent.ops.insert_before(self, op)

    def insert_after(self, op):
        """Insert self after op"""
        assert self.parent is None, self
        self.parent = op.parent
        self.parent.ops.insert_after(self, op)

    def replace_op(self, opcode, args, type=None):
        """Replace this operation's opcode, args and optionally type"""
        # Replace ourselves inplace
        self.opcode = opcode
        self.args   = args
        if type is not None:
            self.type = type

    def _set_registers(self, *ops):
        for op in ops:
            if not op.result:
                op.result = self.function.temp()
        return ops

    @match
    def replace(self, op):
        """
        Replace this operation with a new operation, changing this operation.
        """
        assert op.result is not None and op.result == self.result
        self.replace_op(op.opcode, op.operands, op.type)

    @replace.case(op=list)
    def replace_list(self, op):
        """
        Replace this Op with a list of other Ops. If no Op has the same
        result as this Op, the Op is deleted:

            >>> print block
            %0 = ...
            >>> print [op0, op1, op2]
            [%0 = ..., %1 = ..., %2 = ...]
            >>> op0.replace_with([op1, op0, op2])
            >>> print block
            %1 = ...
            %0 = ...
            %2 = ...
            >>> op0.replace_with([op3, op4])
            %1 = ...
            %3 = ...
            %4 = ...
            %2 = ...
        """
        lst = self._set_registers(*op)
        for i, op in enumerate(lst):
            if op.result == self.result:
                break
            op.insert_before(self)
        else:
            self.delete()
            return

        self.replace(op)
        last = op
        for op in lst[i + 1:]:
            op.insert_after(last)
            last = op

    def delete(self):
        """Delete this operation"""
        self.unlink()
        self.result = None

    def unlink(self):
        """Unlink from the basic block"""
        self.parent.ops.remove(self)
        self.parent = None

    def add_metadata(self, metadata):
        if self.metadata is None:
            self.metadata = metadata
        else:
            self.metadata.update(metadata)

    # @property
    # def args(self):
    #     """Operation arguments of this Operation (may be nested 1 level)"""
    #     values = self.block.parent.values
    #     return [values[argname] for argname in self.operands]

    @property
    def function(self):
        return self.parent.parent

    @property
    def block(self):
        """Containing block"""
        return self.parent

    @property
    def operands(self):
        """
        Operands to this operation, in the form of args with symbols
        and constants.

            >>> print Op("mul", Int32, [op_a, op_b]).operands
            ['a', 'b']
        """
        non_constants = (Block, Operation, FuncArg, GlobalValue)
        result = lambda x: x.result if isinstance(x, non_constants) else x
        return nestedmap(result, self.args)

    @property
    def symbols(self):
        """Set of symbolic register operands"""
        return [x for x in flatten(self.operands)]

    def __repr__(self):
        if self.result:
            return "%s = %s(%s)" % (self.result, self.opcode, repr(self.operands))
        return "%s(%s)" % (self.opcode, repr(self.operands))


class Constant(Value):
    """
    Constant value.
    """

    def __init__(self, pyval, type=None):
        self.opcode = ops.constant
        self.type = type or types.typeof(pyval)
        self.args = [pyval]
        self.result = None

    def replace_op(self, opcode, args, type=None):
        raise RuntimeError("Constants cannot be replaced")

    def replace(self, newop):
        raise RuntimeError("Constants cannot be replaced")

    @property
    def const(self):
        const, = self.args
        return const

    def __repr__(self):
        return "constant(%s)" % (self.const,)


class Undef(Value):
    """Undefined value"""

    def __init__(self, type):
        self.type = type

    def __eq__(self, other):
        return isinstance(other, Undef) and self.type == other.type

Op = Operation
Const = Constant