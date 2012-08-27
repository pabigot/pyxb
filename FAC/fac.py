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
 
"""

A pos (position) is a tuple of non-negative integers comprising a path
from a node in the term tree.  It identifies a node in the tree.

An update instruction (psi) is a map from positions to either RESET or
INCREMENT.  It identifies actions to be taken on the counter states
corresponding to the positions in its domain.

A transition is a pair containing a path and an update instruction.
It indicates a potential next node in the state, and the updates that
are to be performed if the transition is taken.

A follow value is a map from a pos to a set of transitions that may
originate from the pos.  This set is represented as a Python list
since update instructions are dicts and cannot be hashed.
"""


RESET = False
INCREMENT = True

class PositionError (LookupError):
    pass

def posConcatPosSet (pos, pos_set):
    """Definition 11.1"""
    return frozenset([ pos + _mp for _mp in pos_set ])

def posConcatUpdateInstruction (pos, psi):
    """Definition 11.2"""
    rv = {}
    for (q, v) in psi.iteritems():
        rv[pos + q] = v
    return rv

def posConcatTransitionSet (pos, transition_set):
    """Definition 11.3"""
    ts = []
    for (q, psi) in transition_set:
        ts.append((pos + q, posConcatUpdateInstruction(pos, psi) ))
    return ts

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
        raise NotImplementedError('%s.last' % (self.__class__.__name__,))

    __nullable = None
    def __get_nullable (self):
        if self.__nullable is None:
            self.__nullable = self._nullable()
        return self.__nullable
    nullable = property(__get_nullable)
    
    def _nullable (self):
        raise NotImplementedError('%s.nullable' % (self.__class__.__name__,))

    __follow = None
    def __get_follow (self):
        if self.__follow is None:
            self.__follow = self._follow()
        return self.__follow
    follow = property(__get_follow)

    def _follow (self):
        raise NotImplementedError('%s.follow' % (self.__class__.__name__,))

    def walkTermTree (self, pre, post, arg):
        return self._walkTermTree((), pre, post, arg)

    def _walkTermTree (self, position, pre, post, arg):
        raise NotImplementedError('%s.walkTermTree' % (self.__class__.__name__,))

    def followPosition (self, position):
        raise NotImplementedError('%s.followPosition' % (self.__class__.__name__,))

    def counterPositions (self):
        """All numerical constraint positions that aren't r+.
        
        I.e., implement Definition 13.1."""
        cpos = []
        self.walkTermTree(lambda _n,_p,_a: \
                              isinstance(_n, NumericalConstraint) \
                              and 1 != _n.min \
                              and _n.max is not None \
                              and _a.append(_p),
                          None, cpos)
        return frozenset(cpos)

class MultiTermNode (Node):
    """Intermediary for nodes that have multiple child nodes."""
    
    __terms = None
    def __get_terms (self):
        return self.__terms
    terms = property(__get_terms)

    def __init__ (self, *terms):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(MultiTermNode, self).__init__()
        self.__terms = terms

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        for c in xrange(len(self.__terms)):
            self.__terms[c]._walkTermTree(position + (c,), pre, post, arg)
        if post is not None:
            post(self, position, arg)

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
        super(NumericalConstraint, self).__init__()
        self.__term = term
        if 0 == min:
            raise ValueError('numerical constraint min must be positive')
        self.__min = min
        self.__max = max

    def _first (self):
        return [ (0,) + _fc for _fc in self.__term.first ]

    def _last (self):
        return [ (0,) + _lc for _lc in self.__term.last ]

    def _nullable (self):
        return self.__term.nullable

    def _follow (self):
        rv = {}
        pp = (0,)
        last_r1 = set(self.__term.last)
        counter_pos = self.__term.counterPositions()
        for (q, transition_set) in self.__term.follow.iteritems():
            rv[pp+q] = posConcatTransitionSet(pp, transition_set)
            if q in last_r1:
                last_r1.remove(q)
                for sq1 in self.__term.first:
                    q1 = pp+sq1
                    psi = {}
                    for p1 in counter_pos:
                        if p1 == q[:len(p1)]:
                            psi[pp+p1] = RESET
                    if (1 != self.min) or (self.max is not None):
                        psi[()] = INCREMENT
                    rv[pp+q].append((q1, psi))
        assert not last_r1
        return rv
                
    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        self.__term._walkTermTree(position + (0,), pre, post, arg)
        if post is not None:
            post(self, position, arg)

    def followPosition (self, position):
        if 0 == len(position):
            return self
        if 0 != position[0]:
            raise PositionError(position)
        return self.__term.followPosition(position[1:])

    def __str__ (self):
        rv = str(self.__term)
        if self.__term._Precedence < self._Precedence:
            rv = '(' + rv + ')'
        rv += '^(%u,' % (self.__min,)
        if self.__max is not None:
            rv += '%u' % (self.__max)
        return rv + ')'

