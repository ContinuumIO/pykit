# -*- coding: utf-8 -*-

"""
Dead code elimination.
"""

from pykit.analysis import loop_detection

effect_free = set([
    'alloca', 'load', 'new_list', 'new_tuple', 'new_dict', 'new_set',
    'new_struct', 'new_data', 'new_exc', 'phi', 'exc_setup', 'exc_catch',
    'ptrload', 'ptrcast', 'ptr_isnull', 'getfield', 'getindex',
    'add', 'sub', 'mul', 'div', 'mod', 'lshift', 'rshift', 'bitand', 'bitor',
    'bitxor', 'invert', 'not_', 'uadd', 'usub', 'eq', 'noteq', 'lt', 'lte',
    'gt', 'gte', 'is_', 'addressof',
])

def dce(func, env=None):
    """
    Eliminate dead code.

    TODO: Prune branches, dead loops
    """
    for op in func.ops:
        if op.opcode in effect_free and len(func.uses[op]) == 0:
            op.delete()

run = dce