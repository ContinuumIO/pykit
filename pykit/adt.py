# -*- coding: utf-8 -*-

"""
Simple abstract data types.
"""

from __future__ import print_function, division, absolute_import

class LinkableItem(object):
    """
    Linked list item interface. Items must support the _prev and _next
    attributes initialized to None
    """

    def __init__(self, data=None):
        self.data  = data
        self._prev = None
        self._next = None

    def __cmp__(self, other):
        return cmp(self.data, other.data)

    def __repr__(self):
        return "Item(%r)" % (self.data,)

class LinkedList(object):
    """Simple doubly linked list of objects with LinkableItem inferface"""

    def __init__(self, items=()):
        self._head = LinkableItem()
        self._tail = LinkableItem()
        self._head._next = self._tail
        self._tail._prev = self._head
        self.extend(items)

    def insert_before(self, a, b):
        """Insert a before b"""
        a._prev = b._prev
        a._next = b
        b._prev = a
        a._prev._next = a

    def insert_after(self, a, b):
        """Insert a after b"""
        a._prev = b
        a._next = b._next
        b._next = a
        a._next._prev = a

    def remove(self, item):
        """Remove item from list"""
        item._prev._next = item._next
        item._next._prev = item._prev
        item._prev = None
        item._next = None

    def append(self, item):
        """Append an item at the end"""
        self.insert_after(item, self._tail._prev)

    def extend(self, items):
        """Extend list at the end"""
        for op in items:
            self.append(op)

    @property
    def head(self):
        return self._head._next if self._head._next is not self._tail else None

    @property
    def tail(self):
        return self._tail._prev if self._tail._prev is not self._head else None

    def __iter__(self, from_op=None):
        cur = from_op or self._head._next
        while cur is not self._tail:
            yield cur
            cur = cur._next

    iter_from = __iter__

    def __repr__(self):
        return "LinkedList(%s)" % (map(repr, self))