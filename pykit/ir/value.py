# -*- coding: utf-8 -*-

"""
In-memory data structures to hold the IR. We use a flow-graph of Operations.
An operation is
"""

from __future__ import print_function, division, absolute_import
from itertools import chain
from collections import defaultdict

from pykit import error, types
from pykit.adt import LinkedList
from pykit.ir import ops
from pykit.ir.pretty import pretty
from pykit.utils import (flatten, nestedmap, match, Delegate, traits, listify,
                         make_temper)

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

    Attributes
    ----------
    module: Module
         Module owning the function

    name:
        name of the function

    args: [FuncArg]

    argnames:
        argument names ([str])

    blocks:
        List of basic blocks in topological order

    startblock: Block
        The entry basic block

    exitblock: Block
        The last block in the list. This will only be the actual 'exit block'
        if the function is actually populated and has an exit block.

    values:  { op_name: Operation }

    uses: { Operation : [Operation] }
        Operations that refer to this operation in their 'args' list

    temp: function, name -> tempname
        allocate a temporary name
    """

    def __init__(self, name, argnames, type, temper=None):
        self.module = None
        self.name = name
        self.type = type
        self.temp = temper or make_temper()

        self.blocks = LinkedList()
        self.blockmap = dict((block.name, block) for block in self.blocks)
        self.argnames = argnames
        self.argdict = {}

        self.uses = defaultdict(set)

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

    def new_block(self, label, ops=None, after=None):
        """Create a new block with name `label` and append it"""
        assert label not in self.blockmap, label
        label = self.temp(label)
        return self.add_block(Block(label, self, ops), after)

    def add_block(self, block, after=None):
        """Add a Block at the end, or after `after`"""
        if block.parent is None:
            block.parent = self
        else:
            assert block.parent is self

        self.blockmap[block.name] = block
        if after is None:
            self.blocks.append(block)
        else:
            self.blocks.insert_after(block, after)

        return block

    def get_block(self, label):
        return self.blockmap[label]

    def del_block(self, block):
        self.blocks.remove(block)
        del self.blockmap[block.name]

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

    # ______________________________________________________________________
    # uses

    def add_op(self, op):
        """
        Register a new Op as part of the function.

        Does NOT insert the Op in any basic block
        """
        _add_args(self.uses, op, op.args)

    def reset_uses(self):
        from pykit.analysis import defuse
        self.uses = defuse.defuse(self)

    # ______________________________________________________________________

    def __repr__(self):
        return "FunctionGraph(%s)" % self.blocks


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
        self.parent.add_op(op)

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
        assert self.is_terminated(), self.ops.tail
        return self.ops.tail

    def is_terminated(self):
        """Returns whether the block is terminated"""
        return self.ops.tail and ops.is_terminator(self.ops.tail.opcode)

    def __repr__(self):
        return "Block(%s)" % self.name


class Local(Value):
    """
    Local value in a Function. This is either a FuncArg or an Operation.
    Constants do not belong to any function.
    """

    @property
    def function(self):
        """The Function owning this local value"""
        raise NotImplementedError

    def replace_uses(self, dst):
        """
        Replace all uses of `self` with `dst`. This does not invalidate this
        Operation!
        """
        src = self

        # Replace src with dst in use sites
        for use in set(self.function.uses[src]):
            def replace(op):
                if op == src:
                    return dst
                return op
            newargs = nestedmap(replace, use.args)
            use.set_args(newargs)


class FuncArg(Local):
    """
    Argument to the function. Use Function.get_arg()
    """

    def __init__(self, func, name, type):
        self.parent = func
        self.opcode = 'arg'
        self.type   = type
        self.result = name

    @property
    def function(self):
        return self.parent

    def __repr__(self):
        return "FuncArg(%%%s)" % self.result


class Operation(Local):
    """
    Typed n-ary operation with a result. E.g.

        %0 = add(%a, %b)

    Attributes:
    -----------
    opcode:
        ops.* opcode, e.g. "getindex"

    type: types.Type
        Result type of applying this operation

    args:
        (one level nested) list of argument Values

    operands:
        symbolic operands, e.g. ['%0'] (virtual registers)

    result:
        symbol result, e.g. '%0'

    args:
        Operand values, e.g. [Operation("getindex", ...)
    """

    __slots__ = ("parent", "opcode", "type", "args", "result", "metadata",
                 "_prev", "_next")

    def __init__(self, opcode, type, args, result=None, parent=None):
        self.parent   = parent
        self.opcode   = opcode
        self.type     = type
        self._args     = args
        self.result   = result
        self.metadata = None
        self._prev    = None
        self._next    = None

    @property
    def uses(self):
        "Enumerate all Operations referring to this value"
        return self.function.uses[self]

    @property
    def args(self):
        """Operands to this Operation (readonly)"""
        return self._args

    # ______________________________________________________________________
    # Placement

    def insert_before(self, op):
        """Insert self before op"""
        assert self.parent is None, op
        self.parent = op.parent
        self.parent.ops.insert_before(self, op)
        self.function.add_op(self)

    def insert_after(self, op):
        """Insert self after op"""
        assert self.parent is None, self
        self.parent = op.parent
        self.parent.ops.insert_after(self, op)
        self.function.add_op(self)

    # ______________________________________________________________________
    # Replace

    def replace_op(self, opcode, args, type=None):
        """Replace this operation's opcode, args and optionally type"""
        # Replace ourselves inplace
        self.opcode = opcode
        self.set_args(args)
        if type is not None:
            self.type = type

    def replace_args(self, replacements):
        """
        Replace arguments listed in the `replacements` dict. The replacement
        instructions must dominate this instruction.
        """
        if replacements:
            newargs = nestedmap(lambda arg: replacements.get(arg, arg), self.args)
            self.set_args(newargs)

    @match
    def replace(self, op):
        """
        Replace this operation with a new operation, changing this operation.
        """
        assert op.result is not None and op.result == self.result
        self.replace_op(op.opcode, op.args, op.type)

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

    # ______________________________________________________________________

    def set_args(self, args):
        """Set a new argslist"""
        _del_args(self.function.uses, self, self.args)
        _add_args(self.function.uses, self, args)
        self._args = args

    # ______________________________________________________________________

    def delete(self):
        """Delete this operation"""
        if self.uses:
            raise error.IRError(
                "Operation %s is still in use and cannot be deleted" % (self,))

        _del_args(self.function.uses, self, self.args)
        self.unlink()
        self.result = None

    def unlink(self):
        """Unlink from the basic block"""
        self.parent.ops.remove(self)
        self.parent = None

    # ______________________________________________________________________

    def add_metadata(self, metadata):
        if self.metadata is None:
            self.metadata = metadata
        else:
            self.metadata.update(metadata)

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

    # ______________________________________________________________________

    def _set_registers(self, *ops):
        "Set virtual register names if unset for each Op in ops"
        for op in ops:
            if not op.result:
                op.result = self.function.temp()
        return ops

    # ______________________________________________________________________

    def __repr__(self):
        if self.result:
            return "%s = %s(%s)" % (self.result, self.opcode,
                                    repr(self.operands))
        return "%s(%s)" % (self.opcode, repr(self.operands))

    def __iter__(self):
        return iter((self.result, self.type, self.opcode, self.args))



def _add_args(uses, newop, args):
    "Update uses when a new instruction is inserted"
    def add(arg):
        if isinstance(arg, (Op, FuncArg, Block)):
            uses[arg].add(newop)
    nestedmap(add, args)

def _del_args(uses, oldop, args):
    "Delete uses when an instruction is removed"
    seen = set() # Guard against duplicates in 'args'
    def remove(arg):
        if isinstance(arg, Operation) and arg not in seen:
            uses[arg].remove(oldop)
            seen.add(arg)
    nestedmap(remove, args)


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