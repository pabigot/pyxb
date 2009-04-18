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
        self.setdefault(start, {}).setdefault(key, set()).add(end)
        return self

    def ok (self, key, start, end):
        return end in self[start].get(key, set())

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
            transitions = self.get(start, None)
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
        self.fromTerm(term, self.__nfa.start(), self.__nfa.end())
        print self.__nfa
        print

    def fromElement (self, element, start, end):
        self.addTransition(element, start, end)
        return self

    def addTransition (self, element, start, end):
        self.__nfa.addTransition(element, start, end)

    def fromParticle (self, particle, start, end):
        print '# %d to %s of %s' % (particle.minOccurs(), particle.maxOccurs(), particle.term())

        cur_start = None
        next_end = self.__nfa.newState()
        self.addTransition(None, start, next_end)

        if 0 == particle.minOccurs():
            self.addTransition(None, start, end)

        for step in range(0, particle.minOccurs()):
            cur_start = next_end
            next_end = self.__nfa.newState()
            self.addTransition(particle.term(), cur_start, next_end)

        if None is particle.maxOccurs():
            self.addTransition(None, next_end, cur_start)
        else:
            for step in range(particle.minOccurs(), particle.maxOccurs()):
                cur_start = next_end
                next_end = self.__nfa.newState()
                self.addTransition(None, cur_start, end)
                self.addTransition(particle.term(), cur_start, next_end)
        self.addTransition(None, next_end, end)

    def fromTerm (self, term, start, end):
        if isinstance(term, Particle):
            return self.fromParticle(term, start, end)
        return self.fromElement(term, start, end)

class TestThompson (unittest.TestCase):

    def testParticleOne (self):
        t = Thompson(Particle(1,1,'a'))
        nfa = t.nfa()
        print dict.__str__(nfa)
        self.assertEquals(4, len(nfa))
        self.assertTrue(nfa.ok(None, nfa.start(), 2))
        self.assertTrue(nfa.ok('a', 2, 3))
        self.assertTrue(nfa.ok(None, 3, 0))
        self.assertFalse(nfa.ok(None, 1, 0))

    def testParticleOptional (self):
        t = Thompson(Particle(0,1,'a'))
        nfa = t.nfa()
        print dict.__str__(nfa)
        self.assertEquals(4, len(nfa))
        self.assertTrue(nfa.ok(None, nfa.start(), 2))
        self.assertTrue(nfa.ok('a', 2, 3))
        self.assertTrue(nfa.ok(None, 3, 0))
        self.assertTrue(nfa.ok(None, 1, 0))

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
    unittest.main()
    
