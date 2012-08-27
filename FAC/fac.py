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

A transition is a pair containing a pos and an update instruction.
It indicates a potential next node in the state, and the updates that
are to be performed if the transition is taken.

A follow value is a map from a pos to a set of transitions that may
originate from the pos.  This set is represented as a Python list
since update instructions are dicts and cannot be hashed.
"""

import operator

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

class NondeterministicFACError (Exception):
    pass

class RecognitionError (Exception):
    pass

class InvalidFACError (Exception):
    pass

class Automaton (object):
    __termTree = None
    def __get_termTree (self):
        return self.__termTree
    termTree = property(__get_termTree)

    __state = None
    def __get_state (self):
        return self.__state
    state = property(__get_state)

    __counterValues = None

    def __init__ (self, term_tree):
        self.__termTree = term_tree
        self.reset()

    def reset (self):
        tt = self.__termTree
        self.__state = None
        self.__counterValues = dict(zip(tt.counters, len(tt.counters) * (1,)))

    def __satisfiable (self, psi):
        for c in psi.iterkeys():
            cv = self.__counterValues[c]
            uv = psi[c]
            if (INCREMENT == uv) and (cv >= c.max):
                return False
            if (RESET == uv) and (cv < c.min):
                return False
        return True

    def __updateCounters (self, psi):
        for (c, uv) in psi.iteritems():
            if RESET == uv:
                self.__counterValues[c] = 1
            else:
                self.__counterValues[c] += 1

    def isFinal (self):
        for (c, cv) in self.__counterValues.iteritems():
            if (cv < c.min) or ((c.max is not None) and (c.max < cv)):
                return False
        return True

    def step (self, sym):
        tt = self.__termTree
        if self.__state is None:
            istate = tt.initialStateMap.get(sym)
            if istate is None:
                raise RecognitionError(sym)
            (self.__state,) = istate
        else:
            delta = tt.phi[self.__state]
            sym_trans = delta.get(sym)
            if sym_trans is None:
                raise RecognitionError(sym)
            sel_trans = None
            for tp in sym_trans:
                (dst, psi) = tp
                if self.__satisfiable(psi):
                    if sel_trans is not None:
                        raise NondeterministicFACError('multiple satisfiable transitions')
                    sel_trans = tp
            if sel_trans is None:
                raise RecognitionError(sym)
            (self.__state, psi) = sel_trans
            self.__updateCounters(psi)
        return self

    def candidateSymbols (self):
        return self.__termTree.phi[self.__state].keys()

    def __str__ (self):
        tt = self.__termTree
        rv = []
        if self.__state is None:
            rv.append("INIT")
        else:
            rv.append(str(tt.nodePosMap[self.__state]))
        rv.append(': ')
        rv.append(' ; '.join([ '%s = %u' % (tt.nodePosMap[_c], _v) for (_c, _v) in self.__counterValues.iteritems() ]))
        return ''.join(rv)

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

    __posNodeMap = None
    def __get_posNodeMap (self):
        if self.__posNodeMap is None:
            pnm = { }
            self.walkTermTree(lambda _n,_p,_a: _a.setdefault(_p, _n), None, pnm)
            self.__posNodeMap = pnm
        return self.__posNodeMap
    posNodeMap = property(__get_posNodeMap)

    __nodePosMap = None
    def __get_nodePosMap (self):
        if self.__nodePosMap is None:
            npm = {}
            for (p,n) in self.posNodeMap.iteritems():
                npm[n] = p
            self.__nodePosMap = npm
        return self.__nodePosMap
    nodePosMap = property(__get_nodePosMap)

    def followPosition (self, position):
        return self.posNodeMap[position]

    def __buildAutomaton (self):
        self.__states = frozenset([ self.posNodeMap[_p] for _p in self.follow.iterkeys() ])
        # All states should be Symbol instances
        assert reduce(operator.and_, map(lambda _s: isinstance(_s, LeafNode), self.__states), True)
        self.__counters = frozenset([ self.posNodeMap[_p] for _p in self.counterPositions() ])
        # All counters should be NumericalConstraint instances
        assert reduce(operator.and_, map(lambda _s: isinstance(_s, NumericalConstraint), self.__counters), True)
        self.__phi = {}
        for (p, transition_set) in self.follow.iteritems():
            src = self.posNodeMap[p]
            self.__phi[src] = delta = {}
            for (q, psi) in transition_set:
                npsi = {}
                for (c, u) in psi.iteritems():
                    npsi[self.posNodeMap[c]] = u
                dst = self.posNodeMap[q]
                delta.setdefault(dst.symbol, []).append((dst, npsi))
        self.__initialStateMap = {}
        for p in self.first:
            n = self.posNodeMap[p]
            if isinstance(n, Symbol):
                self.__initialStateMap.setdefault(n.symbol,set()).add(n)

    __states = None
    def __get_states (self):
        if self.__states is None:
            self.__buildAutomaton()
        return self.__states
    states = property(__get_states)

    __initialStateMap = None
    def __get_initialStateMap (self):
        if self.__initialStateMap is None:
            self.__buildAutomaton()
        return self.__initialStateMap
    initialStateMap = property(__get_initialStateMap)

    __counters = None
    def __get_counters (self):
        if self.__counters is None:
            self.__buildAutomaton()
        return self.__counters
    counters = property(__get_counters)

    __phi = None
    def __get_phi (self):
        if self.__phi is None:
            self.__buildAutomaton()
        return self.__phi
    phi = property(__get_phi)

    def counterPositions (self):
        """All numerical constraint positions that aren't r+.
        
        I.e., implement Definition 13.1."""
        cpos = []
        self.walkTermTree(lambda _n,_p,_a: \
                              isinstance(_n, NumericalConstraint) \
                              and ((1 != _n.min) \
                                   or (_n.max is not None)) \
                              and _a.append(_p),
                          None, cpos)
        return frozenset(cpos)

    def validateAutomaton (self):
        node_map = {}
        self.walkTermTree(lambda _n,_p,_a: _a.setdefault(_n,[]).append(_p), None, node_map)
        for (node, paths) in node_map.iteritems():
            if 1 < len(paths):
                raise InvalidFACError('Node %s appears multiple times at %s' % (node, ' '.join(map(str,paths))))
        return self

    def displayAutomaton (self):
        positions = sorted(self.posNodeMap.keys())
        for p in positions:
            n = self.posNodeMap[p]
            print '%s recognizes %s' % (p, n)
            print '\tfirst: %s' % (' '.join(map(str,n.first)),)
            print '\tlast: %s' % (' '.join(map(str,n.last)),)
        for (src, trans_map) in self.phi.iteritems():
            print '%s recognizing %s:' % (self.nodePosMap[src], src)
            for (sym, transition_set) in trans_map.iteritems():
                for (dst, psi) in transition_set:
                    av = []
                    for (c, uv) in psi.iteritems():
                        av.append('%s %s' % (self.nodePosMap[c], (uv == INCREMENT) and 'inc' or 'res'))
                    print '\t%s via %s: %s' % (self.nodePosMap[dst], sym, ' , '.join(av))

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

class LeafNode (Node):
    pass

class Symbol (LeafNode):
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

    def __str__ (self):
        return str(self.__symbol)

class Empty (LeafNode):
    """A leaf term indicating absence of a symbol.

    This is the only way to introduce nullable into the system."""

    _Precedence = 0

    def _first (self):
        return []
    def _last (self):
        return []
    def _nullable (self):
        return True
    def _follow (self):
        return { (): frozenset() }

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        if post is not None:
            post(self, position, arg)

    def __str__ (self):
        return '_'

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

    def testAutomaton (self):
        au = Automaton(self.ex)
        print 'Initial %s maystart %s' % (au, ' or '.join(au.termTree.initialStateMap.keys()))
        for c in 'aabcaa':
            au.step(c)
            print 'eat %s now %s next %s' % (c, au, ' or '.join(au.candidateSymbols()))
        self.assertTrue(au.isFinal())

    def testKT2004 (self):
        a = Symbol('a')
        x = NumericalConstraint(Sequence(Choice(Symbol('b'), Empty()), Symbol('c')), 1, 2)
        invalid_x = Sequence(Choice(a, Empty()), x, Choice(a, Symbol('d')))
        self.assertRaises(InvalidFACError, invalid_x.validateAutomaton)
        x = Sequence(Choice(Symbol('a'), Empty()), x, Choice(Symbol('a'), Symbol('d')))
        x = NumericalConstraint(x, 3, 4)
        au = Automaton(x.validateAutomaton())
        for word in ['cacaca', 'abcaccdacd']:
            au.reset()
            print 'Initial %s maystart %s' % (au, ' or '.join(au.termTree.initialStateMap.keys()))
            for c in word:
                au.step(c)
                print 'eat %s now %s next %s' % (c, au, ' or '.join(au.candidateSymbols()))
            self.assertTrue(au.isFinal())
        for word in ['caca', 'abcaccdac']:
            au.reset()
            print 'Initial %s maystart %s' % (au, ' or '.join(au.termTree.initialStateMap.keys()))
            for c in word:
                au.step(c)
                print 'eat %s now %s next %s' % (c, au, ' or '.join(au.candidateSymbols()))
            self.assertFalse(au.isFinal())

if __name__ == '__main__':
    unittest.main()
