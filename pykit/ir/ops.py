from __future__ import print_function, division, absolute_import
import collections

try:
    intern
except NameError:
    intern = lambda s: s

#===------------------------------------------------------------------===
# Syntax
#===------------------------------------------------------------------===

all_ops = []
op_syntax = {} # Op -> Syntax

List  = collections.namedtuple('List',  []) # syntactic list
Value = collections.namedtuple('Value', []) # single Value
Const = collections.namedtuple('Const', []) # syntactic constant
Any   = collections.namedtuple('Any',   []) # Value | List
Star  = collections.namedtuple('Star',  []) # any following arguments
Obj   = collections.namedtuple('Obj',   []) # any object

fmts = {'l': List, 'v': Value, 'c': Const, 'a': Any, '*': Star, 'o': Obj}

# E.g. op('foo', List, Const, Value, Star) specificies an opcode 'foo' accepting
# as the argument list a list of arguments, a constant, an operation and any
# trailing arguments. E.g. [[], Const(...), Op(...)] would be valid.

def op(name, *args):
    if '/' in name:
        name, fmt = name.split('/')
        args = [fmts[c] for c in fmt]

    name = intern(name)
    all_ops.append(name)
    op_syntax[name] = list(args)
    return name

#===------------------------------------------------------------------===
# Typed IR (initial input)
#===------------------------------------------------------------------===

# IR Constants. Constants start with an uppercase letter

# math
Sin                = 'Sin'
Asin               = 'Asin'
Sinh               = 'Sinh'
Asinh              = 'Asinh'
Cos                = 'Cos'
Acos               = 'Acos'
Cosh               = 'Cosh'
Acosh              = 'Acosh'
Tan                = 'Tan'
Atan               = 'Atan'
Atan2              = 'Atan2'
Tanh               = 'Tanh'
Atanh              = 'Atanh'
Log                = 'Log'
Log2               = 'Log2'
Log10              = 'Log10'
Log1p              = 'Log1p'
Exp                = 'Exp'
Exp2               = 'Exp2'
Expm1              = 'Expm1'
Floor              = 'Floor'
Ceil               = 'Ceil'
Abs                = 'Abs'
Erfc               = 'Erfc'
Rint               = 'Rint'
Pow                = 'Pow'
Round              = 'Round'

# ______________________________________________________________________
# Constants

constant           = op('constant/o')         # object pyval

# ______________________________________________________________________
# Variables

alloca             = op('alloca/')
load               = op('load/v')             # alloc var
store              = op('store/vv')           # expr value, alloc var
# phi is below

# ______________________________________________________________________
# Primitives

# Arrays/lists
map                = op('map/vlc')            # fn func, expr *arrays, const axes
reduce             = op('reduce/vvc')         # fn func, expr array, const axes
filter             = op('filter/vv')          # fn func, expr array
scan               = op('scan/vvc')           # fn func, expr array, const axes
zip                = op('zip/l')              # expr *arrays
allpairs           = op('allpairs/vvc')       # fn func, expr array, const axes
flatten            = op('flatten/v')          # expr array

print              = op('print/v')            # expr value

# ______________________________________________________________________
# Containers

# Arrays/lists/tuples/sets/dicts
concat             = op('concat/l')           # expr *values
length             = op('length/v')           # expr value
contains           = op('contains/vv')        # expr item, expr container

list_append        = op('list_append/vv')     # expr list, expr item
list_pop           = op('list_pop/v')         # expr list

set_add            = op('set_add/vv')         # expr set, expr value
set_remove         = op('set_remove/vv')      # expr set, expr value

dict_add           = op('dict_add/vvv')       # expr dict, expr key, expr value
dict_remove        = op('dict_remove/vv')     # expr dict, expr key
dict_keys          = op('dict_keys/v')        # expr dict
dict_values        = op('dict_values/v')      # expr dict
dict_items         = op('dict_items/v')       # expr dict

# ______________________________________________________________________
# Conversion

box                = op('box/v')              # expr arg
unbox              = op('unbox/v')            # expr arg
convert            = op('convert/v')          # expr arg

# ______________________________________________________________________
# Constructors

new_list           = op('new_list/l')         # expr *elems
new_tuple          = op('new_tuple/l')        # expr *elems
new_dict           = op('new_dict/ll')        # expr *keys, expr *values
new_set            = op('new_set/l')          # expr *elems

new_struct         = op('new_struct/l')       # expr *initializers
new_data           = op('new_data/v')         # expr size
new_exc            = op('new_exc/v*')         # str exc_name, expr *args

# ______________________________________________________________________
# Control flow

