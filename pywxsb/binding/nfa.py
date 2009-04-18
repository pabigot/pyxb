import unittest
from content import *

# Represent state transitions as a map from states to maps from
# symbols to sets of states.  States are integers.

class FiniteAutomaton (dict):
    """Represent a finite automaton.

    States are integers.  The start and end state are distinguished.
    Transitions are by value; the value None represents an epsilon
    transition."""

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

    def oneStep (self, origin, key):
        """Return the set of states reachable by one transition of key
        from the given origin."""
        return self.setdefault(origin, {}).get(key, set())

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

    def canReach (self, key, origin=None):
        """Return the set of nodes that can be reached from origin
        with any number of epsilon moves and exactly one key move.  If
        no origin is provided, the automaton start state is used."""
        if origin is None:
            origin = [ self.start() ]
        if not isinstance(origin, (list, set, frozenset)):
            origin = [ origin ]
        eps_moves = set(origin)
        key_moves = set()

        last_eps_moves = None
        last_key_moves = None

        while ((last_eps_moves != eps_moves) or (last_key_moves != key_moves)):
            last_eps_moves = eps_moves.copy()
            last_key_moves = key_moves.copy()
            for source in eps_moves:
                eps_moves = eps_moves.union(self.oneStep(source, None))
                key_moves = key_moves.union(self.oneStep(source, key))
            for source in last_key_moves:
                key_moves = key_moves.union(self.oneStep(source, None))
        return key_moves
        
    def isFullPath (self, steps):
        """Return True iff the automaton can be traversed from start
        to end following the given steps, including arbitrary epsilon
        moves."""
        reaches = set( [self.start()] )
        #print 'Starting full path from %s\n%s\n' % (reaches, self)
        for s in steps:
            reaches = self.canReach(s, reaches)
            #print 'Add %s reaches %s' % (s, reaches)
        return self.end() in reaches

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

class Thompson:
    """Create a NFA from a content model.  Reminiscent of Thompson's
    algorithm for creating an NFA from a regular expression."""

    # The NFA 
    __nfa = None

    def nfa (self):
        return self.__nfa

    def __init__ (self, term=None):
        self.__nfa = FiniteAutomaton()
        if term is not None:
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
        for p in particles:
            next_state = self.__nfa.newState()
            self.addTransition(p, start, next_state)
            start = next_state
        self.addTransition(None, start, end)

    def __fromMGChoice (self, particles, start, end):
        # Trivial: start to end for each possibility
        for p in particles:
            self.addTransition(p, start, end)

    def __fromMGAll (self, particles, start, end):
        # Brute force: start to end for each possibility
        for possibility in _Permutations(particles):
            self.__fromMGSequence(possibility, start, end)

    def __fromModelGroup (self, group, start, end):
        # Do the right thing based on the model group compositor
        if ModelGroup.C_ALL == group.compositor():
            return self.__fromMGAll(group.particles(), start, end)
        if ModelGroup.C_CHOICE == group.compositor():
            return self.__fromMGChoice(group.particles(), start, end)
        if ModelGroup.C_SEQUENCE == group.compositor():
            return self.__fromMGSequence(group.particles(), start, end)
        assert False

