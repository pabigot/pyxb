# -*- coding: utf-8 -*-

# "Regular Expressions with Numerical Constraints and Automata with
# Counters", Dag Hovland.  Proceedings of the 6th International
# Colloquium on Theoretical Aspects of Computing, pp 231--245.  Pages
# 231 - 245 Springer-Verlag Berlin, Heidelberg, 2009.
#
# http://www.ii.uib.no/~dagh/
#
# LATA 2012: The Membership Problem for Regular Expressions with
# Unordered Concatenation and Numerical Constraints
# (http://www.ii.uib.no/~dagh/presLATA2012.pdf)
 

class PathError (LookupError):
    pass

class Node (object):
    """Abstract class for any node in the term tree."""

    _Precedence = None
    """An integral value used for parenthesizing expressions.

    A subterm that has a precedence less than that of its containing
    term must be enclosed in parentheses when forming a text
    expression representing the containing term."""

    __first = None
    def __get_first (self):
        if self.__first is None:
            self.__first = frozenset(self._first())
        return self.__first
    first = property(__get_first)

    def _first (self):
        raise NotImplementedError('%s.first' % (self.__class__.__name__,))

    __last = None
    def __get_last (self):
        if self.__last is None:
            self.__last = frozenset(self._last())
        return self.__last
    last = property(__get_last)
    
    def _last (self):
        raise NotImplementedError('%s.first' % (self.__class__.__name__,))

    __nullable = None
    def __get_nullable (self):
        if self.__nullable is None:
            self.__nullable = self._nullable()
        return self.__nullable
    nullable = property(__get_nullable)
    
    def _nullable (self):
        raise NotImplementedError('%s.nullable' % (self.__class__.__name__,))

    def followPath (self, path):
        raise NotImplementedError('%s.followPath' % (self.__class__.__name__,))

class NumericalConstraint (Node):
    """A term with a numeric range constraint.

    This corresponds to a "particle" in the XML Schema content model."""

    _Precedence = -1

    __min = None
    def __get_min (self):
        return self.__min
    min = property(__get_min)

    __max = None
    def __get_max (self):
        return self.__max
    max = property(__get_max)

    __term = None
    def __get_term (self):
        return self.__term
    term = property(__get_term)

    def __init__ (self, term, min=0, max=1):
        """Term with a numerical constraint.

        @param term: A term, the number of appearances of which is
        constrained in this term.
        @type term: L{Node}

        @keyword min: The minimum number of occurrences of C{term}.
        The value must be positive.  To model a situation where the
        minimum number of occurrences is zero, use L{Choice} with an
        L{Empty} term and a L{NumericalConstraint} term with a minimum
        occurrence of 1.

        @keyword max: The maximum number of occurrences of C{term}.
        The value must be positive (in which case it must also be no
        smaller than C{min}), or C{None} to indicate an unbounded
        number of occurrences."""
        self.__term = term
        if 0 == min:
            raise ValueError('numerical constraint min must be positive')
        self.__min = min
        self.__max = max

    def _first (self):
        return [ (0,) + _fc for _fc in self.__term.first ]

    def _nullable (self):
        return self.__term.nullable

    def followPath (self, path):
        if 0 == len(path):
            return self
        if 0 != path[0]:
            raise PathError(path)
        return self.__term.followPath(path[1:])

    def __str__ (self):
        rv = str(self.__term)
        if self.__term._Precedence < self._Precedence:
            rv = '(' + rv + ')'
        rv += '^(%u,' % (self.__min,)
        if self.__max is not None:
            rv += '%u' % (self.__max)
        return rv + ')'

class Choice (Node):
    """A term that may be any one of a set of terms.

    This term matches if any one of its contained terms matches."""
    
    _Precedence = -3

    __terms = None
    
    def __init__ (self, *terms):
        """Term that selects one of a set of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def _first (self):
        rv = set()
        for c in xrange(len(self.__terms)):
            rv.update([ (c,) + _fc for _fc in  self.__terms[c].first])
        return rv

    def _last (self):
        rv = set()
        for c in xrange(len(self.__terms)):
            rv.update([ (c,) + _lc for _lc in  self.__terms[c].last])
        return rv

    def _nullable (self):
        for t in self.__terms:
            if t.nullable:
                return True
        return False

    def followPath (self, path):
        if 0 == len(path):
            return self
        c = path[0]
        return self.__terms[c].followPath(path[1:])

    def __str__ (self):
        elts = []
        for t in self.__terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '+'.join(elts)

class Sequence (Node):
    """A term that is an ordered sequence of terms."""
    
    _Precedence = -2

    __terms = None

    def __init__ (self, *terms):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def _first (self):
        rv = set()
        c = 0
        while c < len(self.__terms):
            t = self.__terms[c]
            rv.update([ (c,) + _fc for _fc in t.first])
            if not t.nullable:
                break
            c += 1
        return rv

    def _nullable (self):
        for t in self.__terms:
            if not t.nullable:
                return False
        return True

    def followPath (self, path):
        if 0 == len(path):
            return self
        c = path[0]
        return self.__terms[c].followPath(path[1:])

    def __str__ (self):
        elts = []
        for t in self.__terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '.'.join(elts)

class All (Node):
    """A term that is an unordered sequence of terms."""

    _Precedence = 0

    __terms = None

    def __init__ (self, *terms):
        """Term that collects an unordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def _nullable (self):
        for t in self.__terms:
            if not t.nullable:
                return False
        return True

    def __str__ (self):
        return u'&(' + ','.join([str(_t) for _t in self.__terms]) + ')'