# Basic block leaders
phi                = op('phi/ll')             # expr *blocks, expr *values
exc_setup          = op('exc_setup/l')        # block *handlers
exc_catch          = op('exc_catch/l')        # expr *types

# Basic block terminators
jump               = op('jump/v')             # block target
cbranch            = op('cbranch/vvv')        # expr test, block true_target, block false_target)
exc_throw          = op('exc_throw/v')        # expr exc
ret                = op('ret/o')              # expr result

# ______________________________________________________________________
# Functions

function           = op('function/o')         # str funcname
call               = op('call/v*')            # expr obj, expr *args
call_math          = op('call_math/ol')       # str name, expr *args

# ______________________________________________________________________
# Pointers

ptradd             = op('ptradd/vv')          # expr pointer, expr value
ptrload            = op('ptrload/v')          # expr pointer
ptrstore           = op('ptrstore/vv')        # expr pointer, expr value
ptrcast            = op('ptrcast/v')          # expr pointer
ptr_isnull         = op('ptr_isnull/v')       # expr pointer

# ______________________________________________________________________
# Attributes

getfield           = op('getfield/vo')        # (expr value, str attr)
setfield           = op('setfield/vov')       # (expr value, str attr, expr value)

# ______________________________________________________________________
# Indexing

getindex           = op('getindex/vl')        # (expr value, expr *indices)
setindex           = op('setindex/vlv')       # (expr value, expr *indices, expr value)
getslice           = op('getslice/vl')        # (expr value, expr *indices)
setslice           = op('setslice/vlv')       # (expr value, expr *indices, expr value)

slice              = op('slice/vvv')          # (expr lower, expr upper, expr step)
# newaxis            = 'newaxis'        # => const(None) ?

# ______________________________________________________________________
# Basic operators

# Binary
add                = op('add/vv')
sub                = op('sub/vv')
mul                = op('mul/vv')
div                = op('div/vv')
mod                = op('mod/vv')
lshift             = op('lshift/vv')
rshift             = op('rshift/vv')
bitand             = op('bitand/vv')
bitor              = op('bitor/vv')
bitxor             = op('bitxor/vv')

# Unary
invert             = op('invert/v')
not_               = op('not_/v')
uadd               = op('uadd/v')
usub               = op('usub/v')

# Compare
eq                 = op('eq/vv')
noteq              = op('noteq/vv')
lt                 = op('lt/vv')
lte                = op('lte/vv')
gt                 = op('gt/vv')
gte                = op('gte/vv')
is_                = op('is_/vv')

# ______________________________________________________________________
# Threads

threadpool_start   = op('threadpool_start/v')    # expr nthreads
threadpool_submit  = op('threadpool_submit/vvl') # expr threadpool, fn function, expr *args
threadpool_join    = op('threadpool_join/v')     # expr threadpool
threadpool_close   = op('threadpool_close/v')    # expr threadpool
thread_start       = op('thread_start/vl')       # fn function, expr *args
thread_join        = op('thread_join/v')         # expr thread

# ______________________________________________________________________
# Debugging

print              = op('print/v')

#===------------------------------------------------------------------===
# Low-level IR
#===------------------------------------------------------------------===

# Low-level result:
#   - no objects, arrays, complex numbers
#   - no builtins
#   - no frames
#   - no map, reduce, scan, or yield

check_overflow     = op('check_overflow/v')     # expr arg
check_error        = op('check_error/vo')       # expr result, expr? badval

addressof          = op('addressof/v')          # fn func

exc_matches        = op('exc_matches/vv')       # expr exc, expr matcher
store_tl_exc       = op('store_tl_exc/v')       # expr exc
load_tl_exc        = op('load_tl_exc/')

# ______________________________________________________________________
# Garbage collection

# Refcounting
gc_gotref          = op('gc_gotref/v')        # expr arg
gc_giveref         = op('gc_giveref/v')       # expr arg
gc_incref          = op('gc_incref/v')        # expr obj
gc_decref          = op('gc_decref/v')        # expr obj

# GC
gc_alloc           = op('gc_alloc/v')         # expr n
gc_dealloc         = op('gc_dealloc/v')       # expr value

# ______________________________________________________________________
# Opcode utils

import fnmatch

void_ops = (print, store, store_tl_exc, check_overflow, check_error)

is_leader     = lambda x: x in (phi, exc_setup, exc_catch)
is_terminator = lambda x: x in (jump, cbranch, exc_throw, ret)
is_void       = lambda x: is_terminator(x) or x in void_ops

def oplist(pattern):
    """Given a pattern, return all matching opcodes, e.g. thread_*"""
    for name, value in globals().iteritems():
        if not name.startswith('__') and fnmatch.fnmatch(name, pattern):
            yield value
