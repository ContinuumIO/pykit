FAQ
===

Why this project?
-----------------

The motivation for this project is an ever growing number of compilers for
Python out there. Pykit tries to provide a higher-level layer than LLVM
or C for typed Python code, focussing on numeric code, so that optimizations
and runtime improvements benefit everyone.

It aims to be reusable for projects including:

    * Numba
    * Parakeet
    * Pythran
    * Theano
    * NumbaPro
    * Your next awesome compiler

If something in pykit somehow precludes reuse in any of the above projects,
then pykit has failed and we need to fix that.

Why not LLVM IR?
----------------

Why not directly use LLVM IR for the internal format? There are pros and
cons to doing that, below are some reasons why not to:

    * Completeness, we can encode all high-level constructs directly in
      the way we wish, without naming schemes, LLVM metadata, or external
      data
    * Instruction polymorphism the way we want it
    * High-level types, such as arrays, complex numbers, objects, partial
      functions etc, without opague type mappings
    * Simple arbitrary metadata through a key/value mechanism
    * No aborting, ever