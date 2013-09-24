# -*- coding: utf-8 -*-

"""
Invoke the code generator for each function in the call graph. This makes
sure each function is "initialized" (e.g. has a C declaration or a dummy
LLVM function, etc).
"""

from pykit.analysis import callgraph

def run(func, env, codegen=None):
    """
    Invoke the code generator after initializing all functions in the call graph
    """
    codegen = codegen or env["codegen.impl"]

    graph = callgraph.callgraph(func)

    initialized = {}
    for callee in graph.node:
        initialized[callee] = codegen.initialize(callee, env)

    # TODO: Caching!!
    # TODO: Different environments for each function?
    results = {}
    for callee in graph.node:
        results[callee] = codegen.translate(callee, env, initialized[callee])

    return results[func], env