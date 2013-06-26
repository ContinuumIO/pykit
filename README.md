pykit
=====

Backend compiler for high-level typed code with first-class support for
multi-dimensional arrays, objects, complex numbers, list tuples and dicts,
higher-order functions and sum/union-types.

Pykit tries to address an ever-growing number of compilers in the Python
community, with a focus on array-oriented numerical code.

pykit:

    * lowers and optimizes intermediate code
    * produces IR that can be mapped to any desired runtime
    * tries to be independent from platform or high-level language
    * can generate LLVM or C89 out of the box

pykit is inspired by VMKit and LLVM.

Why not LLVM IR
===============

Why not directly use LLVM IR for the internal format? There are pros and
cons to doing that, below are some reasons why not to:

    * Completeness, we can encode all high-level constructs directly in
      the way we wish, without naming schemes, LLVM metadata, or external
      data
    * Instruction polymorphism the way we want it
    * High-level types, such as arrays, complex numbers, objects, partial
      functions etc, without opague type mappings
    * Simple arbitrary metadata through a key/value mechanism
    * A linker that isn't botched
    * No aborting, ever