# -*- coding: utf-8 -*-

"""
Pipeline that determines phase ordering and execution.
"""

from __future__ import print_function, division, absolute_import
import types

cpy = {
    'lower_convert': lower_convert,
}

lower = {

}

# ______________________________________________________________________
# Execute pipeline

def apply_transform(transform, func, env):
    if isinstance(transform, types.ModuleType):
        return transform.run(func, env)
    else:
        return transform(func, env)

def run(transforms, order, func, env):
    for transform in order:
        if transform in transforms:
            func, env = apply_transform(transforms[transform], func, env)