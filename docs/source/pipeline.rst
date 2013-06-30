Pykit pipeline
==============

The input to pykit is a typed program in the form of a Module, consisting of
a set of functions, global variables and external symbols.

The functions within the module go through successive transformations or
stages defined by the pipeline. We can categorize stages as follows
(similar to parakeet):

    * High-level optimizations and analyses
    * Lowering and scalarization
    * Codegen

Every stage in the pipeline is optional. The order is configurable. Entire
stages can be skipped or overridden.


High-level Optimizations and Analyses
-------------------------------------

Transformations:

    * SSA/mem2reg
    * Transform unary/binary operations on arrays to map
    * fusion of map/reduce/scan

Optimizations and analyses include:

    * (sparse conditional) constant propagation
    * Container vectorization (``list_append -> map``)
    * Purity analysis
    * Escape analysis
    * Partial redundancy elimination
    * Scalar replacement
    * Bounds check, wrap around, None check elimination
    * Optimize cell variables with static binding
    * Loop fusion (temporary elimination)
    * Inlining
    * Exception analysis

We need to perform these analyses on high-level code, since subsequent
lowering transformations will reduce or preclude the effectiveness.

For example optimizations pykit should do, see :ref:`optimizations`.

.. _lowering:

Lowering and Specialization
---------------------------

These stages specialize to a type representation and a runtime. Default
stages lower to a provided pykit :ref:`runtime`.

    * Scalarization ``map -> for``
    * Expand sum type operations
    * Data and object allocation (based on escape analysis)
    * Lower container operations
    * Lower Thread API into runtime calls
    * Lower cell variable allocation and storage/loading
    * Lower type conversion...

        * Internal representation
        * CPython C API

    * Lower object operations

        * CPython C API
        * Some user pass
        * Error

    * Lower virtual method calls / virtual attribute access

        * Actual vtable lookup should be deferred to a user provided pass

    * Refcounting or GC pass
    * Lower exception handling code

        * zero cost
        * setjmp/longjump
        * error return codes


Codegen
-------

The code is in a low-level format by now, and can be easily used to generate
code from. We are left with:

    * Scalars operations (int, float, pointer, function)
    * Aggregate accesses (struct, union)
    * Scalar conversions and pointer casts
    * Memory operations (load, store)
    * Control flow (branch, conditional branch, return, exceptions)
    * Function calls
    * phi
    * Constants