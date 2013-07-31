# -*- coding: utf-8 -*-

"""
Convenience IR builder.
"""

from __future__ import print_function, division, absolute_import
from contextlib import contextmanager

from pykit import types, config
from pykit.ir import Value, Op, Block, Const, Undef, ops, findop
from pykit.ir.verification import op_verifier
from pykit.utils import flatten

def make_arg(arg):
    """Return the virtual register or the result"""
    return arg.result if isinstance(arg, (Op, Block)) else arg


class OpBuilder(object):
    """
    I know how to build Operations.
    """

    def _op(op):
        """Helper to create Builder methods"""
        def _process(self, ty, args=None, result=None, **metadata):
            if args is None:
                args = []
            assert ty is not None
            assert isinstance(args, list), args
            assert not any(arg is None for arg in flatten(args)), args
            result = Op(op, ty, args, result)
            if metadata:
                result.add_metadata(metadata)
            self._insert_op(result)
            return result

        def _process_void(self, *args, **kwds):
            result = kwds.pop('result', None)
            op = _process(self, types.Void, list(args), result)
            if kwds:
                op.add_metadata(kwds)
            return op

        if ops.is_void(op):
            build_op = _process_void
        else:
            build_op = _process

        if config.op_verify:
            build_op = op_verifier(build_op)

        return build_op

    def _insert_op(self, op):
        """Implement in subclass that emits Operations"""

    _const = lambda val: Const(val, types.Void)

    # __________________________________________________________________
    # IR constructors

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
    new_struct           = _op(ops.new_struct)
    new_complex          = _op(ops.new_complex)
    new_data             = _op(ops.new_data)
    new_exc              = _op(ops.new_exc)
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
    mod                  = _op(ops.mod)
    lshift               = _op(ops.lshift)
    rshift               = _op(ops.rshift)
    bitand               = _op(ops.bitand)
    bitor                = _op(ops.bitor)
    bitxor               = _op(ops.bitxor)
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
    check_error          = _op(ops.check_error)
    addressof            = _op(ops.addressof)
    load_vtable          = _op(ops.load_vtable)
    vtable_lookup        = _op(ops.vtable_lookup)
    exc_matches          = _op(ops.exc_matches)
    gc_gotref            = _op(ops.gc_gotref)
    gc_giveref           = _op(ops.gc_giveref)
    gc_incref            = _op(ops.gc_incref)
    gc_decref            = _op(ops.gc_decref)
    gc_alloc             = _op(ops.gc_alloc)
    gc_dealloc           = _op(ops.gc_dealloc)

    def convert(self, type, args, result=None, buildop=convert):
        if type == args[0].type:
            return args[0]
        return buildop(self, type, args, result)

class Builder(OpBuilder):
    """
    I build Operations and emit them into the function.

    Also provides convenience operations, such as loops, guards, etc.
    """

    def __init__(self, func):
        self.func = func
        self.temp = func.temp
        self.module = func.module
        self._curblock = None
        self._lastop = None

    def emit(self, op):
        """
        Emit an Operation at the current position.
        Sets result register if not set already.
        """
        assert self._curblock, "Builder is not positioned!"

        if op.result is None:
            op.result = self.func.temp()

        if self._lastop == 'head' and self._curblock.ops.head:
            op.insert_before(self._curblock.ops.head)
        elif self._lastop in ('head', 'tail'):
            self._curblock.append(op)
        else:
            op.insert_after(self._lastop)
        self._lastop = op

    def _insert_op(self, op):
        if self._curblock:
            self.emit(op)

    # __________________________________________________________________
    # Positioning

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

    def gen_call_external(self, fname, args, result=None):
        """Generate call to external function (which must be declared"""
        gv = self.module.get_global(fname)

        assert gv is not None, "Global %s not declared" % fname
        assert gv.type.is_function, gv
        assert gv.type.argtypes == [arg.type for arg in args]

        op = self.call(gv.type.res, [Const(fname), args])
        op.result = result or op.result
        return op

    def _find_handler(self, exc, exc_setup):
        """
        Given an exception and an exception setup clause, generate
        exc_matches() checks
        """
        catch_sites = [findop(block, 'exc_catch') for block in exc_setup.args]
        for exc_catch in catch_sites:
            for exc_type in exc_catch.args:
                with self.if_(self.exc_matches(types.Bool, [exc, exc_type])):
                    self.jump(exc_catch.block)
                    block = self._curblock
                self.position_at_end(block)

    def gen_error_propagation(self, exc=None):
        """
        Propagate an exception. If `exc` is not given it will be loaded
        to match in 'except' clauses.
        """
        assert self._curblock

        block = self._curblock
        exc_setup = findop(block.leaders, 'exc_setup')
        if exc_setup:
            exc = exc or self.load_tl_exc(types.Exception)
            self._find_handler(exc, exc_setup)
        else:
            self.gen_ret_undef()

    def gen_ret_undef(self):
        """Generate a return with undefined value"""
        type = self.func.type.restype
        if type.is_void:
            self.ret(None)
        else:
            self.ret(Undef(type))

    def splitblock(self, name=None, terminate=False):
        """Split the current block, returning (old_block, new_block)"""
        newblock = self.func.add_block(name or 'block', after=self._curblock)
        op = self._lastop

        # Terminate if requested and not done already
        if terminate and not ops.is_terminator(op):
            op = self.jump(newblock)

        if op:
            # Move any tailing Ops...
            if op == 'head':
                trailing = list(op.block.ops)
            elif op == 'tail':
                trailing = []
            else:
                trailing = list(op.block.ops.iter_from(op))[1:]

            for op in trailing:
                op.unlink()
            newblock.extend(trailing)

        return self._curblock, newblock

    def if_(self, cond):
        """with b.if_(b.eq(a, b)): ..."""
        old, exit = self.splitblock()
        if_block = self.func.add_block("if_block", after=self._curblock)
        self.cbranch(cond, if_block, exit)
        return self.at_end(if_block)

    def ifelse(self, cond):
        old, exit = self.splitblock()
        if_block = self.func.add_block("if_block", after=self._curblock)
        el_block = self.func.add_block("else_block", after=if_block)
        self.cbranch(cond, if_block, el_block)
        return self.at_end(if_block), self.at_end(el_block), exit

    def gen_loop(self, start=None, stop=None, step=None):
        """
        Generate a loop given start, stop, step and the index variable type.
        The builder's position is set to the end of the body block.

        Returns (condition_block, body_block, exit_block).
        """
        assert isinstance(stop, Value), "Stop should be a Constant or Operation"

        ty = stop.type
        start = start or Const(0, ty)
        step  = step or Const(1, ty)
        assert start.type == ty == step.type

        with self.at_front(self.func.startblock):
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
