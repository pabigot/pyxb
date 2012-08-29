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
Theoretical Aspects of Computing - ICTAC 2009, Pages 231-245.  In what
follows, this reference will be denoted B{HOV09}.
 
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

class FACError (Exception):
    pass

class InvalidTermTreeError (FACError):
    """Exception raised when a FAC term tree is not a tree.

    For example, a L{Symbol} node appears multiple times, or a cycle is detected."""
    pass

class CounterApplicationError (FACError):
    """Exception raised when an unsatisfied update instruction is executed.

    This indicates an internal error in the implementation."""
    pass

class NondeterministicFACError (Exception):
    pass

class RecognitionError (Exception):
    pass

class State (object):
    """A thin wrapper around an object reference.

    The state of the automaton corresponds to a position, or marked
    symbol, in the term tree.  Because the same symbol may appear at
    multiple locations in the tree, and the distinction between these
    positions is critical, a L{State} wrapper is provided to maintain
    distinct values."""
    __symbol = None
    def __get_symbol (self):
        return self.__symbol
    symbol = property(__get_symbol)

    def __init__ (self, symbol=None):
        self.__symbol = symbol

    def match (self, symbol):
        """Return C{True} iff the symbol matches for this state.

        This may be overridden by subclasses when matching by
        equivalence does not work."""
        return self.__symbol == symbol

class CounterCondition (object):
    """A counter condition is a range limit on valid counter values.

    Instances of this class serve as keys for the counters that
    represent the configuration of a FAC.  The instance also maintains
    a pointer to application-specific L{metadata}."""

    __min = None
    def __get_min (self):
        """The minimum legal value for the counter.

        This is a non-negative integer."""
        return self.__min
    min = property(__get_min)

    __max = None
    def __get_max (self):
        """The maximum legal value for the counter.

        This is a positive integer, or C{None} to indicate that the
        counter is unbounded."""
        return self.__max
    max = property(__get_max)
    
    __metadata = None
    def __get_metadata (self):
        """A pointer to application metadata provided when the condition was created."""
        return self.__metadata
    metadata = property(__get_metadata)

    def __init__ (self, min, max, metadata=None):
        """Create a counter condition.

        @param min : The value for L{min}
        @param max : The value for L{max}
        @param metadata : The value for L{metadata}
        """
        self.__min = min
        self.__max = max
        self.__metadata = metadata

class UpdateInstruction:
    """An update instruction pairs a counter with a mutation of that counter.

    The instruction is executed during a transition from one state to
    another, and causes the corresponding counter to be incremented or
    reset.  The instruction may only be applied if doing so does not
    violate the conditions of the counter it affects."""
    __counterCondition = None
    __min = None
    __max = None
    __doIncrement = None

    def __init__ (self, counter_condition, do_increment):
        """Create an update instruction.

        @param counter_condition : A L{CounterCondition} identifying a
        minimum and maximum value for a counter, and serving as a map
        key for the value of the corresponding counter.

        @param do_increment : C{True} if the update is to increment
        the value of the counter; C{False} if the update is to reset
        the counter.
        """
        self.__counterCondition = counter_condition
        self.__min = counter_condition.min
        self.__max = counter_condition.max
        self.__doIncrement = not not do_increment

    def satisfiedBy (self, counter_values):
        """Implement a component of definition 5 from B{HOV09}.

        The update instruction is satisfied by the counter values if
        its action may be legitimately applied to the value of its
        associated counter.

        @param counter_values : A map from  L{CounterCondition}s to
        non-negative integers

        @return:  C{True} or C{False}
        """
        value = counter_values[self.__counterCondition]
        if self.__doIncrement \
                and (self.__max is not None) \
                and (value >= self.__max):
            return False
        if (not self.__doIncrement) \
                and (value < self.__min):
            return False
        return True

    @classmethod
    def Satisfies (cls, counter_values, update_instructions):
        """Return C{True} iff the counter values satisfy the update
        instructions.

        @param counter_values : A map from L{CounterCondition} to
        integer counter values

        @param update_instructions : A set of L{UpdateInstruction}
        instances

        @return: C{True} iff all instructions are satisfied by the
        values and limits."""
        for psi in update_instructions:
            if not psi.satisfiedBy(counter_values):
                return False
        return True

    def apply (self, counter_values):
        """Apply the update instruction to the provided counter values.

        @param counter_values : A map from L{CounterCondition} to
        inter counter values.  This map is updated in-place."""
        if not self.satisfiedBy(counter_values):
            raise CounterSatisfactionError(self, counter_values)
        value = counter_values[self.__counterCondition]
        if self.__doIncrement:
            value += 1
        else:
            value = 1
        counter_values[self.__counterCondition] = value

    @classmethod
    def Apply (cls, update_instructions, counter_values):
        """Apply the update instructions to the counter values.

        @param update_instructions : A set of L{UpdateInstruction}
        instances.

        @param counter_values : A map from L{CounterCondition}
        instances to non-negative integers.  This map is updated
        in-place by applying each instruction in
        C{update_instructions}."""
        for psi in update_instructions:
            psi.apply(counter_values)

