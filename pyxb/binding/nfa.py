# Copyright 2009, Peter A. Bigot
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

"""Finite automata classes that support content model management."""

from pyxb.xmlschema.structures import Particle, ModelGroup

# Represent state transitions as a map from states to maps from
# symbols to sets of states.  States are integers.

class FiniteAutomaton (dict):
    """Represent a finite automaton.

    The FiniteAutomaton instance is a map from states to sets of transitions.

    A transition is a map from a key to a set of states.

    States are integers.  The start and end state are distinguished.
    Transitions are by value, and are one of ElementDeclaration,
    ModelGroup[all], and Wildcard.  The value None represents an
    epsilon transition.

    """

    # A unique identifier used for creating states
    __stateID = -1

    # The state serving as the automaton start.
    __start = None

    # The state serving as the automaton end.
    __end = None

    def __init__ (self):
        self.__end = self.newState()
        self.__start = self.newState()

    def newState (self):
        """Create a new node in the automaton.  No transitions are added."""
        self.__stateID += 1
        self.setdefault(self.__stateID, {})
        return self.__stateID

    def start (self):
        """Obtain the start node of the automaton."""
        return self.__start

    def end (self):
        """Obtain the end node of the automaton."""
        return self.__end

    def addTransition (self, key, source, destination):
        """Add a transition on key from the source state to the destination state."""
        assert destination is not None
        self.setdefault(source, {}).setdefault(key, set()).add(destination)
        return self

    def ok (self, key, source, destination):
        """Return True iff the automaton can transition from source to
        destination on key."""
        return destination in self[source].get(key, set())

    def addSubAutomaton (self, nfa):
        """Copy the given automaton into this one.  Returns a pair of
        the start and end states of the copied sub-automaton."""
        nfa_base_id = self.__stateID+1
        self.__stateID += len(nfa)
        for sub_state in nfa.keys():
            ssid = sub_state + nfa_base_id
            ss_map = self.setdefault(ssid, {})
            for key in nfa[sub_state]:
                ss_map.setdefault(key, set())
                ss_map[key] = ss_map[key].union(set([ (nfa_base_id+_i) for _i in nfa[sub_state][key]]))
        return (nfa_base_id+nfa.start(), nfa_base_id+nfa.end())

    def alphabet (self):
        """Determine the keys that allow transitions in the automaton."""
        elements = set()
        for s in self.keys():
            transitions = self[s]
            elements = elements.union(transitions.keys())
        elements.discard(None)
        return elements
    
    def isFullPath (self, steps):
        """Return True iff the automaton can be traversed from start
        to end following the given steps, including arbitrary epsilon
        moves."""
        reaches = self.epsilonClosure([self.start()])
        #print 'Starting full path from %s\n%s\n' % (reaches, self)
        for s in steps:
            reaches = self.epsilonClosure(self.move(reaches, s))
        return self.end() in reaches

    def move (self, states, key):
        """Determine the set of states reachable from the input set of states by one key transition."""
        next_states = set()
        for s in states:
            next_states = next_states.union(self[s].get(key, set()))
        #print 'Move from %s via %s is %s' % (states, key, next_states)
        return next_states

    def epsilonClosure (self, states):
        """Calculate the epsilon closure of the given set of states."""
        states = set(states)
        while True:
            new_states = states.union(self.move(states, None))
            if states == new_states:
                return states
            states = new_states

    def reverseTransitions (self):
        reverse_map = { }
        for state in self.keys():
            transitions = self[state]
            for key in transitions.keys():
                [ reverse_map.setdefault(_s, {}).setdefault(key, set()).add(state) for _s in transitions[key] ]
        #print reverse_map
        return reverse_map

    def minimizeDFA (self, final_states):
        nonfinal_states = tuple(set(self.keys()).difference(set(final_states)))
        alphabet = self.alphabet()
        reverse_map = self.reverseTransitions()
        work = set([ final_states, nonfinal_states ])
        partition = work.copy()
        while 0 < len(work):
            states = set(work.pop())
            #print 'State %s, partition %s' % (states, partition)
            for key in alphabet:
                sources = set()
                [ sources.update(reverse_map.get(_s, {}).get(key, set())) for _s in states ]
                new_partition = set()
                for r in partition:
                    rs = set(r)
                    if (0 < len(sources.intersection(rs))) and (0 < len(rs.difference(sources))):
                        r1 = tuple(rs.intersection(sources))
                        r2 = tuple(rs.difference(r1))
                        #print 'Split on %s: %s and %s' % (key, r1, r2)
                        new_partition.add(r1)
                        new_partition.add(r2)
                        if r in work:
                            work.remove(r)
                            work.add(r1)
                            work.add(r2)
                        elif len(r1) <= len(r2):
                            work.add(r1)
                        else:
                            work.add(r2)
                    else:
                        new_partition.add(r)
                partition = new_partition
        translate_map = { }
        min_dfa = FiniteAutomaton()
        for p in partition:
            if self.start() in p:
                new_state = min_dfa.start()
            elif self.end() in p:
                new_state = min_dfa.end()
            else:
                new_state = min_dfa.newState()
            #print 'Convert %s to %s' % (p, new_state)
            for max_state in p:
                assert max_state not in translate_map
                translate_map[max_state] = new_state

        for f in final_states:
            self.addTransition(None, f, self.end())
        #print 'DFA: %s' % (self,)
        for (state, transitions) in self.items():
            for (key, destination) in transitions.items():
                assert 1 == len(destination)
                d = destination.copy().pop()
                #print 'Old: %s via %s to %s\nNew: %s via %s to %s' % (state, key, d, translate_map[state], key, translate_map[d])
                min_dfa.addTransition(key, translate_map[state], translate_map[d])

        # Just in case self.start() and self.end() are in the same partition
        min_dfa.addTransition(None, translate_map[self.end()], min_dfa.end())
        #print 'Final added %d jump to %d' % (translate_map[self.end()], min_dfa.end())

        #print 'DFA: %s' % (self,)
        #print 'Start: %s' % (translate_map[self.start()],)
        #print 'Final: %s' % (set([ translate_map[_s] for _s in final_states ]).pop(),)
        #print 'Partition: %s' % (partition,)
        #print 'Minimized: %s' % (min_dfa,)
        #print "Resulting DFA:\n%s\n\n" % (min_dfa,)
        #print 'Minimal DFA has %d states, original had %d' % (len(min_dfa), len(self))
        return min_dfa
        
    def buildDFA (self):
        """Build a deterministic finite automaton that accepts the
        same language as this one.

        The resulting automaton has epsilon transitions only from
        terminal states to the DFA distinguished end state."""

        #print "Building DFA from NFA:\n%s\n" % (self,)
        dfa = FiniteAutomaton()
        ps0 = tuple(self.epsilonClosure([ dfa.start() ]))
        #print "Start state is %s" % (ps0,)
        pset_to_state = { ps0 : dfa.start() }
        changing = True
        alphabet = self.alphabet()
        while changing:
            changing = False
            for (psi, dfa_state) in pset_to_state.items():
                for key in alphabet:
                    assert key is not None
                    ns = tuple(self.epsilonClosure(self.move(psi, key)))
                    if 0 == len(ns):
                        #print 'From %s via %s is dead' % (psi, key)
                        continue
                    #print 'From %s via %s can reach %s' % (psi, key, ns)
                    new_state = pset_to_state.get(ns, None)
                    if new_state is None:
                        new_state = dfa.newState()
                        pset_to_state[ns] = new_state
                        #print "New state %d is %s" % (new_state, ns)
                    if not dfa.ok(key, dfa_state, new_state):
                        changing = True
                        dfa.addTransition(key, dfa_state, new_state)
        final_states = set()
        for (psi, dfa_state) in pset_to_state.items():
            if self.end() in psi:
                final_states.add(dfa_state)
        return dfa.minimizeDFA(tuple(final_states))

    def __str__ (self):
        states = set(self.keys())
        elements = set()
        for k in self.keys():
            transitions = self[k]
            elements = elements.union(transitions.keys())
            for step in transitions.keys():
                states = states.union(transitions[step])
        states = list(states)
        states.sort()
        strings = []
        for source in states:
            if source == self.end():
                strings.append('%s terminates' % (source,))
                continue
            transitions = self[source]
            if 0 == len(transitions):
                strings.append('%s dead-ends' % (source,))
                continue
            for step in transitions.keys():
                strings.append('%s via %s to %s' % (source, step, ' '.join([ str(_s) for _s in transitions[step]])))
        return "\n".join(strings)

