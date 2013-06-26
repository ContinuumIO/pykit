# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from os.path import dirname, abspath
import unittest

__version__ = '0.1'

root = dirname(dirname(abspath(__file__)))

def test():
    """Run tests and return exit status"""
    tests =  unittest.TestLoader().discover(root)
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    return not result.wasSuccessful()