#===------------------------------------------------------------------===
# Typed IR (initial input)
#===------------------------------------------------------------------===

# IR Constants

# operator
add                = 'add'
sub                = 'sub'
mult               = 'mult'
div                = 'div'
mod                = 'mod'
pow                = 'pow'
lshift             = 'lshift'
rshift             = 'rshift'
bitor              = 'bitor'
bitxor             = 'bitxor'
bitand             = 'bitand'
floordiv           = 'floordiv'

# unaryop
invert             = 'invert'
not_               = 'not'
uadd               = 'uadd'
usub               = 'usub'

# cmpop
eq                 = 'eq'
noteq              = 'noteq'
lt                 = 'lt'
lte                = 'lte'
gt                 = 'gt'
gte                = 'gte'
is_                = 'is'
isnot              = 'isnot'
in_                = 'in'
notin              = 'notin'

# builtins
min                = 'min'
max                = 'max'

# math
sin                = ' sin '
asin               = ' asin '
sinh               = ' sinh '
asinh              = ' asinh'
cos                = ' cos '
acos               = ' acos '
cosh               = ' cosh '
acosh              = ' acosh'
tan                = ' tan '
atan               = ' atan '
atan2              = ' atan2 '
tanh               = ' tanh '
atanh              = ' atanh'
log                = ' log '
log2               = ' log2 '
log10              = ' log10 '
log1p              = ' log1p'
exp                = ' exp '
exp2               = ' exp2 '
expm1              = ' expm1'
floor              = ' floor '
ceil               = ' ceil '
abs                = ' abs '
erfc               = ' erfc '
rint               = ' rint'
pow                = ' pow '
round              = ' round'

# ______________________________________________________________________

# coerce
box                = 'box'              # (expr arg)
unbox              = 'unbox'            # (expr arg)
convert            = 'convert'          # (expr arg)

# ctor
new_list           = 'new_list'         # (expr elems)
new_tuple          = 'new_tuple'        # (expr elems)
new_dict           = 'new_dict'         # (expr keys, expr values)
new_set            = 'new_set'          # (expr elems)
new_string         = 'new_string'       # (expr chars)
new_unicode        = 'new_unicode'      # (expr char)
new_object         = 'new_object'       # (expr args)
new_ext_object     = 'new_ext_object'   # (expr args)
new_struct         = 'new_struct'       # (expr initializers)
new_data           = 'new_data'         # (expr size)
new_complex        = 'new_complex'      # (expr real, expr imag)

# const
constant           = 'constant'         # (object pyval)

# slice_
slice              = 'slice'            # (expr lower, expr upper, expr step)

# Basic block leaders
phi                = 'phi'              # (expr blocks, expr values)
excepthandler      = 'excepthandler'    # (expr *types, str name, str body)

# tail
jump               = 'jump'             # (str target)
cbranch            = 'cbranch'          # (expr test, str true_target,
                                        #  str false_target)
throw              = 'throw'            # (expr exn)
ret                = 'ret'              # (expr result)
setup_exc          = 'setup_exc'        # (str body, excepthandler handlers,
                                        #  str orelse, str finalbody)

# generators
yield_             = 'yield'            # (expr value)
yieldfrom          = 'yieldfrom'        # (expr value)

# Variables
alloca             = 'alloca'           # (expr n)
load               = 'load'             # (alloc var)
store              = 'store'            # (alloc var, expr value)

# element-wise, for objects and arrays
map                = 'map'              # (fn func, expr arrays, const axes)
reduce             = 'reduce'           # (fn func, expr array, const axes)
scan               = 'scan'             # (fn func, expr array, const axes)

# fn
function           = 'function'         # (const func)
partial            = 'partial'          # (fn function, expr vals)
extmethod          = 'extmethod'        # (expr extobj, string methname)
funcaddr           = 'funcaddr'         # (expr pointer)
builtin            = 'builtin'          # (const func)
operator           = 'operator'         # (const op)
# make_closure       = 'make_closure'     # (fn func, frame f) (partial)

# calls
call_obj           = 'call_obj'         # (expr obj)
call_virtual       = 'call_virtual'     # (fn method)
call_external      = 'call_external'    # (str name)
call_math          = 'call_math'        # (str func)
call_func          = 'call_func'        # (fn func)

# pointers
ptradd             = 'ptradd'           # (expr pointer, expr addition)
ptrload            = 'ptrload'          # (expr pointer)
ptrstore           = 'ptrstore'         # (expr pointer, expr value)
ptr_isnull         = 'ptr_isnull'       # (expr pointer)

# iter
getiter            = 'getiter'          # (expr obj)
next               = 'next'             # (iter it)

# fields
getfield_struct    = 'getfield_struct'  # (expr struct, int field_idx)
setfield_struct    = 'setfield_struct'  # (expr struct, int field_idx, expr value)
getfield_obj       = 'getfield_obj'     # (expr obj, string attr)
setfield_obj       = 'setfield_obj'     # (expr obj, string attr, expr value)
getfield_frame     = 'getfield_frame'   # (frame f, string attr)
setfield_frame     = 'setfield_frame'   # (frame f, string attr, expr value)

# indices
getindex_array     = 'getindex_array'   # (expr array, expr indices)
setindex_array     = 'setindex_array'   # (expr array, expr indices, expr value)
getslice_array     = 'getslice_array'   # (expr array, expr indices)
setslice_array     = 'setslice_array'   # (expr array, expr indices, expr value)
getindex_obj       = 'getindex_obj'     # (expr array, expr indices)
setindex_obj       = 'setindex_obj'     # (expr array, expr indices, expr value)

# block
block              = 'block'

# op
compare            = 'compare'          # (expr left, str op, expr right)
binop              = 'binop'            # (expr left, str op, expr right)
unop               = 'unop'             # (str op, expr operand)

# closures
make_activation_fame = 'make_activation_fame' # (frame parent, string names)

# threads
threadpool_start   = 'threadpool_start' # (expr nthreads)
threadpool_join    = 'threadpool_join'  # (expr threadpool)
threadpool_submit  = 'threadpool_submit' # (fn function)
thread_start       = 'thread_start'     # (fn function)
thread_join        = 'thread_join'      # (expr thread)

#===------------------------------------------------------------------===
# Low-level IR
#===------------------------------------------------------------------===

# Low-level result:
#   - no objects, arrays, complex numbers
#   - no builtins
#   - no frames
#   - no map, reduce, scan, or yield

to_object          = 'to_object'        # (expr arg)
from_object        = 'from_object'      # (expr arg)
ptr_to_int         = 'ptr_to_int'       # (expr arg)
int_to_ptr         = 'int_to_ptr'       # (expr arg)

### Garbage collection ###
# Refcounting
gc_gotref          = 'gc_gotref'        # (expr arg)
gc_giveref         = 'gc_giveref'       # (expr arg)
gc_incref          = 'gc_incref'        # (expr obj)
gc_decref          = 'gc_decref'        # (expr obj)

# GC
gc_alloc           = 'gc_alloc'         # (expr n)
gc_dealloc         = 'gc_dealloc'       # (expr value)
gc_collect         = 'gc_collect'
gc_write_barrier   = 'gc_write_barrier'
gc_read_barrier    = 'gc_read_barrier'
gc_traverse        = 'gc_traverse'