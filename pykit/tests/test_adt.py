# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.adt import LinkableItem, LinkedList

class TestADT(unittest.TestCase):
    def test_linkedlist(self):
        items = map(LinkableItem, range(5))
        l = LinkedList(items)
        foo, bar, head, tail = map(LinkableItem, ["foo", "bar", "head", "tail"])
        five = LinkableItem(5)

        l.insert_before(foo, items[2])
        l.insert_after(bar, items[2])
        l.insert_before(head, items[0])
        l.append(five)
        l.insert_after(tail, five)
        l.remove(items[4])

        expected = ["head", 0, 1, "foo", 2, "bar", 3, 5, "tail"]
        self.assertEqual(list(l), list(map(LinkableItem, expected)))