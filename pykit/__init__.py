# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import os
import unittest

__version__ = '0.1'

root = os.path.dirname(os.path.abspath(__file__))

def test():
    """Run tests and return exit status"""
    tests =  unittest.TestLoader().discover(root)
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    return not result.wasSuccessful()