# -*- coding: utf-8 -*-

"""
IR interpreter.
"""

from __future__ import print_function, division, absolute_import

import ctypes
import operator
try:
    import exceptions
except ImportError:
    import builtins as exceptions
from itertools import chain, product
from collections import namedtuple
from functools import partial

import numpy as np

from pykit import types
from pykit.ir import Function, Block, GlobalValue, Const, combine, ArgLoader
from pykit.ir import ops, linearize, defs
from pykit.utils import ValueDict

#===------------------------------------------------------------------===
# Interpreter
#===------------------------------------------------------------------===

Undef = object()                        # Undefined/uninitialized value
State = namedtuple('State', ['refs'])   # State shared by stack frames

class Reference(object):
    """
    Models a reference to an object
    """

    def __init__(self, obj, refcount, producer):
        self.obj = obj
        self.refcount = refcount
        self.producer = producer

class UncaughtException(Exception):
    """
    Raised by the interpreter when code raises an exception that isn't caught
    """

class Interp(object):
    """
    Interpret the function given as a ir.Function. See the run() function
    below.

        func:           The ir.Function we interpret
        exc_model:      ExceptionModel that knows how to deal with exceptions
        argloader:      InterpArgloader: knows how pykit Values are associated
                        with runtime (stack) values (loads from the store)
        ops:            Flat list of instruction targets (['%0'])
        blockstarts:    Dict mapping block labels to address offsets
        prevblock:      Previously executing basic block
        pc:             Program Counter
        lastpc:         Last value of Program Counter
        exc_handlers:   List of exception target blocks to try
        exception:      Currently raised exception
        refs:           { id(obj) : Reference }
    """

    def __init__(self, func, env, exc_model, argloader, state):
        self.func = func
        self.env = env
        self.exc_model = exc_model
        self.argloader = argloader

        self.state = {
            'env':       env,
            'exc_model': exc_model,
        }

        self.ops, self.blockstarts = linearize(func)
        self.lastpc = 0
        self._pc = 0
        self.prevblock = None
        self.exc_handlers = None
        self.exception = None

        self.refs = state.refs

    # __________________________________________________________________
    # Utils

    def incr_pc(self):
        """Increment program counter"""
        self.pc += 1

    @property
    def op(self):
        """Return the current operation"""
        return self.getop(self.pc)

    def getop(self, pc):
        """PC -> Op"""
        return self.ops[pc]

    def setpc(self, newpc):
        self.lastpc = self.pc
        self._pc = newpc

    pc = property(lambda self: self._pc, setpc, doc="Program Counter")

    def blockswitch(self, oldblock, newblock):
        self.prevblock = oldblock
        self.exc_handlers = []

    noop = lambda *args: None

    # __________________________________________________________________
    # Core operations

    # unary, binary and compare operations set below

    def convert(self, arg):
        return types.convert(arg, self.op.type)

    def check_overflow(self, value):
        assert self.op.type.is_int
        bits = self.op.type.bits / 2
        lower = 2 ** -bits
        upper = 2 ** bits - 1
        if not lower <= value <= upper:
            raise OverflowError(value, self.op, lower, upper)

    # __________________________________________________________________
    # Var

    def alloca(self):
        return { 'value': Undef, 'type': self.op.type }

    def load(self, var):
        assert var['value'] is not Undef, self.op
        return var['value']

    def store(self, value, var):
        var['value'] = value

    def phi(self):
        for i, block in enumerate(self.op.args[0]):
            if block == self.prevblock:
                values = self.op.args[1]
                return self.argloader.load_op(values[i])

        raise RuntimeError("Previous block %r not a predecessor of %r!" %
                                    (self.prevblock.name, self.op.block.name))

    # __________________________________________________________________
    # Functions

    def function(self, funcname):
        return self.func.module.get_function(funcname)

    def partial(self, function, *args):
        if isinstance(function, Function):
            return lambda *more: self.call(function, *(args + more))

    def call(self, func, args):
        if isinstance(func, Function):
            # We're calling another known pykit function,
            try:
                return run(func, args=args, **self.state)
            except UncaughtException as e:
                # make sure to handle any uncaught exceptions properly
                self.exception, = e.args
                self._propagate_exc()
        else:
            return func(*args)

    def call_math(self, fname, *args):
        return defs.math_funcs[fname](*args)

    def call_external(self):
        pass

    def call_virtual(self):
        pass

    # __________________________________________________________________
    # Attributes

    getfield = getattr
    setfield = setattr

    # __________________________________________________________________
    # Index

    getindex = operator.getitem
    setindex = operator.setitem
    getslice = operator.getitem
    setslice = operator.setitem
    slice = slice

    # __________________________________________________________________
    # Arrays

    allpairs = product # hmm

    def map(self, f, args, axes):
        assert not axes # TODO
        u = np.vectorize(f)
        return u(*args)

    def reduce(self, f, arg, axes):
        assert not axes # TODO
        if isinstance(arg, np.ndarray):
            arg = arg.flatten()
        return reduce(f, arg)

    def scan(self, f, arg, axes):
        assert not axes # TODO
        result = arg.copy().flatten()
        for i, x in enumerate(arg.flatten()[1:]):
            result[i+1] = f(result[i], result[i+1])
        return result

    # __________________________________________________________________

    print = print

    # __________________________________________________________________
    # Pointer

    def ptradd(self, ptr, addition):
        val = ctypes.cast(ptr, ctypes.c_void_p).value
        return ctypes.cast(val, type(ptr))

    def ptrload(self, ptr):
        return ptr[0]

    def ptrstore(self, ptr, value):
        ptr[0] = value

    def ptr_isnull(self, ptr):
        return ctypes.cast(ptr, ctypes.c_void_p).value == 0

    def func_from_addr(self, ptr):
        type = self.op.type
        return ctypes.cast(ptr, types.to_ctypes(type))

    # __________________________________________________________________
    # iterators

    getiter = iter

    def next(self, it):
        try:
            return next(it)
        except Exception as e:
            self.exc_throw(e)

    # __________________________________________________________________
    # Primitives

    max = max
    min = min

    # __________________________________________________________________
    # Constructors

    new_list    = list
    new_tuple   = tuple
    new_set     = set
    new_dict    = lambda self, keys, values: dict(zip(keys, values))

    # __________________________________________________________________
    # Control flow

    def ret(self, arg):
        self.pc = -1
        if self.func.type.restype != types.Void:
            return arg

    def cbranch(self, test, true, false):
        if test:
            self.pc = self.blockstarts[true.name]
        else:
            self.pc = self.blockstarts[false.name]

    def jump(self, block):
        self.pc = self.blockstarts[block.name]

    # __________________________________________________________________
    # Exceptions

    def new_exc(self, exc_name, exc_args):
        return self.exc_model.exc_instantiate(exc_name, *exc_args)

    def exc_catch(self, types):
        self.exception = None # We caught it!

    def exc_setup(self, exc_handlers):
        self.exc_handlers = exc_handlers

    def exc_throw(self, exc):
        self.exception = exc
        self._propagate_exc() # Find exception handler

    def _exc_match(self, exc_types):
        """
        See whether the current exception matches any of the exception types
        """
        return any(self.exc_model.exc_match(self.exception, exc_type)
                        for exc_type in exc_types)

    def _propagate_exc(self):
        """Propagate installed exception (`self.exception`)"""
        catch_op = self._find_handler()
        if catch_op:
            # Exception caught! Transfer control to block
            catch_block = catch_op.parent
            self.pc = self.blockstarts[catch_block.name]
        else:
            # No exception handler!
            raise UncaughtException(self.exception)

    def _find_handler(self):
        """Find a handler for an active exception"""
        exc = self.exception

        for block in self.exc_handlers:
            for leader in block.leaders:
                if (leader.opcode == ops.exc_catch and
                        self._exc_match(leader.args)):
                    return leader

    # __________________________________________________________________
    # Generators

    def yieldfrom(self, op):
        pass # TODO:

    def yieldval(self, op):
        pass # TODO:

    # __________________________________________________________________
    # Closures

    def make_cell(self):
        return { 'cell': Undef }

    def load_cell(self, cell):
        assert cell['cell'] is not Undef
        return cell['cell']

    def store_cell(self, cell, value):
        cell['cell'] = value

    def make_frame(self, parent, names):
        values = dict((name, Undef) for name in names)
        values['_parent_frame'] = parent
        return ValueDict(values)

    # __________________________________________________________________
    # Threads

    thread_start      = noop
    thread_join       = noop
    threadpool_start  = noop
    threadpool_submit = noop
    threadpool_join   = noop
    threadpool_close  = noop

    def load_vtable(self, op):
        pass

    def vtable_lookup(self, op):
        pass

    # __________________________________________________________________
    # GC/Refcounting

    def _checkref(self, obj):
        assert id(obj) in self.refs
        ref = self.refs[id(obj)]
        assert ref.obj is obj
        assert ref.refcount >= 1

    def gc_incref(self, obj):
        self._checkref(obj)
        ref = self.refs[id(obj)]
        ref.refcount += 1

    def gc_decref(self, obj):
        self._checkref(obj)
        ref = self.refs[id(obj)]
        ref.refcount -= 1
        if ref.refcount == 0:
            del self.refs[id(obj)]

    def gc_gotref(self, obj):
        assert id(obj) not in self.refs
        self.refs[id(obj)] = 1

    def gc_giveref(self, obj):
        self._checkref(obj)

    def gc_alloc(self, n):
        result = np.empty(n, dtype=np.object)
        result[...] = Undef
        return result

    def gc_dealloc(self, value):
        value[...] = Undef

    def gc_collect(self, op):
        pass

    def gc_read_barrier(self, op):
        pass

    def gc_traverse(self, op):
        pass

    def gc_write_barrier(self, op):
        pass