class Choice (MultiTermNode):
    """A term that may be any one of a set of terms.

    This term matches if any one of its contained terms matches."""
    
    _Precedence = -3

    def __init__ (self, *terms):
        """Term that selects one of a set of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Choice, self).__init__(*terms)
        
    def _first (self):
        rv = set()
        for c in xrange(len(self.terms)):
            rv.update([ (c,) + _fc for _fc in self.terms[c].first])
        return rv

    def _last (self):
        rv = set()
        for c in xrange(len(self.terms)):
            rv.update([ (c,) + _lc for _lc in self.terms[c].last])
        return rv

    def _nullable (self):
        for t in self.terms:
            if t.nullable:
                return True
        return False

    def _follow (self):
        rv = {}
        for c in xrange(len(self.terms)):
            for (q, transition_set) in self.terms[c].follow.iteritems():
                pp = (c,)
                rv[pp + q] = posConcatTransitionSet(pp, transition_set)
        return rv

    def followPosition (self, position):
        if 0 == len(position):
            return self
        c = position[0]
        return self.terms[c].followPosition(position[1:])

    def __str__ (self):
        elts = []
        for t in self.terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '+'.join(elts)

class Sequence (MultiTermNode):
    """A term that is an ordered sequence of terms."""
    
    _Precedence = -2

    def __init__ (self, *terms):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Sequence, self).__init__(*terms)

    def _first (self):
        rv = set()
        c = 0
        while c < len(self.terms):
            t = self.terms[c]
            rv.update([ (c,) + _fc for _fc in t.first])
            if not t.nullable:
                break
            c += 1
        return rv

    def _last (self):
        rv = set()
        c = len(self.terms) - 1;
        while 0 <= c:
            t = self.terms[c]
            rv.update([ (c,) + _lc for _lc in t.last])
            if not t.nullable:
                break
            c -= 1
        return rv

    def _nullable (self):
        for t in self.terms:
            if not t.nullable:
                return False
        return True

    def _follow (self):
        rv = {}
        for c in xrange(len(self.terms)):
            pp = (c,)
            for (q, transition_set) in self.terms[c].follow.iteritems():
                rv[pp + q] = posConcatTransitionSet(pp, transition_set)
        for c in xrange(len(self.terms)-1):
            pp = (c,)
            counter_pos = self.terms[c].counterPositions()
            for q in self.terms[c].last:
                for sq1 in self.terms[c+1].first:
                    q1 = (c+1,) + sq1
                    psi = {}
                    for p1 in counter_pos:
                        if p1 == q[:len(p1)]:
                            psi[pp + p1] = RESET
                    rv[pp+q].append((q1, psi))
        return rv
            
    def followPosition (self, position):
        if 0 == len(position):
            return self
        c = position[0]
        return self.terms[c].followPosition(position[1:])

    def __str__ (self):
        elts = []
        for t in self.terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '.'.join(elts)

class All (MultiTermNode):
    """A term that is an unordered sequence of terms."""

    _Precedence = 0

    def __init__ (self, *terms):
        """Term that collects an unordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(All, self).__init__(*terms)

    def _nullable (self):
        for t in self.terms:
            if not t.nullable:
                return False
        return True

    def __str__ (self):
        return u'&(' + ','.join([str(_t) for _t in self.terms]) + ')'

