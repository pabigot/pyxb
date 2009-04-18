import unittest
from content import *

class Element (object):
    __name = None

    def __init__ (self, name):
        self.__name = name

    def name (self): return self.__name

    def __str__ (self): return self.name()


# Represent state transitions as a map from states to maps from
# symbols to sets of states.  States are integers.

class NFA (dict):
    __stateID = -1
    __start = None
    __end = None

    def __init__ (self):
        self.__end = self.newState()
        self.__start = self.newState()

    def newState (self):
        self.__stateID += 1
        self.setdefault(self.__stateID, {})
        return self.__stateID

    def start (self): return self.__start

    def end (self): return self.__end

    def addTransition (self, key, start, end):
        assert end is not None
        self.setdefault(start, {}).setdefault(key, set()).add(end)
        return self

    def ok (self, key, start, end):
        return end in self[start].get(key, set())

    def oneStep (self, node, key):
        return self.setdefault(node, {}).get(key, set())

    def canReach (self, key, start=None, with_epsilon=False):
        if start is None:
            start = [ self.start() ]
        if not isinstance(start, (list, set, frozenset)):
            start = [ start ]
        eps_moves = set(start)
        key_moves = set()

        last_eps_moves = None
        last_key_moves = None

        while ((last_eps_moves != eps_moves) or (last_key_moves != key_moves)):
            last_eps_moves = eps_moves.copy()
            last_key_moves = key_moves.copy()
            for start in eps_moves:
                eps_moves = eps_moves.union(self.oneStep(start, None))
                key_moves = key_moves.union(self.oneStep(start, key))
            for start in last_key_moves:
                key_moves = key_moves.union(self.oneStep(start, None))
        if with_epsilon:
            return eps_moves.union(key_moves)
        return key_moves
        
    def isFullPath (self, steps):
        reaches = set( [self.start()] )
        for s in steps:
            reaches = self.canReach(s, reaches)
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
        for start in states:
            if start == self.end():
                strings.append('%s terminates' % (start,))
                continue
            transitions = self[start]
            if 0 == len(transitions):
                strings.append('%s dead-ends' % (start,))
                continue
            for step in transitions.keys():
                strings.append('%s via %s to %s' % (start, step, ' '.join([ str(_s) for _s in transitions[step]])))
        return "\n".join(strings)

class Thompson:
    """Create a NFA from a content model."""

    __nfa = None

    def nfa (self): return self.__nfa

    def __init__ (self, term):
        self.__nfa = NFA()
        self.addTransition(term, self.__nfa.start(), self.__nfa.end())

    def addTransition (self, element, start, end):
        if isinstance(element, Particle):
            return self.fromParticle(element, start, end)
        if isinstance(element, ModelGroup):
            return self.fromModelGroup(element, start, end)
        self.__nfa.addTransition(element, start, end)

    def fromParticle (self, particle, start, end):
        #print '# %d to %s of %s' % (particle.minOccurs(), particle.maxOccurs(), particle.term())

        if 0 == particle.minOccurs():
            self.addTransition(None, start, end)

        cur_start = next_end = start
        for step in range(0, particle.minOccurs()):
            cur_start = next_end
            next_end = self.__nfa.newState()
            self.addTransition(particle.term(), cur_start, next_end)

        if None is particle.maxOccurs():
            if next_end == start:
                self.addTransition(particle.term(), start, end)
                next_end = end
            self.addTransition(None, next_end, cur_start)
        else:
            for step in range(particle.minOccurs(), particle.maxOccurs()):
                cur_start = next_end
                next_end = self.__nfa.newState()
                self.addTransition(None, cur_start, end)
                self.addTransition(particle.term(), cur_start, next_end)
        self.addTransition(None, next_end, end)

    def __fromMGSequence (self, particles, start, end):
        for p in particles:
            next_state = self.__nfa.newState()
            self.addTransition(p, start, next_state)
            start = next_state
        self.addTransition(None, start, end)

    def __fromMGChoice (self, particles, start, end):
        for p in particles:
            self.addTransition(p, start, end)

    def fromModelGroup (self, group, start, end):
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
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testChoice3 (self):
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        nfa = t.nfa()
        self.assertFalse(nfa.isFullPath([ ]))
        self.assertTrue(nfa.isFullPath([ 'a' ]))
        self.assertTrue(nfa.isFullPath([ 'b' ]))
        self.assertTrue(nfa.isFullPath([ 'c' ]))
        self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))


'''
a = Element('a')

t = Thompson(a)
ex = Particle(1, 1, a)
Thompson(Particle(1, 1, a))
Thompson(Particle(0, 1, a))
Thompson(Particle(1, 2, a))
Thompson(Particle(3, 5, a))
Thompson(Particle(2, None, a))
ex = Particle(0, 1, a)
ex = Particle(2, 5, a)
ex = Particle(2, None, a)

ex = Particle(1, 1, ModelGroup(ModelGroup.C_SEQUENCE, [ Particle(1,1,'a'), Particle(1,1,'b')]))
'''
if __name__ == '__main__':
    #Thompson(Particle(0,None,'a'))
    unittest.main()
    
