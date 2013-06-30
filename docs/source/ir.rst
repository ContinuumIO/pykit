Pykit IR
========

The pykit IR is a linear N-address code delineated through basic blocks,
analogously to LLVM IR. It defines a set of opcodes, which specify what
an operation does. Opcodes range from high-level such as container operations,
to low-level operations such as pointer stores. Each operation has a type,
and implicit coercions do not exists. Instead coercions need explicit
conversions.

Similarly to LLVM pykit comes with an ``alloca`` instruction that allocates
an object on the stack, such as a scalar or a small array. The resulting
pointer can be loaded and stored to.

Pykit uses SSA, and can promote stack allocated scalars to virtual registers
and remove the load and store operations, allowing better optimizations
since values propagate directly to their use sites.

All opcodes are defined in ``pykit.ir.ops``. Below follows a summary and
rationale.

Control Flow
------------

Control flow is supported through through ``jump``, ``cbranch`` and ``ret``.
Additionally, ``phi`` merges different incoming values or definitions from
predecessor basic blocks.

Exceptions are supported through ``exc_setup``, ``exc_catch`` and
``exc_throw``.

    * ``exc_setup``: marks the exception handlers for the basic block
    * ``exc_catch``: specifies which exceptions this basic block can handle
    * ``exc_throw``: raises an exception

The implementation is pluggable (costful/zero-cost, etc), and these opcodes
are entirely optional. More on this can be read here: :ref:`lowering`.

Primitives
----------

Like parakeet and copperhead, pykit has high-level data parallel operators,
such as ``map``, ``reduce``, ``filter``, ``scan``, ``zip``, and ``allpairs``
are provided for arrays and lists. This allows
optimizations such as fusion and parallelization before scalarization takes
place.

Containers
----------

Lists, dicts, tuples and sets are supported. Basic operations are provided
in the IR, and additional operations are deferred to calls to a runtime.
The opcodes provided are there only since they expose hints for optimizations,
see :ref:`container_opt`.

Indexing and Slicing
--------------------

Indexing is supported for containers (including arrays) and pointers.
Slicing is supported for tuples, lists and arrays. Newaxis is supported
for arrays.

Attributes
----------

Attributes are supported through ``getfield`` and ``setfield`` for objects
and structs.

Conversion
----------

The ``convert`` opcode converts its argument to the destination type.

Iterators
---------

Supported through ``iter`` and ``next`` on arrays, flattened arrays, lists,
sets, dict keys, dict values and dict items.

Functions
---------

Pykit considers external and defined functions to be functions. These can
be called through the ``call`` opcode. Additionally, pykit supports partial
functions, which are also functions. Only these functions may be passed to
``map`` etc, or used in ``phi`` instructions (if the signatures are compatible).

Math is supported through ``call_math``, since the functions have polymorphic
signatures (real or complex). Math functions take a constant function name as
first argument. These are defined in ``ops.py``.

Note that pykit does not support keyword arguments. A front-end can however
handle this statically if possible, or otherwise rewrite the signature to
take an explicit dictionary as argument if so desired (and star arguments
through an explicit tuple).

Closures
--------

Pykit assumes closure conversion and lambda lifting has taken place. For
dynamic binding of call variables it provides cell objects through
``make_cell``, ``load_cell` and ``store_cell``.

Pointers
--------

Supported pointer operations are ``add``, ``ptrload`` and ``ptrstore``.
``ptrcast`` casts the pointer to another pointer (this is distinguished from
a data conversion).

Threads
-------

Supported are thread pools and individual threads.