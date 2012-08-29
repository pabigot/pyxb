# -*- coding: utf-8 -*-
# Copyright 2012, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""This module provides Finite Automata with Counters.

FACs are type of state machine where a transition may include a
constraint and a modification to a set of counters.  They are used to
implement regular expressions with numerical constraints, as are found
in POSIX regexp, Perl, and XML schema.

The implementation here derives from U{Regular Expressions with
Numerical Constraints and Automata with Counters
<https://bora.uib.no/bitstream/1956/3628/3/Hovland_LNCS%205684.pdf>},
Dag Hovland, Lecture Notes in Computer Science, 2009, Volume 5684,
Theoretical Aspects of Computing - ICTAC 2009, Pages 231-245.
 
A regular expression is directly translated into a term tree, where
nodes are operators such as sequence, choice, and counter
restrictions, and the leaf nodes denote symbols in the language of the
regular expression.

In the case of XML content models, the symbols include L{element
declarations <pyxb.xmlschema.structures.ElementDeclaration>} and
L{wildcard elements <pyxb.xmlschema.structures.Wildcard>}.  A
numerical constraint node corresponds to an L{XML particle
<pyxb.xmlschema.structures.Particle>}, and choice and sequence nodes
derive from L{model groups <pyxb.xmlschema.structures.ModelGroup>} of
types B{choice} and B{sequence}.  As suggested in U{The Membership
Problem for Regular Expressions with Unordered Concatenation and
Numerical Constraints <http://www.ii.uib.no/~dagh/presLATA2012.pdf>}
the B{all} content model can be translated into state machine using
choice and sequence at the cost of a quadratic size explosion;
consequently this type of node is likely to become a leaf node in the
FAC that manages internal transitions among a set of subordinate FACs
corresponding to the alternatives in the group.

In its original form a B{position} (C{pos}) is a tuple of non-negative
integers comprising a path from a node in the term tree.  It
identifies a node in the tree.  After the FAC has been constructed,
only positions that are leaf nodes in the term tree remain, and the
corresponding symbol value (Python instance) is used as the position.

An B{update instruction} (C{psi}) is a map from positions to either
L{RESET} or L{INCREMENT}.  It identifies actions to be taken on the
counter states corresponding to the positions in its domain.

A B{transition} is a pair containing a position and an update instruction.
It identifies a potential next node in the state and the updates that
are to be performed if the transition is taken.

A B{follow value} is a map from a pos to a set of transitions that may
originate from the pos.  This set is represented as a Python list
since update instructions are dicts and cannot be hashed.
"""

import operator

RESET = False
"""An arbitrary value representing reset of a counter."""

INCREMENT = True
"""An arbitrary value representing increment of a counter."""

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
        tt = self.__termTree
        if self.__state is None:
            return tt.nullable
        pos = tt.nodePosMap[self.__state]
        if not (pos in tt.last):
            return False
        for cp in tt.subPositions(pos):
            c = tt.posNodeMap[cp]
            cv = self.__counterValues[c]
            if (cv < c.min) or (cv > c.max):
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
        node_map = {}
        self.walkTermTree(lambda _n,_p,_a: _a.setdefault(_n,[]).append(_p), None, node_map)
        for (node, paths) in node_map.iteritems():
            if 1 < len(paths):
                raise InvalidFACError('Node %s appears multiple times at %s' % (node, ' '.join(map(str,paths))))
        self.__states = frozenset([ self.posNodeMap[_p] for _p in self.follow.iterkeys() ])
        # All states should be Symbol instances
        assert reduce(operator.and_, map(lambda _s: isinstance(_s, Symbol), self.__states), True)
        self.__counters = frozenset([ self.posNodeMap[_p] for _p in self.counterPositions ])
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

    __counterPositions = None
    def __get_counterPositions (self):
        """All numerical constraint positions that aren't r+.
        
        I.e., implement Definition 13.1."""
        if self.__counterPositions is None:
            cpos = []
            self.walkTermTree(lambda _n,_p,_a: \
                                  isinstance(_n, NumericalConstraint) \
                                  and ((1 != _n.min) \
                                       or (_n.max is not None)) \
                                  and _a.append(_p),
                              None, cpos)
            self.__counterPositions = frozenset(cpos)
        return self.__counterPositions
    counterPositions = property(__get_counterPositions)

    def subPositions (self, pos):
        rv = set()
        for cpos in self.counterPositions:
            if cpos == pos[:len(cpos)]:
                rv.add(cpos)
        return frozenset(rv)

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
        for p in self.last:
            print 'Final %s: %s' % (str(p), ' '.join([ str(_p) for _p in self.subPositions(p)]))

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
        The value must be non-negative.

        @keyword max: The maximum number of occurrences of C{term}.
        The value must be positive (in which case it must also be no
        smaller than C{min}), or C{None} to indicate an unbounded
        number of occurrences."""
        super(NumericalConstraint, self).__init__()
        self.__term = term
        self.__min = min
        self.__max = max

    def _first (self):
        return [ (0,) + _fc for _fc in self.__term.first ]

    def _last (self):
        return [ (0,) + _lc for _lc in self.__term.last ]

    def _nullable (self):
        return (0 == self.__min) or self.__term.nullable

    def _follow (self):
        rv = {}
        pp = (0,)
        last_r1 = set(self.__term.last)
        for (q, transition_set) in self.__term.follow.iteritems():
            rv[pp+q] = posConcatTransitionSet(pp, transition_set)
            if q in last_r1:
                last_r1.remove(q)
                for sq1 in self.__term.first:
                    q1 = pp+sq1
                    psi = {}
                    for p1 in self.__term.subPositions(q):
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
            t = self.terms[c]
            pp = (c,)
            for q in t.last:
                for sq1 in self.terms[c+1].first:
                    q1 = (c+1,) + sq1
                    psi = {}
                    for p1 in t.subPositions(q):
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

    def __str__ (self):
        return str(self.__symbol)
