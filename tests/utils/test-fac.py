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
        au = self.a.buildAutomaton()
        cfg = Configuration(au)
        self.assertFalse(cfg.isAccepting())
        cfg.step('a')
        self.assertTrue(cfg.isAccepting())
        cfg.reset()
        self.assertFalse(cfg.isAccepting())
        self.assertRaises(RecognitionError, cfg.step, 'b')

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

    def testAllConstruction (self):
        tt = All(Symbol('a'), Symbol('b'))
        au = tt.buildAutomaton()
        self.assertEqual(1, len(au.states))
        st = iter(au.states).next()
        self.assertTrue(st.isUnorderedCatenation)

    # Example from Kilpelainen & Tuhkanen, "Towards Efficient
    # Implementation of XML Schema Content Models"
    def testKT2004 (self):
        a = Symbol('a')
        x = NumericalConstraint(Symbol('b'), 0, 1)
        x = NumericalConstraint(Sequence(x, Symbol('c')), 1, 2)
        x = Sequence(NumericalConstraint(Symbol('a'), 0, 1), x, Choice(Symbol('a'), Symbol('d')))
        x = NumericalConstraint(x, 3, 4)
        cfg = Configuration(x.buildAutomaton())
        for word in ['cacaca', 'abcaccdacd']:
            cfg.reset()
            for c in word:
                cfg = cfg.step(c)
            self.assertTrue(cfg.isAccepting())
        for word in ['caca', 'abcaccdac']:
            cfg.reset()
            for c in word:
                cfg = cfg.step(c)
            self.assertFalse(cfg.isAccepting())
        word = list('ad')
        cfg.reset()
        cfg = cfg.step(word.pop(0))
        try:
            cfg = cfg.step(word.pop(0))
            self.fail("Expected recognition error")
        except RecognitionError as e:
            self.assertEqual(e.symbol, 'd')
            self.assertEqual(e.expected, ['b', 'c'])
        except Exception as e:
            self.fail("Unexpected exception %s" % (e,))
            
    # Example from email by Casey Jordan to xmlschema-dev mailing list
    # 20100810: http://lists.w3.org/Archives/Public/xmlschema-dev/2010Aug/0008.html
    # This expression is non-deterministic, but at the end only one path is
    # accepting.
    def testCJ2010 (self):
        x = NumericalConstraint(Symbol('b'), 1, 2)
        x = NumericalConstraint(Choice(x, Symbol('c')), 2, 2)
        x = Sequence(Symbol('a'), x, Symbol('d'))
        cfg = Configuration(x.buildAutomaton())
        word = list('abbd')
        cfg = cfg.step(word.pop(0))
        cfg = cfg.step(word.pop(0))
        try:
            cfg = cfg.step(word.pop(0))
            self.fail('Expected nondeterminism exception')
        except NondeterministicSymbolError as e:
            word.insert(0, e.symbol)
        mcfg = MultiConfiguration(cfg)
        mcfg = mcfg.step(word.pop(0))
        mcfg = mcfg.step(word.pop(0))
        accepting = mcfg.acceptingConfigurations()
        self.assertEqual(1, len(accepting))

    def testExpandAll (self):
        a = Symbol('a')
        b = Symbol('b')
        c = Symbol('c')
        all = All.CreateTermTree(a, b, c)
        import itertools
        cfg = Configuration(all.buildAutomaton())
        for word in itertools.permutations('abc'):
            cfg.reset()
            for c in word:
                cfg.step(c)
            self.assertTrue(cfg.isAccepting())
        cfg.reset()
        cfg.step('a')
        cfg.step('b')
        self.assertFalse(cfg.isAccepting())

    def testTransitionChain (self):
        cc1 = CounterCondition(0, 1)
        cc2 = CounterCondition(3, None)
        psi = frozenset([UpdateInstruction(cc1, False), UpdateInstruction(cc2, True)])
        s1 = State('1', True)
        s2 = State('2', False)
        x1 = Transition(s1, psi)
        x2 = Transition(s2, [UpdateInstruction(cc2, False)])
        x1b = x1.chainTo(x2)
        self.assertNotEqual(x1, x1b)
        self.assertEqual(id(x1.updateInstructions), id(x1b.updateInstructions))
        self.assertEqual(x1.nextTransition, None)
        self.assertEqual(x1b.nextTransition, x2)

    def testTransitionLayers (self):
        a1 = All(NumericalConstraint(Symbol('a'), 0, 1), Symbol('b'), NumericalConstraint(Symbol('c'), 0, 1))
        a2 = All(Symbol('d'), NumericalConstraint(Symbol('e'), 0, 1), Symbol('f'))
        tt = NumericalConstraint(Sequence(NumericalConstraint(a1, 0, 1), NumericalConstraint(a2, 0, 1), Symbol('l')), 0, 3)
        au = tt.buildAutomaton()
        topcfg = Configuration(au)
        cfg = topcfg.step('b')
        cfg = cfg.step('a')
        cfg = cfg.step('e')
        topcfg.reset()
        cfg = topcfg.step('a')
        # Can't move to 'e' until the required component 'b' of a1 has
        # been provided.  'c' is also permitted.
        try:
            cfg = cfg.step('e')
            self.fail('Expected recognition error')
        except RecognitionError as e:
            self.assertEqual(e.symbol, 'e')
            self.assertEqual(frozenset(e.expected), frozenset(['c', 'b']))
        except Exception as e:
            self.fail('Unexpected exception %s' % (e,))
        cfg = cfg.step('b')
        cfg = cfg.step('e')

    def testAllTree (self):
        a1 = All(Symbol('a'), Symbol('b'), Symbol('c'))
        a2 = All(Symbol('d'), Symbol('e'), Symbol('f'))
        ex = Sequence(NumericalConstraint(Symbol('f'), 0, 1), a1, NumericalConstraint(a2, 0, 1), Symbol('l'))
        # print ex
        # f^(0,1).&(a,b,c).&(d,e,f)^(0,1).l
        au = ex.buildAutomaton()
        cfg = Configuration(au)
        for word in ['fabcl', 'fcabl']:
            cfg.reset()
            for c in word:
                cfg = cfg.step(c)
            self.assertTrue(cfg.isAccepting())
    
    def testNonAllTree (self):
        a1 = Symbol('a')
        a2 = Symbol('d')
        ex = Sequence(NumericalConstraint(Symbol('f'), 0, 1), a1, NumericalConstraint(a2, 0, 1), Symbol('l'))
        # f?ad?l
        au = ex.buildAutomaton()
        cfg = Configuration(au)
        # This checks that the transition from a can jump over the d and find the l.
        for word in ['fal', 'fadl']:
            cfg.reset()
            for c in word:
                cfg = cfg.step(c)
            self.assertTrue(cfg.isAccepting())


if __name__ == '__main__':
    unittest.main()