class TestThompson (unittest.TestCase):

    def testParticleOne (self):
        t = Thompson(Particle(1,1,'a'))
        nfa = t.nfa()
        self.assertFalse(nfa.end() in nfa.canReach(None, nfa.start()))
        self.assertTrue(nfa.end() in nfa.canReach('a', nfa.start()))
        self.assertFalse(nfa.end() in nfa.canReach('a', nfa.canReach('a')))

    def testParticleOptional (self):
        t = Thompson(Particle(0,1,'a'))
        nfa = t.nfa()
        self.assertTrue(nfa.end() in nfa.canReach(None, nfa.start()))
        self.assertTrue(nfa.end() in nfa.canReach('a', nfa.start()))
        self.assertFalse(nfa.end() in nfa.canReach('a', nfa.canReach('a')))

    def testParticleAny (self):
        t = Thompson(Particle(0,None,'a'))
        nfa = t.nfa()
        self.assertTrue(nfa.end() in nfa.canReach(None, nfa.start()))
        self.assertTrue(nfa.end() in nfa.canReach('a', nfa.start()))
        reaches = [ nfa.start() ]
        for rep in range(0, 10):
            reaches = nfa.canReach('a', reaches)
            self.assertTrue(nfa.end() in reaches)

    def testParticle2Plus (self):
        particle = Particle(2, None, 'a')
        t = Thompson(particle)
        nfa = t.nfa()
        reaches = [ nfa.start() ]
        for rep in range(1, 10):
            reaches = nfa.canReach('a', reaches)
            if particle.minOccurs() <= rep:
                self.assertTrue(nfa.end() in reaches)
            else:
                self.assertFalse(nfa.end() in reaches)

    def testParticleSome (self):
        particle = Particle(3, 5, 'a')
        t = Thompson(particle)
        nfa = t.nfa()
        reaches = [ nfa.start() ]
        for rep in range(1, 10):
            reaches = nfa.canReach('a', reaches)
            if (particle.minOccurs() <= rep) and (rep <= particle.maxOccurs()):
                self.assertTrue(nfa.end() in reaches)
            else:
                self.assertFalse(nfa.end() in reaches)

    def testSequence1 (self):
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testSequence3 (self):
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertFalse(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'a', 'b', 'c' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b', 'c', 'd' ]))

    def testChoice1 (self):
        seq = ModelGroup(ModelGroup.C_CHOICE, [ 'a' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testChoice3 (self):
        seq = ModelGroup(ModelGroup.C_CHOICE, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertTrue(nfa.isFullPath([ 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'c' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testAll1 (self):
        seq = ModelGroup(ModelGroup.C_ALL, [ 'a' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'a' ]))

    def testAll2 (self):
        seq = ModelGroup(ModelGroup.C_ALL, [ 'a', 'b' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertFalse(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'a' ]))
        self.assertTrue(nfa.isFullPath([ 'a', 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'b', 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b', 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'b', 'a', 'b' ]))

    def testAll3 (self):
        seq = ModelGroup(ModelGroup.C_ALL, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertFalse(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))
        self.assertFalse(nfa.isFullPath([ 'b', 'a' ]))
        self.assertTrue(nfa.isFullPath([ 'a', 'b', 'c' ]))
        self.assertTrue(nfa.isFullPath([ 'a', 'c', 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'b', 'a', 'c' ]))
        self.assertTrue(nfa.isFullPath([ 'b', 'c', 'a' ]))
        self.assertTrue(nfa.isFullPath([ 'c', 'a', 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'c', 'b', 'a' ]))

class TestFiniteAutomaton (unittest.TestCase):
    def testSubAutomaton (self):
        subnfa = FiniteAutomaton()
        subnfa.addTransition('a', subnfa.start(), subnfa.end())
        nfa = FiniteAutomaton()
        ( start, end ) = nfa.addSubAutomaton(subnfa)
        nfa.addTransition('b', nfa.start(), start)
        nfa.addTransition('c', end, nfa.end())
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath(['b', 'a', 'c']))

    def testSubAutomaton (self):
        subnfa = FiniteAutomaton()
        subnfa.addTransition('a', subnfa.start(), subnfa.end())
        nfa = FiniteAutomaton()
        ( start, end ) = nfa.addSubAutomaton(subnfa)
        nfa.addTransition('b', nfa.start(), start)
        nfa.addTransition(None, end, nfa.end())
        ( start, end ) = nfa.addSubAutomaton(subnfa)
        nfa.addTransition(None, nfa.start(), start)
        nfa.addTransition('b', end, nfa.end())

        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath(['b', 'a']))
        self.assertTrue(nfa.isFullPath(['a', 'b']))
        self.assertFalse(nfa.isFullPath(['a', 'a']))
        self.assertFalse(nfa.isFullPath(['b', 'a', 'b']))
        self.assertFalse(nfa.isFullPath(['a', 'b', 'a']))

class TestPermutations (unittest.TestCase):
    def testPermutations (self):
        p1 = set(_Permutations(['a']))
        self.assertEqual(1, len(p1))

        p2 = set(_Permutations(['a', 'b']))
        self.assertEqual(2, len(p2))
        self.assertTrue(('a', 'b') in p2)
        self.assertTrue(('b', 'a') in p2)

        p3 = set(_Permutations(['a', 'b', 'c']))
        self.assertEqual(6, len(p3))
        self.assertTrue(('a', 'b', 'c') in p3)
        self.assertTrue(('a', 'c', 'b') in p3)
        self.assertTrue(('b', 'a', 'c') in p3)
        self.assertTrue(('b', 'c', 'a') in p3)
        self.assertTrue(('c', 'a', 'b') in p3)
        self.assertTrue(('c', 'b', 'a') in p3)

if __name__ == '__main__':
    unittest.main()
    
