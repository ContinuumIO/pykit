import __builtin__ as builtins

map    = lambda *args: list(builtins.map(*args))
invert = lambda d: dict((v, k) for k, v in d.iteritems())

def nestedmap(f, args):
    """
    Map `f` over `args`, which contains elements or nested lists
    """
    result = []
    for arg in args:
        if isinstance(arg, list):
            result.append(list(map(f, arg)))
        else:
            result.append(f(arg))

    return result

def flatten(args):
    """Flatten nested lists (return as iterator)"""
    for arg in args:
        if isinstance(arg, list):
            for x in arg:
                yield x
        else:
            yield arg

def mutable_flatten(args):
    """Flatten nested lists (return as iterator)"""
    for arg in args:
        if isinstance(arg, list):
            for x in arg:
                yield x
        else:
            yield arg

# ______________________________________________________________________

def hashable(x):
    try:
        hash(x)
    except TypeError:
        return False
    else:
        return True

# ______________________________________________________________________

class ValueDict(object):
    """
    Use dict values as attributes.
    """

    def __init__(self, d):
        self.__getattr__ = d.__getitem__
        self.__setattr__ = d.__setitem__
        self.__detattr__ = d.__detitem__