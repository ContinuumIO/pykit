# -*- coding: utf-8 -*-

"""
Convenience IR builder.
"""

from __future__ import print_function, division, absolute_import
from functools import partial
from contextlib import contextmanager

from pykit import types
from pykit.ir import Value, Op, Block, Const, ops
from pykit.utils import nestedmap

def make_arg(arg):
    """Return the virtual register or the result"""
    return arg.result if isinstance(arg, (Op, Block)) else arg


class Builder(object):
    """
    Simple Op builder.
    """

    def __init__(self, func):
        self.func = func
        self.temp = func.temp
        self.module = func.module
        self._curblock = None
        self._lastop = None

    # __________________________________________________________________
    # Positioning (optional)

    def _insert_op(self, op):
        """Insert op at the current position if set"""
        if self._curblock:
            if self._lastop == 'head' and self._curblock.ops.head:
                op.insert_before(self._curblock.ops.head)
            elif self._lastop in ('head', 'tail'):
                self._curblock.append(op)
            else:
                op.insert_after(self._lastop)
            self._lastop = op

    def _assert_position(self):
        assert self._curblock, "Builder is not positioned!"

    def position_at_beginning(self, block):
        """Position the builder at the beginning of the given block."""
        self._curblock = block
        self._lastop = 'head'

    def position_at_end(self, block):
        """Position the builder at the end of the given block."""
        self._curblock = block
        self._lastop = block.tail or 'tail'

    def position_before(self, op):
        """Position the builder before the given op."""
        self._curblock = op.block
        self._lastop = op._prev

    def position_after(self, op):
        """Position the builder after the given op."""
        self._curblock = op.block
        self._lastop = op

    @contextmanager
    def _position(self, block, position):
        curblock, lastop = self._curblock, self._lastop
        position(block)
        yield
        self._curblock, self._lastop = curblock, lastop

    at_front = lambda self, b: self._position(b, self.position_at_beginning)
    at_end   = lambda self, b: self._position(b, self.position_at_end)

    # __________________________________________________________________
    # Convenience

    def gen_call_external(self, fname, args):
        gv = self.module.get_global(fname)
        assert gv.type.is_function, gv
        assert gv.type.argtypes == [arg.type for arg in args]
        return self.call_external(gv.type.res, [Const(fname), args])

    def splitblock(self, name=None, terminate=False):
        """Split the current block, returning (old_block, new_block)"""
        self._assert_position()
        name = self.func.temp(name or 'block')
        newblock = self.func.add_block(name, after=self._curblock)
        op = self._lastop

        # Terminate if requested and not done already
        if terminate and not ops.is_terminator(op):
            op = self.jump(newblock)

        if op:
            # Move any tailing Ops...
            trailing = list(op.block.ops.iter_from(op))[1:]
            for op in trailing:
                op.unlink()
            newblock.extend(trailing)

        return self._curblock, newblock

    def gen_loop(self, start=None, stop=None, step=None):
        """
        Generate a loop given start, stop, step and the index variable type.
        The builder's position is set to the end of the body block.

        Returns (condition_block, body_block, exit_block).
        """
        self._assert_position()
        assert isinstance(stop, Value), "Stop should be a Constant or Operation"

        ty = stop.type
        start = start or Const(0, ty)
        step  = step or Const(1, ty)
        assert start.type == ty == step.type

        with self.at_front(self.func.blocks[0]):
            var = self.alloca(types.Pointer(ty), [])

        prev, exit = self.splitblock('loop.exit')
        cond = self.func.add_block('loop.cond', after=prev)
        body = self.func.add_block('loop.body', after=cond)

        with self.at_end(prev):
            self.store(start, var)
            self.jump(cond)

        # Condition
        with self.at_front(cond):
            index = self.load(ty, [var])
            self.store(self.add(ty, [index, step]), var)
            self.cbranch(self.lt(types.Bool, [index, stop]), body, exit)

        with self.at_end(body):
            self.jump(cond)

        self.position_at_beginning(body)
        return cond, body, exit

    # __________________________________________________________________
    # IR constructors

    def _op(op):
        """Helper to create Builder methods"""
        def _process(self, ty, args, result=None):
            assert ty is not None
            # args = nestedmap(make_arg, args)
            result = Op(op, ty, args, result or self.func.temp())
            self._insert_op(result)
            return result

        if ops.is_void(op):
            def build_op(self, *args, **kwds):
                return _process(self, types.Void, args, kwds.pop('result', None))
        else:
            build_op = _process

        return build_op

    _const = Const

    # Generated by pykit.utils._generate
    Sin                  = _const(ops.Sin)
    Asin                 = _const(ops.Asin)
    Sinh                 = _const(ops.Sinh)
    Asinh                = _const(ops.Asinh)
    Cos                  = _const(ops.Cos)
    Acos                 = _const(ops.Acos)
    Cosh                 = _const(ops.Cosh)
    Acosh                = _const(ops.Acosh)
    Tan                  = _const(ops.Tan)
    Atan                 = _const(ops.Atan)
    Atan2                = _const(ops.Atan2)
    Tanh                 = _const(ops.Tanh)
    Atanh                = _const(ops.Atanh)
    Log                  = _const(ops.Log)
    Log2                 = _const(ops.Log2)
    Log10                = _const(ops.Log10)
    Log1p                = _const(ops.Log1p)
    Exp                  = _const(ops.Exp)
    Exp2                 = _const(ops.Exp2)
    Expm1                = _const(ops.Expm1)
    Floor                = _const(ops.Floor)
    Ceil                 = _const(ops.Ceil)
    Abs                  = _const(ops.Abs)
    Erfc                 = _const(ops.Erfc)
    Rint                 = _const(ops.Rint)
    Pow                  = _const(ops.Pow)
    Round                = _const(ops.Round)
    alloca               = _op(ops.alloca)
    load                 = _op(ops.load)
    store                = _op(ops.store)
    map                  = _op(ops.map)
    reduce               = _op(ops.reduce)
    filter               = _op(ops.filter)
    scan                 = _op(ops.scan)
    zip                  = _op(ops.zip)
    allpairs             = _op(ops.allpairs)
    flatten              = _op(ops.flatten)
    print_               = _op(ops.print_)
    concat               = _op(ops.concat)
    length               = _op(ops.length)
    contains             = _op(ops.contains)
    list_append          = _op(ops.list_append)
    list_pop             = _op(ops.list_pop)
    set_add              = _op(ops.set_add)
    set_remove           = _op(ops.set_remove)
    dict_add             = _op(ops.dict_add)
    dict_remove          = _op(ops.dict_remove)
    dict_keys            = _op(ops.dict_keys)
    dict_values          = _op(ops.dict_values)
    dict_items           = _op(ops.dict_items)
    box                  = _op(ops.box)
    unbox                = _op(ops.unbox)
    convert              = _op(ops.convert)
    new_list             = _op(ops.new_list)
    new_tuple            = _op(ops.new_tuple)
    new_dict             = _op(ops.new_dict)
    new_set              = _op(ops.new_set)
    new_string           = _op(ops.new_string)
    new_unicode          = _op(ops.new_unicode)
    new_object           = _op(ops.new_object)
    new_struct           = _op(ops.new_struct)
    new_complex          = _op(ops.new_complex)
    new_data             = _op(ops.new_data)
    phi                  = _op(ops.phi)
    exc_setup            = _op(ops.exc_setup)
    exc_catch            = _op(ops.exc_catch)
    jump                 = _op(ops.jump)
    cbranch              = _op(ops.cbranch)
    exc_throw            = _op(ops.exc_throw)
    ret                  = _op(ops.ret)
    function             = _op(ops.function)
    partial              = _op(ops.partial)
    call                 = _op(ops.call)
    call_virtual         = _op(ops.call_virtual)
    call_math            = _op(ops.call_math)
    ptrload              = _op(ops.ptrload)
    ptrstore             = _op(ops.ptrstore)
    ptrcast              = _op(ops.ptrcast)
    ptr_isnull           = _op(ops.ptr_isnull)
    getiter              = _op(ops.getiter)
    next                 = _op(ops.next)
    yieldval             = _op(ops.yieldval)
    getfield             = _op(ops.getfield)
    setfield             = _op(ops.setfield)
    getindex             = _op(ops.getindex)
    setindex             = _op(ops.setindex)
    getslice             = _op(ops.getslice)
    setslice             = _op(ops.setslice)
    slice                = _op(ops.slice)
    add                  = _op(ops.add)
    sub                  = _op(ops.sub)
    mul                  = _op(ops.mul)
    div                  = _op(ops.div)
    floordiv             = _op(ops.floordiv)
    mod                  = _op(ops.mod)
    lshift               = _op(ops.lshift)
    rshift               = _op(ops.rshift)
    bitand               = _op(ops.bitand)
    bitor                = _op(ops.bitor)
    bitxor               = _op(ops.bitxor)
    and_                 = _op(ops.and_)
    invert               = _op(ops.invert)
    not_                 = _op(ops.not_)
    uadd                 = _op(ops.uadd)
    usub                 = _op(ops.usub)
    eq                   = _op(ops.eq)
    noteq                = _op(ops.noteq)
    lt                   = _op(ops.lt)
    lte                  = _op(ops.lte)
    gt                   = _op(ops.gt)
    gte                  = _op(ops.gte)
    is_                  = _op(ops.is_)
    make_cell            = _op(ops.make_cell)
    load_cell            = _op(ops.load_cell)
    store_cell           = _op(ops.store_cell)
    threadpool_start     = _op(ops.threadpool_start)
    threadpool_submit    = _op(ops.threadpool_submit)
    threadpool_join      = _op(ops.threadpool_join)
    threadpool_close     = _op(ops.threadpool_close)
    thread_start         = _op(ops.thread_start)
    thread_join          = _op(ops.thread_join)
    check_overflow       = _op(ops.check_overflow)
    load_vtable          = _op(ops.load_vtable)
    vtable_lookup        = _op(ops.vtable_lookup)
    gc_gotref            = _op(ops.gc_gotref)
    gc_giveref           = _op(ops.gc_giveref)
    gc_incref            = _op(ops.gc_incref)
    gc_decref            = _op(ops.gc_decref)
    gc_alloc             = _op(ops.gc_alloc)
    gc_dealloc           = _op(ops.gc_dealloc)
    gc_collect           = _op(ops.gc_collect)
    gc_write_barrier     = _op(ops.gc_write_barrier)
    gc_read_barrier      = _op(ops.gc_read_barrier)
    gc_traverse          = _op(ops.gc_traverse)