def _Permutations (particles):
    if 1 == len(particles):
        yield tuple(particles)
    else:
        for i in range(len(particles)):
            this = particles[i]
            rest = particles[:i] + particles[i+1:]
            for p in _Permutations(rest):
                yield (this,) + p

class AllWalker (object):
    """A list of minimized DFAs each of which is a single option within
    an ALL model group."""
    __particles = None

    def __init__ (self):
        self.__particles = [ ]

    def particles (self): return  self.__particles

    def add (self, dfa, is_required):
        self.__particles.append( ( dfa, is_required ) )

class Thompson:
    """Create a NFA from a content model.  Reminiscent of Thompson's
    algorithm for creating an NFA from a regular expression.  See
    U{http://portal.acm.org/citation.cfm?doid=363387}"""

    # The NFA 
    __nfa = None

    def nfa (self):
        return self.__nfa

    def __init__ (self, term=None):
        self.__nfa = FiniteAutomaton()
        if term is not None:
            #assert isinstance(term, Particle)
            self.addTransition(term, self.__nfa.start(), self.__nfa.end())

    def addTransition (self, term, start, end):
        """Interpret the term and update the NFA to support a path
        from start to end that is consistent with the term.

        Particles express looping operations with minimum and maximum
        iteration counts.

        Model groups express control structures: ordered and unordered
        sequences, and alternatives.

        Anything else is assumed to be a character in the automaton
        alphabet.
        """
        if isinstance(term, Particle):
            return self.__fromParticle(term, start, end)
        if isinstance(term, ModelGroup):
            return self.__fromModelGroup(term, start, end)
        self.__nfa.addTransition(term, start, end)

    def __fromParticle (self, particle, start, end):
        """Add transitions to interpret the particle."""

        #print '# %d to %s of %s' % (particle.minOccurs(), particle.maxOccurs(), particle.term())

        # If possible, epsilon transition straight from start to end.
        if 0 == particle.minOccurs():
            self.addTransition(None, start, end)

        # Add term transitions from start through the minimum number
        # of instances of the term.
        cur_start = next_end = start
        for step in range(0, particle.minOccurs()):
            cur_start = next_end
            next_end = self.__nfa.newState()
            self.addTransition(particle.term(), cur_start, next_end)

        if None is particle.maxOccurs():
            # Add a back loop to repeat the last instance of the term
            # (creating said instance, if we haven't already)
            if next_end == start:
                self.addTransition(particle.term(), start, end)
                next_end = end
            self.addTransition(None, next_end, cur_start)
        else:
            # Add additional terms up to the maximum, with a short-cut
            # exit for those above the minOccurs value.
            for step in range(particle.minOccurs(), particle.maxOccurs()):
                cur_start = next_end
                next_end = self.__nfa.newState()
                self.addTransition(None, cur_start, end)
                self.addTransition(particle.term(), cur_start, next_end)
        # Leave the sub-FA
        self.addTransition(None, next_end, end)

    def __fromMGSequence (self, particles, start, end):
        # Just step from one to the next
        #print '# Sequence of %s' % (particles,)
        for p in particles:
            next_state = self.__nfa.newState()
            self.addTransition(p, start, next_state)
            start = next_state
        self.addTransition(None, start, end)

    def __fromMGChoice (self, particles, start, end):
        # Start to end for each choice, but make the choice stage
        # occur once (in case a particle adds a transition from end to
        # start.
        for p in particles:
            choice_start = self.__nfa.newState()
            choice_end = self.__nfa.newState()
            self.addTransition(None, start, choice_start)
            self.addTransition(p, choice_start, choice_end)
            self.addTransition(None, choice_end, end)

    def __fromMGAll (self, particles, start, end):
        # All is too ugly: exponential state growth.  Use a special
        # construct instead.
        walker = AllWalker()
        for p in particles:
            walker.add(Thompson(p).nfa().buildDFA(), 0 < p.minOccurs())
        self.addTransition(walker, start, end)

    def __fromModelGroup (self, group, start, end):
        # Do the right thing based on the model group compositor
        if ModelGroup.C_ALL == group.compositor():
            return self.__fromMGAll(group.particles(), start, end)
        if ModelGroup.C_CHOICE == group.compositor():
            return self.__fromMGChoice(group.particles(), start, end)
        if ModelGroup.C_SEQUENCE == group.compositor():
            return self.__fromMGSequence(group.particles(), start, end)
        assert False
