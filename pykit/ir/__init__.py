from __future__ import print_function, division, absolute_import

from .value import (Module, GlobalValue, Function, Block, Operation, Constant,
                    Value, Op, Const)
from .parser import from_assembly
from .builder import Builder
from .traversal import transform, visit, index