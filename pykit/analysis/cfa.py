# -*- coding: utf-8 -*-

"""
Contruct a control flow graph and compute the SSA graph.
"""

from __future__ import print_function, division, absolute_import
from pykit.ir import Op, ops

from llpython import control_flow

def cfg(func):
    """
    Compute the control flow graph for `func`
    """
    cfg = control_flow.ControlFlowGraph()

    cfg.add_block('pykit_exit')
    for block in func.blocks:
        cfg.add_block(block.name, block)

    for block in func.blocks:
        # Deduce CFG edges from block terminator
        op = block.terminator
        if op.opcode in (ops.jump, ops.cbranch):
            targets = op.operands
        elif op.opcode == ops.ret:
            targets = []
        else:
            assert op.opcode == ops.exc_throw
            targets = [block.get_metadata('exc_target') or 'pykit_exit']

        # Add edges
        for target in targets:
            cfg.add_edge(block.name, target)

    return cfg

def update_writes(func, cfg):
    """Reflect loads and stores in the cfg"""
    for block in func.blocks:
        for op in block:
            if op.opcode == ops.load:
                cfg.blocks_reads[block.name].add(op.result)
            elif op.opcode == ops.store:
                cfg.writes_local(op.result, op.result)

def insert_phis(func, cfg):
    """Reflect computed φs from CFG in IR"""
    raise NotImplementedError

def ssa(func, cfg):
    """
    Compute the SSA graph and insert φ instructions
    """
    update_writes(func, cfg)
    cfg.compute_dataflow()
    cfg.update_for_ssa()
    insert_phis(func, cfg)