class Symbol (Node):
    """A leaf term that is a symbol."""

    __symbol = None
    def __get_symbol (self):
        return self.__symbol
    symbol = property(__get_symbol)

    _Precedence = 0

    def __init__ (self, symbol):
        super(Symbol, self).__init__()
        self.__symbol = symbol

    def _first (self):
        return [()]
    def _last (self):
        return [()]
    def _nullable (self):
        return False
    def _follow (self):
        return { (): frozenset() }

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        if post is not None:
            post(self, position, arg)

    def followPosition (self, position):
        if () != position:
            raise PositionError(position)
        return self

    def __str__ (self):
        return str(self.__symbol)

class Empty (Node):
    """A leaf term indicating absence of a symbol.

    This is the only way to introduce nullable into the system."""

    _Precedence = 0

    def _first (self):
        return []
    def _last (self):
        return []
    def _nullable (self):
        return True

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        if post is not None:
            post(self, position, arg)

    def followPosition (self, position):
        if () != position:
            raise PositionError(position)
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
        null_position = frozenset([()])
        p0 = frozenset([(0,)])
        p1 = frozenset([(1,)])
        p0or1 = frozenset(set(p0).union(p1))
        self.assertEqual(empty_set, self.epsilon.first)
        self.assertEqual(null_position, self.a.first)
        for p in self.a.first:
            self.assertEqual(self.a, self.a.followPosition(p))
        self.assertEqual(p0or1, self.aOb.first)
        self.assertEqual(p0, self.aTb.first)
        for p in self.aTb.first:
            self.assertEqual(self.a, self.aTb.followPosition(p))
        rs = set()
        for p in self.a2ObTc.first:
            rs.add(self.a2ObTc.followPosition(p))
        self.assertEqual(frozenset([self.a, self.b]), rs)

    def testLast (self):
        empty_set = frozenset()
        null_position = frozenset([()])
        p0 = frozenset([(0,)])
        p1 = frozenset([(1,)])
        p0or1 = frozenset(set(p0).union(p1))
        self.assertEqual(empty_set, self.epsilon.last)
        self.assertEqual(null_position, self.a.last)
        self.assertEqual(p0or1, self.aOb.last)
        self.assertEqual(p1, self.aTb.last)
        rs = set()
        for p in self.a2ObTc.last:
            rs.add(self.a2ObTc.followPosition(p))
        self.assertEqual(frozenset([self.a, self.c]), rs)

        #import sys
        #pre_print = lambda _n,_p,_a: sys.stdout.write('Pre %s at %s\n' % (_n, _p))
        #post_print = lambda _n,_p,_a: sys.stdout.write('Post %s at %s\n' % (_n, _p))
        #self.ex.walkTermTree(pre_print, post_print, None)

    def testWalkTermTree (self):
        pre_pos = []
        post_pos = []
        set_sym_pos = lambda _n,_p,_a: isinstance(_n, Symbol) and _a.append(_p)
        self.ex.walkTermTree(set_sym_pos, None, pre_pos)
        self.ex.walkTermTree(None, set_sym_pos, post_pos)
        self.assertEqual(pre_pos, post_pos)
        self.assertEqual([(0,0,0),(0,1,0),(0,1,1)], pre_pos)

    def testCounterPositions (self):
        self.assertEqual(frozenset([(), (0,0)]), self.ex.counterPositions())

    def testFollow (self):
        m = self.a.follow
        self.assertEqual(1, len(m))
        self.assertEqual([((), frozenset())], m.items())
        
if __name__ == '__main__':
    unittest.main()
