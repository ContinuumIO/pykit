# -*- coding: utf-8 -*-

"""
Invoke the code generator for each function in the call graph. This makes
sure each function is "initialized" (e.g. has a C declaration or a dummy
LLVM function, etc).
"""

from pykit.analysis import callgraph

def code_generation(func, env, codegen=None):
    """
    Invoke the code generator after initializing all functions in the call graph
    """
    codegen = codegen or env["codegen.impl"]
    cache = env["codegen.cache"]

    graph = callgraph.callgraph(func)

    for callee in graph.node:
        if callee not in cache:
            cache[callee] = codegen.initialize(callee, env)

    # TODO: Different environments for each function?
    results = {}
    for callee in graph.node:
        results[callee] = codegen.translate(callee, env, cache[callee])

    return results[func], env

run = code_generation