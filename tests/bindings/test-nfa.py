import unittest
from pyxb.utils.utility import *
from pyxb.utils.utility import _DeconflictSymbols_mixin

'''

class TestThompson (unittest.TestCase):

    def testParticleOne (self):
        t = Thompson(Particle(1,1,'a'))
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([]))
            self.assertTrue(nfa.isFullPath(['a']))
            self.assertFalse(nfa.isFullPath(['a', 'a']))

    def testParticleOptional (self):
        t = Thompson(Particle(0,1,'a'))
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertTrue(nfa.isFullPath([]))
            self.assertTrue(nfa.isFullPath(['a']))
            self.assertFalse(nfa.isFullPath(['a', 'a']))

    def testParticleAny (self):
        t = Thompson(Particle(0,None,'a'))
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertTrue(nfa.isFullPath([]))
            self.assertTrue(nfa.isFullPath(['a']))
            for rep in range(0, 10):
                self.assertTrue(nfa.isFullPath(rep * ['a']))

    def testParticle2Plus (self):
        particle = Particle(2, None, 'a')
        t = Thompson(particle)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            for rep in range(1, 10):
                if particle.minOccurs() <= rep:
                    self.assertTrue(nfa.isFullPath(rep * ['a']))
                else:
                    self.assertFalse(nfa.isFullPath(rep * ['a']))

    def testParticleSome (self):
        particle = Particle(3, 5, 'a')
        t = Thompson(particle)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            for rep in range(1, 10):
                if (particle.minOccurs() <= rep) and (rep <= particle.maxOccurs()):
                    self.assertTrue(nfa.isFullPath(rep * ['a']))
                else:
                    self.assertFalse(nfa.isFullPath(rep * ['a']))

    def testSequence1 (self):
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([ ]))
            self.assertTrue(nfa.isFullPath([ 'a' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testSequence3 (self):
        seq = ModelGroup(ModelGroup.C_SEQUENCE, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([ ]))
            self.assertFalse(nfa.isFullPath([ 'a' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))
            self.assertTrue(nfa.isFullPath([ 'a', 'b', 'c' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'b', 'c', 'd' ]))

    def testChoice1 (self):
        seq = ModelGroup(ModelGroup.C_CHOICE, [ 'a' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([ ]))
            self.assertTrue(nfa.isFullPath([ 'a' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testChoice3 (self):
        seq = ModelGroup(ModelGroup.C_CHOICE, [ 'a', 'b', 'c' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([ ]))
            self.assertTrue(nfa.isFullPath([ 'a' ]))
            self.assertTrue(nfa.isFullPath([ 'b' ]))
            self.assertTrue(nfa.isFullPath([ 'c' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'b' ]))

    def testAll1 (self):
        seq = ModelGroup(ModelGroup.C_ALL, [ 'a' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
            self.assertFalse(nfa.isFullPath([ ]))
            self.assertTrue(nfa.isFullPath([ 'a' ]))
            self.assertFalse(nfa.isFullPath([ 'a', 'a' ]))

    def testAll2 (self):
        seq = ModelGroup(ModelGroup.C_ALL, [ 'a', 'b' ])
        t = Thompson(seq)
        for nfa in (t.nfa(), t.nfa().buildDFA()):
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
        for nfa in (t.nfa(), t.nfa().buildDFA()):
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

    def testDFA (self):
        nfa = FiniteAutomaton()
        q1 = nfa.newState()
        nfa.addTransition(None, nfa.start(), q1)
        nfa.addTransition('a', q1, q1)
        nfa.addTransition('b', q1, q1)
        q2 = nfa.newState()
        nfa.addTransition('a', q1, q2)
        q3 = nfa.newState()
        nfa.addTransition('b', q2, q3)
        nfa.addTransition('b', q3, nfa.end())
        dfa = nfa.buildDFA()

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

class TestSchema (unittest.TestCase):
    def testWsdl (self):
        x = ModelGroup(ModelGroup.C_CHOICE, [ 'a', 'b', 'c' ])
        x = ModelGroup(ModelGroup.C_SEQUENCE, [ Particle(0, None, x) ])
        x = ModelGroup(ModelGroup.C_SEQUENCE, [ Particle(0, None, 'W'), x ])
        x = ModelGroup(ModelGroup.C_SEQUENCE, [ Particle(0, 1, 'd'), x ])
        t = Thompson(x)
        for nfa in ( t.nfa(), t.nfa().buildDFA() ):
            self.assertTrue(nfa.isFullPath([ 'd' ]))
            self.assertFalse(nfa.isFullPath([ 'd', 'd' ]))
                                          
if __name__ == '__main__':
    unittest.main()
    
'''
    