class Configuration (object):
    __state = None
    def __get_state (self):
        """The state of the configuration.

        This is C{None} to indicate an initial state, or one of the underlying automaton's states."""
        return self.__state
    state = property(__get_state)

    __counterValues = None
    """The values of the counters.

    This is a map from the CounterCondition instances of the
    underlying automaton to integer values."""

    __automaton = None
    def __get_automaton (self):
        return self.__automaton
    automaton = property(__get_automaton)

    def reset (self):
        fac = self.__automaton
        self.__state = None
        self.__counterValues = dict(zip(fac.counterConditions, len(fac.counterConditions) * (1,)))

    def __init__ (self, automaton):
        self.__automaton = automaton
        self.reset()

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
        for cp in tt.counterSubPositions(pos):
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

    def __init__ (self, **kw):
        """Create a FAC term-tree node.

        @kw metadata : Any application-specific metadata retained in
        the term tree for transfer to the resulting automaton."""
        self.__metadata = kw.get('metadata')

    __metadata = None
    def __get_metadata (self):
        """Application-specific metadata provided during construction."""
        return self.__metadata
    metadata = property(__get_metadata)

    __first = None
    def __get_first (self):
        """The I{first} set for the node.

        This is the set of positions leading to symbols that can
        appear first in a string matched by an execution starting at
        the node."""
        if self.__first is None:
            self.__first = frozenset(self._first())
        return self.__first
    first = property(__get_first)

    def _first (self):
        """Abstract method that defines L{first} for the subclass.

        The return value should be an iterable of tuples of integers
        denoting paths from this node through the term tree to a
        symbol."""
        raise NotImplementedError('%s.first' % (self.__class__.__name__,))

    __last = None
    def __get_last (self):
        """The I{last} set for the node.

        This is the set of positions leading to symbols that can
        appear last in a string matched by an execution starting at
        the node."""
        if self.__last is None:
            self.__last = frozenset(self._last())
        return self.__last
    last = property(__get_last)
    
    def _last (self):
        """Abstract method that defines L{last} for the subclass.

        The return value should be an iterable of tuples of integers
        denoting paths from this node through the term tree to a
        symbol."""
        raise NotImplementedError('%s.last' % (self.__class__.__name__,))

    __nullable = None
    def __get_nullable (self):
        """C{True} iff the empty string is accepted by this node."""
        if self.__nullable is None:
            self.__nullable = self._nullable()
        return self.__nullable
    nullable = property(__get_nullable)
    
    def _nullable (self):
        """Abstract method that defines L{nullable} for the subclass.

        The return value should be C{True} or C{False}."""
        raise NotImplementedError('%s.nullable' % (self.__class__.__name__,))

    __follow = None
    def __get_follow (self):
        """The I{follow} map for the node."""
        if self.__follow is None:
            self.__follow = self._follow()
        return self.__follow
    follow = property(__get_follow)

    def _follow (self):
        """Abstract method that defines L{follow} for the subclass.
        
        The return value should be a map from tuples of integers (positions)
        to a list of transitions, where a transition is a position and
        an update instruction."""
        raise NotImplementedError('%s.follow' % (self.__class__.__name__,))

    def walkTermTree (self, pre, post, arg):
        """Utility function for term tree processing.

        @param pre : a callable that, unless C{None}, is invoked at
        each node C{n} with parameters C{n}, C{pos}, and C{arg}, where
        C{pos} is the tuple of integers identifying the path from the
        node at on which this method was invoked to the node being
        processed.  The invocation occurs before processing any
        subordinate nodes.

        @param post : as with C{pre} but invocation occurs after
        processing any subordinate nodes.

        @param arg : a value passed to invocations of C{pre} and
        C{post}."""
        self._walkTermTree((), pre, post, arg)

    def _walkTermTree (self, position, pre, post, arg):
        """Abstract method implementing L{walkTermTree} for the subclass."""
        raise NotImplementedError('%s.walkTermTree' % (self.__class__.__name__,))

    __posNodeMap = None
    def __get_posNodeMap (self):
        """A map from positions to nodes in the term tree."""
        if self.__posNodeMap is None:
            pnm = { }
            self.walkTermTree(lambda _n,_p,_a: _a.setdefault(_p, _n), None, pnm)
            self.__posNodeMap = pnm
        return self.__posNodeMap
    posNodeMap = property(__get_posNodeMap)

    __nodePosMap = None
    def __get_nodePosMap (self):
        """A map from nodes to their position in the term tree."""
        if self.__nodePosMap is None:
            npm = {}
            for (p,n) in self.posNodeMap.iteritems():
                npm[n] = p
            self.__nodePosMap = npm
        return self.__nodePosMap
    nodePosMap = property(__get_nodePosMap)

    @classmethod
    def _PosConcatPosSet (cls, pos, pos_set):
        """Implement definition 11.1 in B{HOV09}."""
        return frozenset([ pos + _mp for _mp in pos_set ])

    @classmethod
    def _PosConcatUpdateInstruction (cls, pos, psi):
        """Implement definition 11.2 in B{HOV09}"""
        rv = {}
        for (q, v) in psi.iteritems():
            rv[pos + q] = v
        return rv

    @classmethod
    def _PosConcatTransitionSet (cls, pos, transition_set):
        """Implement definition 11.3 in B{HOV09}"""
        ts = []
        for (q, psi) in transition_set:
            ts.append((pos + q, cls._PosConcatUpdateInstruction(pos, psi) ))
        return ts

    def __validateTreeNode (self, node, pos, visited_nodes):
        if node in visited_nodes:
            raise InvalidTermTreeError(self)
        visited_nodes.add(node)

    def __buildAutomaton (self, state_ctor=State, ctr_cond_ctor=CounterCondition):
        # Validate that the term tree is in fact a tree.  A DAG does
        # not work.  If the tree has cycles, this won't even return.
        self.walkTermTree(self.__validateTreeNode, None, set())

        # Get the FAC states as nodes in the term tree
        self.__states = frozenset([ self.posNodeMap[_p] for _p in self.follow.iterkeys() ])

        # All states should be Symbol instances
        assert reduce(operator.and_, map(lambda _s: isinstance(_s, Symbol), self.__states), True)

        # Get the FAC counters as nodes in the term tree
        self.__counters = frozenset([ self.posNodeMap[_p] for _p in self.counterPositions ])
        # All counters should be NumericalConstraint instances
        assert reduce(operator.and_, map(lambda _s: isinstance(_s, NumericalConstraint), self.__counters), True)

        # Get the transition function as a map from nodes (src) to
        # maps from symbols to maps from nodes (dst) to update
        # instructions.
        self.__phi = {}
        for (p, transition_set) in self.follow.iteritems():
            src = self.posNodeMap[p]
            self.__phi[src] = delta = {}
            for (q, psi) in transition_set:
                npsi = {}
                for (c, u) in psi.iteritems():
                    npsi[self.posNodeMap[c]] = u
                dst = self.posNodeMap[q]
                delta.setdefault(dst.metadata, []).append((dst, npsi))
        self.__initialStateMap = {}
        for p in self.first:
            n = self.posNodeMap[p]
            if isinstance(n, Symbol):
                self.__initialStateMap.setdefault(n.metadata, set()).add(n)

    __states = None
    def __get_states (self):
        """The set of L{symbols <Symbol>} that serve as states in the FAC."""
        if self.__states is None:
            self.__buildAutomaton()
        return self.__states
    states = property(__get_states)

    __initialStateMap = None
    def __get_initialStateMap (self):
        """The set of L{symbols <Symbol>} that can be initial states in the FAC."""
        if self.__initialStateMap is None:
            self.__buildAutomaton()
        return self.__initialStateMap
    initialStateMap = property(__get_initialStateMap)

    __counters = None
    def __get_counters (self):
        """The set of L{counters <NumericalConstraint>} relevant to processing the FAC."""
        if self.__counters is None:
            self.__buildAutomaton()
        return self.__counters
    counters = property(__get_counters)

    __phi = None
    def __get_phi (self):
        """The transition function for the FAC.

        Given a source L{state <Symbol>} C{src}, the value C{phi[src]}
        is a map showing potential transitions from C{src}.  The map
        is keyed by the L{symbol <Symbol>} that enables the
        transitions.

        A transition is a map from a destination L{state <Symbol>}
        C{dst} to the update instruction that must be applied if that
        transition is selected.

        The same symbol may be used for multiple
        transitions.  If the FAC is deterministic, only one of those
        transitions has an update instruction that is satisfied by the
        FAC counter state."""
        if self.__phi is None:
            self.__buildAutomaton()
        return self.__phi
    phi = property(__get_phi)

    __counterPositions = None
    def __get_counterPositions (self):
        """Implement definition 13.1 from B{HOV09}.

        The return value is the set of all positions leading to
        L{NumericalConstraint} nodes for which either the minimum
        value is not 1 or the maximum value is not unbounded."""
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

    def counterSubPositions (self, pos):
        """Implement definition 13.2 from B{HOV09}.

        This is the subset of L{counterPositions} that occur along the
        path to C{pos}."""
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
            print 'Final %s: %s' % (str(p), ' '.join([ str(_p) for _p in self.counterSubPositions(p)]))

