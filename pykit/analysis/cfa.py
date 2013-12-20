# -*- coding: utf-8 -*-

"""
Contruct a control flow graph and compute the SSA graph, reflected through
phi Operations in the IR.
"""

from __future__ import print_function, division, absolute_import
import collections

from pykit.ir import ops, Builder, Undef
from pykit.analysis import defuse
from pykit.utils import mergedicts

import networkx as nx

def run(func, env=None):
    CFG = cfg(func)
    ssa(func, CFG)

def ssa(func, cfg):
    """Remove all alloca/load/store where possible and insert phi values"""
    # transpose_cfg = cfg.reverse() # reverse edges
    allocas = find_allocas(func)
    move_allocas(func, allocas)
    phis = insert_phis(func, cfg, allocas)
    compute_dataflow(func, cfg, allocas, phis)
    prune_phis(func)
    simplify(func, cfg)

def cfg(func):
    """
    Compute the control flow graph for `func`
    """
    cfg = nx.DiGraph()

    for block in func.blocks:
        # -------------------------------------------------
        # Deduce CFG edges from block terminator
        op = block.terminator
        if op.opcode == 'jump':
            targets = [op.args[0]]
        elif op.opcode == 'cbranch':
            cond, ifbb, elbb = op.args
            targets = [ifbb, elbb]
        elif op.opcode == 'ret':
            targets = []
        else:
            assert op.opcode == ops.exc_throw # exc_throw
            # Below we add all exception handlers as targets. There's nothing
            # to do here (except add the exit block?)

        # -------------------------------------------------
        # Deduce CFG edges from exc_setup

        for op in block.leaders:
            if op.opcode == 'exc_setup':
                [exc_handlers] = op.args
                targets.extend(exc_handlers)

        # -------------------------------------------------
        # Add node and edges to CFG

        cfg.add_node(block)
        for target in targets:
            cfg.add_edge(block, target)

    return cfg

def find_allocas(func):
    """
    Find allocas that can be promoted to registers. We do this only if the
    alloca is used only in load and store operations.
    """
    allocas = set()
    for op in func.ops:
        if (op.opcode == 'alloca' and
                all(u.opcode in ('load', 'store') for u in func.uses[op])):
            allocas.add(op)

    return allocas

def move_allocas(func, allocas):
    """Move all allocas to the start block"""
    builder = Builder(func)
    builder.position_at_beginning(func.startblock)
    for alloca in allocas:
        if alloca.block != func.startblock:
            alloca.unlink()
            builder.emit(alloca)

def insert_phis(func, cfg, allocas):
    """Insert φs in the function given the set of promotable stack variables"""
    builder = Builder(func)
    phis = {} # phi -> alloca
    for block in func.blocks:
        if len(cfg.predecessors(block)) > 1:
            with builder.at_front(block):
                for alloca in allocas:
                    args = [[], []] # predecessors, incoming_values
                    phi = builder.phi(alloca.type.base, args)
                    phis[phi] = alloca

    return phis

def compute_dataflow(func, cfg, allocas, phis):
    """
    Compute the data flow by eliminating load and store ops (given allocas set)

    :param allocas: set of alloca variables to optimize ({Op})
    :param phis:    { φ Op -> alloca }
    """
    values = collections.defaultdict(dict) # {block : { stackvar : value }}

    # Track block values and delete load/store
    for block in func.blocks:
        # Copy predecessor outgoing values into current block values
        preds = cfg.predecessors(block)
        predvars = [values[pred] for pred in preds]
        blockvars = mergedicts(*predvars)

        for op in block.ops:
            if op.opcode == 'alloca' and op in allocas:
                # Initialize to Undefined
                blockvars[op] = Undef(op.type.base)
            elif op.opcode == 'load' and op.args[0] in allocas:
                # Replace load with value
                alloca, = op.args
                op.replace_uses(blockvars[alloca])
                op.delete()
            elif op.opcode == 'store' and op.args[1] in allocas:
                # Delete store and register result
                value, alloca = op.args
                blockvars[alloca] = value
                op.delete()
            elif op.opcode == 'phi' and op in phis:
                alloca = phis[op]
                blockvars[alloca] = op

        values[block] = blockvars

    # Update phis incoming values
    for phi in phis:
        preds = list(cfg.predecessors(phi.block))
        incoming = []
        for block in preds:
            alloca = phis[phi]
            value = values[block][alloca] # value leaving predecessor block
            incoming.append(value)

        phi.set_args([preds, incoming])

    # Remove allocas
    for alloca in allocas:
        alloca.delete()

def prune_phis(func):
    """Delete unnecessary phis (all incoming values equivalent)"""
    for op in func.ops:
        if op.opcode == 'phi' and not func.uses[op]:
            op.delete()
        elif op.opcode == 'phi' and  len(set(op.args[1])) == 1:
            op.replace_uses(op.args[1][0])
            op.delete()

# ______________________________________________________________________

def compute_dominators(func, cfg):
    """
    Compute the dominators for the CFG, i.e. for each basic block the
    set of basic blocks that dominate that block. This means that every path
    from the entry block to that block must go through the blocks in the
    dominator set.

        dominators(root) = {root}
        dominators(x) = {x} ∪ (∩ dominators(y) for y ∈ preds(x))
    """
    dominators = collections.defaultdict(set) # { block : {dominators} }

    # Initialize
    dominators[func.startblock] = set([func.startblock])
    for block in func.blocks:
        dominators[block] = set(func.blocks)

    # Solve equation
    changed = True
    while changed:
        changed = False
        for block in cfg:
            pred_doms = [dominators[pred] for pred in cfg.predecessors(block)]
            new_doms = set([block]) | set.intersection(*pred_doms or [set()])
            if new_doms != dominators[block]:
                dominators[block] = new_doms
                changed = True

    return dominators

# ______________________________________________________________________

def merge_blocks(func, pred, succ):
    """Merge two consecutive blocks (T2 transformation)"""
    assert pred.terminator.opcode == 'jump', pred.terminator.opcode
    assert pred.terminator.args[0] == succ
    pred.terminator.delete()
    pred.extend(succ)
    func.del_block(succ)

def simplify(func, cfg):
    """
    Simplify control flow. Merge consecutive blocks where the parent has one
    child, the child one parent, and both have compatible instruction leaders.
    """
    for block in reversed(list(func.blocks)):
        if len(cfg.predecessors(block)) == 1 and not list(block.leaders):
            [pred] = cfg.predecessors(block)
            exc_block = any(op.opcode in ('exc_setup',) for op in pred.leaders)
            if not exc_block and len(cfg[pred]) == 1:
                merge_blocks(func, pred, block)