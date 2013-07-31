# -*- coding: utf-8 -*-

"""
Pipeline that determines phase ordering and execution.
"""

from __future__ import print_function, division, absolute_import
import types

# ______________________________________________________________________
# Execute pipeline

def _check_transform_result(transform, result):
    if result is not None and not isinstance(result, tuple):
        if isinstance(transform, types.ModuleType):
            transform = transform.run
        transform = transform.__module__ + '.' + transform.__name__
        raise ValueError(
            "Expected (func, env) result in %r, got %s" % (transform, result))


def apply_transform(transform, func, env):
    if isinstance(transform, types.ModuleType):
        result = transform.run(func, env)
    else:
        result = transform(func, env)

    _check_transform_result(transform, result)
    return result or (func, env)

def run(func, env, transforms):
    """Run a sequence of transforms (given as strings) on the function"""
    for transform in transforms:
        if transform not in env or not env[transform]:
            raise ValueError("Transform %r is not installed" % transform)

        result = apply_transform(env[transform], func, env)

        func, env = result
    return func,env

analyze  = lambda func, env: run(func, env, env["pipeline.analyze"])
optimize = lambda func, env: run(func, env, env["pipeline.optimize"])
lower    = lambda func, env: run(func, env, env["pipeline.lower"])
codegen  = lambda func, env: run(func, env, env["pipeline.codegen"])