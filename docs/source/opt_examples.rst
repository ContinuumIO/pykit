.. _optimizations:

Example Optimizations
=====================

What follows are some example transformations pykit should be able to handle
in the future.

Aggregates
----------

Stack allocation:

.. code-block:: python

    t = x, y, z # escape = { 't': [] }
    # --> (struct converion and stack allocation)
    t = new_struct(x, y, z) # stack allocation through escape info

----------

Stack allocation + Inlining:

.. code-block:: python

    def f(x, y):
        t = g(x), g(y) # escape = { 't': ['return'] }
        return t

    x, y = f(1, 2)

    # --> (struct conversion)

    def f(x, y):
        t = new_struct(g(x), g(y)) # escape = { 't': ['return'] }
        return t                   # inlining beneficial to remove temporary

    x, y = f(1, 2)

    # --> (inlining)

    t = new_struct(g(1), g(2))
    x, y = t

    # --> (redundancy elimination)

    x = g(1)
    y = g(2)

Arrays
------

Element-wise:

.. code-block:: python

    result = A + B * C
    # -->
    map(add, A, map(mul, B, C))
    # --> (fusion)
    map(composed_add_mul, A, B, C)
    # -> map(fma, A, B, C) -- llvm will figure this out

----------

Reductions:

.. code-block:: python

    reduce(add, A + B)
    # -->
    reduce(add, map(add, A, B))
    # -->
    reduce(add_add, [A, B])

----------

Parallelism:

.. code-block:: python

    map(pure_function, A)
    # -->
    parallel_map(pure_function, A)

----------

Order specialization:

.. code-block:: python

    A = ... # order = C
    B = ... # order = F
    A + B
    # -->
    tiled_map(add, A, B)

----------

MKL:

.. code-block:: python

    sqrt(A)
    # -->
    map(sqrt, A)
    # -->
    map(vsSqrt, A[:, ::blocksize])

----------

Bounds checking:

.. code-block:: python

    def swap(A, i):
        t        = A[i]
        A[i]     = A[i + 1]
        A[i + 1] = t

    # --> (add bounds checking)

    def swap(A, i):
        assert 0 <= i < A.shape[0]
        t        = A[i]
        assert 0 <= i + 1 < A.shape[0]
        assert 0 <= i < A.shape[0]
        A[i]     = A[i + 1]
        assert 0 <= i + 1 < A.shape[0]
        A[i + 1] = t

    # --> (elimination)

    def swap(A, i):
        assert 0 <= i
        assert i + 1 < A.shape[0]
        t        = A[i]
        A[i]     = A[i + 1]
        A[i + 1] = t

----------

Wrap-around elimination:

.. code-block:: python

    def swap(A, i):
        t        = A[i]
        A[i]     = A[i + 1]
        A[i + 1] = t

    # --> (add wrap around)

    def swap(A, i):
        idx0 = i if i >= 0 else i + A.shape[0]
        t = A[idx0]

        idx1 = i + 1if i + 1 >= 0 else i + 1 + A.shape[0]
        idx2 = i if i >= 0 else i + A.shape[0]
        A[idx2] = A[idx1]

        idx1 = i + 1 if i + 1 >= 0 else i + 1 + A.shape[0]
        A[i + 1] = t

    # --> (elimination)

    def swap(A, i):
        idx0 = i if i >= 0 else i + A.shape[0]
        idx1 = i + 1 if i + 1 >= 0 else i + 1 + A.shape[0]
        t = A[idx0]
        A[idx0] = A[idx1]
        A[idx1] = t


Containers
----------

List loop fusion:

.. code-block:: python

    L = []
    for i in range(10):
        L.append(i*i)
    for x in L:
        use(x)

    # --> (vectorize)

    L = map(square, range(10))  # lazy=True since square is pure
    for x in L:
        use(x)

    # --> (fusion)

    for i in range(10):
        x = i * i
        use(x)

Or perhaps:

.. code-block:: python

    L = []
    for i in range(10):
        L.append(i*i)
    for x in L:
        use(x)

    # --> (vectorize)

    L = map(square, range(10))  # lazy=True, uses=[_]
    _ = map(use, L)             # lazy=False, uses=[]

    # --> (fusion)

    map(compose(use, square), L) # lazy=is_pure(use)

----------

Redundancy elimination:

.. code-block:: python

    L.append(x)
    y = L.pop()
    # -->
    y = x

----------

Preallocation:

.. code-block:: python

    L = []
    for i in range(N):
        L.append(...)

    # -->

    L = [] # preallocate = N
    for i in range(N):
        L.append(...)

----------

List consumption:

.. code-block:: python

    L = [f(x) for x in lst]
    while L:
        x = L.pop()
        use(x)

    # no further uses of L

    # -->

    L = [f(x) for x in lst]
    for x in reversed(L):
        use(x)

    # --> (if f has no side-effects)

    for tmp in reversed(lst):
        x = f(tmp)
        use(x)

----------

Inlining and fusion:

.. code-block:: python

    def split(str, sep):
        result = []
        begin = 0
        end = 0

        while end < len(str):
            end = find(str, sep, begin)
            if end == -1:
                end = len(str)
            result.append(str[begin:end])
            begin = end + len(sep)

        return result # escape={'result': ['return'], 'str': ['find', 'len']}

    def somefunc(str):
        for part in split(str, " "): # inlining beneficial to remove temporary
            use(part)

    # --> (inlining)

    def somefunc(str):
        result = []
        begin = 0
        end = 0

        while end < len(str):
            end = find(str, sep, begin)
            if end == -1:
                end = len(str)
            result.append(str[begin:end])
            begin = end + len(sep)

        for part in result:
            use(part)

    # --> (fusion)

    def somefunc(str):
        result = []
        begin = 0
        end = 0

        while end < len(str):
            end = find(str, sep, begin)
            if end == -1:
                end = len(str)
            tmp = str[begin:end]
            begin = end + len(sep)

            part = tmp
            use(part)

----------