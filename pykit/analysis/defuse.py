# -*- coding: utf-8 -*-

"""
Link definitions to uses.
"""

from __future__ import print_function, division, absolute_import
from collections import defaultdict
from pykit.utils import flatten

def defuse(func):
    """
    Map definitions to uses, e.g.

        %0 = add %a %b
        %1 = mul %0 %b

            => { '%a': {'%0'}, '%b': {'%0', '%1'}, '%0': {'%1'}}
    """
    defuse = defaultdict(set) # { def : { use } }
    for block in func.blocks:
        for op in block:
            for arg in flatten(op.operands):
                defuse[arg].add(op.result)

    return defuse