# Set unary, binary and compare operators
for opname, evaluator in chain(defs.unary.items(), defs.binary.items(),
                               defs.compare.items()):
    setattr(Interp, opname, staticmethod(evaluator))

#===------------------------------------------------------------------===
# Exceptions
#===------------------------------------------------------------------===

class ExceptionModel(object):
    """
    Model that governs the exception hierarchy
    """

    def exc_match(self, exc_type, exception):
        """
        See whether `exception` matches `exc_type`
        """
        return (isinstance(exc_type, exception) or
                issubclass(exception, exc_type))

    def exc_instantiate(self, exc_name, *args):
        """
        Instantiate an exception
        """
        exc_type = getattr(exceptions, exc_name)
        return exc_type(*args)

#===------------------------------------------------------------------===
# Run
#===------------------------------------------------------------------===

def _init_state(func, args):
    """Initialize refcount state"""
    refcounts = {}
    return State(refcounts) # todo
    for param, arg in zip(func.args, args):
        if param.type.managed:
            refcounts[id(arg)] = Reference(obj=arg, refcount=1, producer=param)

    return State(refcounts)

class InterpArgLoader(ArgLoader):

    def load_GlobalValue(self, arg):
        assert not arg.external, "Not supported yet"
        return arg.value.const

    def load_Undef(self, arg):
        return Undef


def run(func, env=None, exc_model=None, _state=None, args=()):
    """
    Interpret function. Raises UncaughtException(exc) for uncaught exceptions
    """
    assert len(func.args) == len(args)

    valuemap = dict(zip(func.argnames, args)) # { '%0' : pyval }
    argloader = InterpArgLoader(valuemap)
    interp = Interp(func, env, exc_model or ExceptionModel(),
                    argloader, state=_state or _init_state(func, args))
    if env:
        handlers = env.get("interp.handlers") or {}
    else:
        handlers = {}

    curblock = None
    while True:
        op = interp.op
        if op.block != curblock:
            interp.blockswitch(curblock, op.block)
            curblock = op.block

        if op.opcode in handlers:
            fn = partial(handlers[op.opcode], interp)
        else:
            fn = getattr(interp, op.opcode)

        args = argloader.load_args(op)

        # Execute...
        oldpc = interp.pc
        result = fn(*args)
        valuemap[op.result] = result

        # Advance PC
        if oldpc == interp.pc:
            interp.incr_pc()
        elif interp.pc == -1:
            # Returning...
            return result
