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