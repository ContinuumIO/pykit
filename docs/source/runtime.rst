.. _runtime:

Pykit Runtime
=============

Pykit comes with a default runtime, that supports the following:

    * Boxed structures with an internal format

        - (atomically) reference counted or GCed

    * Conversion between internal representations and Python objects
    * A portable thread API
    * A memory allocator

All these parts are optional and can be ignored. For instance one can
disallow dynamic memory allocation, or provide a different implementation
simply by writing a different lowering pass or linking with a different
library exposing the same API.