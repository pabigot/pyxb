from pyxb.utils.fac import *
import unittest

class TestFAC (unittest.TestCase):

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
        self.assertEqual('a', self.a.metadata)

    def testNumericalConstraint (self):
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
        x = NumericalConstraint(self.a, 0, 1)
        self.assertTrue(x.nullable)
        self.assertFalse(self.a.nullable)
        self.assertFalse(self.aOb.nullable)
        self.assertFalse(self.aTb.nullable)
        self.assertFalse(self.aXb.nullable)
        x = NumericalConstraint(self.a, 1, 4)
        self.assertFalse(x.nullable)

    def testFirst (self):
        null_position = frozenset([()])
        p0 = frozenset([(0,)])
        p1 = frozenset([(1,)])
        p0or1 = frozenset(set(p0).union(p1))
        self.assertEqual(null_position, self.a.first)
        for p in self.a.first:
            self.assertEqual(self.a, self.a.posNodeMap[p])
        self.assertEqual(p0or1, self.aOb.first)
        self.assertEqual(p0, self.aTb.first)
        for p in self.aTb.first:
            self.assertEqual(self.a, self.aTb.posNodeMap[p])
        rs = set()
        for p in self.a2ObTc.first:
            rs.add(self.a2ObTc.posNodeMap[p])
        self.assertEqual(frozenset([self.a, self.b]), rs)

    def testLast (self):
        null_position = frozenset([()])
        p0 = frozenset([(0,)])
        p1 = frozenset([(1,)])
        p0or1 = frozenset(set(p0).union(p1))
        self.assertEqual(null_position, self.a.last)
        self.assertEqual(p0or1, self.aOb.last)
        self.assertEqual(p1, self.aTb.last)
        rs = set()
        for p in self.a2ObTc.last:
            rs.add(self.a2ObTc.posNodeMap[p])
        self.assertEqual(frozenset([self.a, self.c]), rs)

    def testWalkTermTree (self):
        pre_pos = []
        post_pos = []
        set_sym_pos = lambda _n,_p,_a: isinstance(_n, Symbol) and _a.append(_p)
        self.ex.walkTermTree(set_sym_pos, None, pre_pos)
        self.ex.walkTermTree(None, set_sym_pos, post_pos)
        self.assertEqual(pre_pos, post_pos)
        self.assertEqual([(0,0,0),(0,1,0),(0,1,1)], pre_pos)

    def testCounterPositions (self):
        self.assertEqual(frozenset([(), (0,0)]), self.ex.counterPositions)

    def testFollow (self):
        m = self.a.follow
        self.assertEqual(1, len(m))
        self.assertEqual([((), frozenset())], m.items())

    def testValidateAutomaton (self):
        a = Symbol('a')
        x = Sequence(a, a)
        self.assertRaises(InvalidTermTreeError, x.buildAutomaton)

    def testInternals (self):
        #print self.ex.facToString()
        au = self.ex.buildAutomaton()
        #print str(au)

    def testAutomaton (self):
        au = self.ex.buildAutomaton()
        cfg = Configuration(au)
        for c in 'aabcaa':
            cfg.step(c)
        self.assertTrue(cfg.isAccepting())

    def testKT2004 (self):
        a = Symbol('a')
        x = NumericalConstraint(Symbol('b'), 0, 1)
        x = NumericalConstraint(Sequence(x, Symbol('c')), 1, 2)
        x = Sequence(NumericalConstraint(Symbol('a'), 0, 1), x, Choice(Symbol('a'), Symbol('d')))
        x = NumericalConstraint(x, 3, 4)
        au = Configuration(x.buildAutomaton())
        for word in ['cacaca', 'abcaccdacd']:
            au.reset()
            for c in word:
                au.step(c)
            self.assertTrue(au.isAccepting())
        for word in ['caca', 'abcaccdac']: # , 'ad']:
            au.reset()
            for c in word:
                au.step(c)
            self.assertFalse(au.isAccepting())

    '''
    def testCJ2010 (self):
        x = NumericalConstraint(Symbol('b'), 1, 2)
        x = NumericalConstraint(Choice(x, Symbol('c')), 2, 2)
        x = Sequence(Symbol('a'), x, Symbol('d'))
        au = Configuration(x.buildAutomaton())
        for c in 'abbd':
            au.step(c)
        self.assertTrue(au.isFinal())
    '''

if __name__ == '__main__':
    unittest.main()
