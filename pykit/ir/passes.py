# -*- coding: utf-8 -*-

"""
Pass helpers.
"""

from __future__ import print_function, division, absolute_import
from pykit.ir.builder import OpBuilder, Builder

class FunctionPass(object):
    """
    Can be used from visitors or transformers, holds a builder and opbuilder.
    """

    opbuilder = OpBuilder()

    def __init__(self, func):
        self.func = func
        self.builder = Builder(func)