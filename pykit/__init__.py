# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from os.path import dirname, abspath
import unittest

from pykit.configuration import config
from pykit.parsing import from_c

__version__ = '0.1'

# ______________________________________________________________________
# pykit.test()

root = dirname(abspath(__file__))
pattern = "test_*.py"

def test(root=root, pattern=pattern):
    """Run tests and return exit status"""
    tests =  unittest.TestLoader().discover(root, pattern=pattern)
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    return not result.wasSuccessful()

def run_tests(dirs, pattern=pattern, failfast=True):
    """Run tests in specified order, quitting on the first failure if failfast"""
    status = 0
    for dir in dirs:
        status |= test(dir, pattern)
        if failfast and status != 0:
            break

    return status