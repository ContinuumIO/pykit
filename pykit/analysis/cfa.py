# -*- coding: utf-8 -*-

"""
Contruct a control flow graph and compute the SSA graph, reflected through
phi Operations in the IR.
"""

from __future__ import print_function, division, absolute_import
import collections

from pykit.ir import ops, Builder, Undef
from pykit.adt import Graph
from pykit.analysis import defuse
from pykit.utils import mergedicts

def run(func, env=None):
    CFG = cfg(func)
    ssa(func, CFG)

def ssa(func, cfg):
    """Remove all alloca/load/store where possible and insert phi values"""
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
    cfg = Graph()

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
            raise NotImplementedError
            # assert op.opcode == ops.exc_throw # exc_throw
            # targets = [block.get_metadata('exc_target') or 'pykit.exit']

        # -------------------------------------------------
        # Deduce CFG edges from exc_setup

        for op in block.leaders:
            if op.opcode == 'exc_setup':
                [exc_handlers] = op.args
                targets.extend(exc_handlers)

        # -------------------------------------------------
        # Add edges to CFG

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
    predecessors = cfg.T # transpose CFG, block -> predecessors
    phis = {} # phi -> alloca
    for block in func.blocks:
        if len(predecessors[block]) > 1:
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
    predecessors = cfg.T

    # Track block values and delete load/store
    for block in func.blocks:
        # Copy predecessor outgoing values into current block values
        preds = predecessors[block]
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
        preds = list(predecessors[phi.block])
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
    predecessors = cfg.T

    # Initialize
    dominators[func.startblock] = set([func.startblock])
    for block in func.blocks:
        dominators[block] = set(func.blocks)

    # Solve equation
    changed = True
    while changed:
        changed = False
        for block in cfg:
            pred_doms = [dominators[pred] for pred in predecessors[block]]
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
    preds = cfg.T
    for block in reversed(list(func.blocks)):
        if len(preds[block]) == 1 and not list(block.leaders):
            [pred] = preds[block]
            exc_block = any(op.opcode in ('exc_setup',) for op in pred.leaders)
            if not exc_block and len(cfg[pred]) == 1:
                merge_blocks(func, pred, block)