class MultiTermNode (Node):
    """Intermediary for nodes that have multiple child nodes."""
    
    __terms = None
    def __get_terms (self):
        """The set of subordinate terms of the current node."""
        return self.__terms
    terms = property(__get_terms)

    def __init__ (self, *terms, **kw):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(MultiTermNode, self).__init__(**kw)
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

    def __init__ (self, term, min=0, max=1, **kw):
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
        super(NumericalConstraint, self).__init__(**kw)
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
            rv[pp+q] = self._PosConcatTransitionSet(pp, transition_set)
            if q in last_r1:
                last_r1.remove(q)
                for sq1 in self.__term.first:
                    q1 = pp+sq1
                    psi = {}
                    for p1 in self.__term.counterSubPositions(q):
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

    def __init__ (self, *terms, **kw):
        """Term that selects one of a set of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Choice, self).__init__(*terms, **kw)
        
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
                rv[pp + q] = self._PosConcatTransitionSet(pp, transition_set)
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

    def __init__ (self, *terms, **kw):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Sequence, self).__init__(*terms, **kw)

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
                rv[pp + q] = self._PosConcatTransitionSet(pp, transition_set)
        for c in xrange(len(self.terms)-1):
            t = self.terms[c]
            pp = (c,)
            for q in t.last:
                for sq1 in self.terms[c+1].first:
                    q1 = (c+1,) + sq1
                    psi = {}
                    for p1 in t.counterSubPositions(q):
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

    def __init__ (self, *terms, **kw):
        """Term that collects an unordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(All, self).__init__(*terms, **kw)

    def _nullable (self):
        for t in self.terms:
            if not t.nullable:
                return False
        return True

    def __str__ (self):
        return u'&(' + ','.join([str(_t) for _t in self.terms]) + ')'

class Symbol (Node):
    """A leaf term that is a symbol.

    The symbol is represented by the L{metadata} field."""

    _Precedence = 0

    def __init__ (self, symbol, **kw):
        kw['metadata'] = symbol
        super(Symbol, self).__init__(**kw)

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
        return str(self.metadata)