class Symbol (Node):
    """A term that is a symbol (leaf node)."""

    __symbol = None
    def __get_symbol (self):
        return self.__symbol
    symbol = property(__get_symbol)

    _Precedence = 0

    def __init__ (self, symbol):
        self.__symbol = symbol

    def _first (self):
        return [()]
    def _last (self):
        return [()]
    def _nullable (self):
        return False

    def followPath (self, path):
        if () != path:
            raise PathError(path)
        return self

    def __str__ (self):
        return str(self.__symbol)

class Empty (Node):
    """A term indicating that no symbol is consumed."""

    _Precedence = 0

    def _first (self):
        return []
    def _last (self):
        return []
    def _nullable (self):
        return True

    def followPath (self, path):
        if () != path:
            raise PathError(path)
        return self

    def __str__ (self):
        return u'ε'

import unittest
class TestFAC (unittest.TestCase):

    epsilon = Empty()
    a = Symbol('a')
    b = Symbol('b')
    c = Symbol('c')
    aOb = Choice(a, b)
    aTb = Sequence(a, b)
    a2 = NumericalConstraint(a, 2, 2)
    bTc = Sequence(b, c)
    a2ObTc = Choice(a2, bTc)
    aXb = All(a, b)
    ex = NumericalConstraint(a2ObTc, 3, 5)

    def testSymbol (self):
        self.assertEqual('a', self.a.symbol)

    def testNumericalConstraint (self):
        self.assertRaises(ValueError, NumericalConstraint, self.a, 0, 1)
        self.assertEqual(self.a2ObTc, self.ex.term)
        self.assertEqual(3, self.ex.min)
        self.assertEqual(5, self.ex.max)

    def testBasicStr (self):
        self.assertEqual('a', str(self.a))
        self.assertEqual('b', str(self.b))
        self.assertEqual('a+b', str(self.aOb))
        self.assertEqual('a.b', str(self.aTb))
        self.assertEqual('&(a,b)', str(self.aXb))
        x = Choice(self.b, self.aTb)
        self.assertEqual('b+a.b', str(x))
        x = Sequence(self.a, self.aOb)
        self.assertEqual('a.(a+b)', str(x))
        x = NumericalConstraint(self.a2ObTc, 3, 5)
        self.assertEqual('(a^(2,2)+b.c)^(3,5)', str(x))

    def testNullable (self):
        self.assertTrue(self.epsilon.nullable)
        self.assertFalse(self.a.nullable)
        self.assertFalse(self.aOb.nullable)
        aOe = Choice(self.a, self.epsilon)
        self.assertTrue(aOe.nullable)
        eOa = Choice(self.epsilon, self.a)
        self.assertTrue(eOa.nullable)
        self.assertFalse(self.aTb.nullable)
        x = Sequence(aOe, self.b)
        self.assertFalse(x.nullable)
        x = Sequence(aOe, eOa)
        self.assertTrue(x.nullable)
        self.assertFalse(self.aXb.nullable)
        x = All(aOe, eOa)
        self.assertTrue(x.nullable)
        x = NumericalConstraint(self.a, 1, 4)
        self.assertFalse(x.nullable)
        x = NumericalConstraint(aOe, 1, 4)
        self.assertTrue(x.nullable)

    def testFirst (self):
        empty_set = frozenset()
        null_path = frozenset([()])
        p0 = frozenset([(0,)])
        p1 = frozenset([(1,)])
        p0or1 = frozenset(set(p0).union(p1))
        self.assertEqual(empty_set, self.epsilon.first)
        self.assertEqual(null_path, self.a.first)
        for p in self.a.first:
            self.assertEqual(self.a, self.a.followPath(p))
        self.assertEqual(p0or1, self.aOb.first)
        self.assertEqual(p0, self.aTb.first)
        for p in self.aTb.first:
            self.assertEqual(self.a, self.aTb.followPath(p))
        rs = set()
        for p in self.a2ObTc.first:
            rs.add(self.a2ObTc.followPath(p))
        self.assertEqual(frozenset([self.a, self.b]), rs)

if __name__ == '__main__':
    unittest.main()
