# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

import string
import functools
import collections
from itertools import chain

map    = lambda *args: list(builtins.map(*args))
invert = lambda d: dict((v, k) for k, v in d.items())

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

def mergedicts(*dicts):
    """Merge all dicts into a new dict"""
    return dict(chain(*[d.items() for d in dicts]))

def listify(f):
    """Decorator to turn generator results into lists"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return list(f(*args, **kwargs))
    return wrapper

@listify
def prefix(iterable, prefix):
    """Prefix each item from the iterable with a prefix"""
    for item in iterable:
        yield prefix + item

# ______________________________________________________________________
# Strings

def substitute(s, **substitutions):
    """Use string.Template to substitute placeholders in a string"""
    return string.Template(s).substitute(**substitutions)

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

# ______________________________________________________________________

def cached(f):
    """Cache the result of the function"""
    result = []
    def wrapper(*args, **kwargs):
        if len(result) == 0:
            ret = f(*args, **kwargs)
            result.append(ret)

        return result[0]
    return wrapper

call_once = cached

# ______________________________________________________________________

def make_temper():
    """Return a function that returns temporary names"""
    temps = collections.defaultdict(int)

    def temper(name=""):
        varname = name.rstrip(string.digits)
        count = temps[varname]
        temps[varname] += 1
        if varname and count == 0:
            return varname
        return varname + str(count)

    return temper

# ______________________________________________________________________
