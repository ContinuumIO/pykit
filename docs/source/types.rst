Pykit Types
===========

Pykit supports the following types:

    * Containers: tuples, lists, dicts, sets, N-dimensional arrays
    * Complex numbers
    * Objects (a Python object)
    * Functions and Partial functions
    * Integral and real numbers
    * Structs and Unions
    * Pointers
    * String and Unicode
    * Char and Unicode codepoints
    * Sum type (e.g. Int | Float)
    * Cell types (for closures)

Additionally, pykit supports the notion of a Typedef, which allows a type to be
declared and used now, but resolved later::

    Int = Typedef("Int", Int32)

Above we specify that an ``Int`` type is *like* an ``Int32``, but we don't
fix this representation. This allows the IR to retain portability to a later
stage (or all the way to e.g. C code). It also allows for the creation of a
unique type that external code keeps track of, e.g.

    MyExtensionObject = Typedef("MyExtensionObject", Object)

    obj = new_object(MyExtensionObject)
    call_virtual(obj, "mymethod", [Constant(10, Int)])

A later pass from the user can then determine that ``obj`` is of type
``MyExtensionObject``, and resolve a virtual method call accordingly.