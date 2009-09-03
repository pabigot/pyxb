import unittest
from pyxb.utils.unicode import *

class TestCodePointSet (unittest.TestCase):
    def testConstructor (self):
        c = CodePointSet()
        self.assertEqual(c.asTuples(), [])
        c = CodePointSet(10, 15)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15) ])
        self.assertRaises(TypeError, CodePointSet, [10, 15])

    def testCopyConstructor (self):
        c = CodePointSet()
        c.add(10)
        c.add(15)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15) ])
        c2 = CodePointSet(c)
        self.assertEqual(c2.asTuples(), [ (10, 10), (15, 15) ])
        c.add(20)
        self.assertEqual(c.asTuples(), [ (10, 10), (15, 15), (20, 20) ])
        self.assertEqual(c2.asTuples(), [ (10, 10), (15, 15) ])

    def testNegate (self):
        c = CodePointSet().negate()
        self.assertEqual(c.asTuples(), [ (0, 0x10FFFF) ])
        c2 = c.negate()
        self.assertEqual(c2.asTuples(), [])

    def testAddSingle (self):
        c = CodePointSet()
        c.add(15)
        self.assertEqual(c.asTuples(), [ (15, 15) ])
        c.add(15)
        self.assertEqual(c.asTuples(), [ (15, 15) ])

        c.add(0)
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15) ])
        n = c.negate()
        self.assertEqual(n.asTuples(), [ (1, 14), (16, 0x10FFFF) ])

        n.add(0)
        self.assertEqual(n.asTuples(), [ (0, 14), (16, 0x10FFFF) ])
        n.add(15)
        self.assertEqual(n.asTuples(), [ (0, 0x10FFFF) ])

    def testRemoveRange (self):
        base = CodePointSet(0, 15, (20, 30), (40, 60))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # 0 1 15 16 20 31 40 61
        c = CodePointSet(base).subtract( (22, 25) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 21), (26, 30), (40, 60) ])
        c = CodePointSet(base).subtract( (22, 35) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 21), (40, 60) ])
        c = CodePointSet(base).subtract( (35, 55) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (56, 60) ])
        c = CodePointSet(base).subtract( (35, 38) )
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])

    def testAddRange (self):
        base = CodePointSet(0, 15)
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15) ])
        base.add((20, 30))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30) ])
        base.add((40, 60))
        self.assertEqual(base.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # 0 1 15 16 20 31 40 61
        # Bridge missing range
        c = CodePointSet(base).add((1, 15))
        self.assertEqual(c.asTuples(), [ (0, 15), (20, 30), (40, 60) ])

        # Insert in middle of missing range
        c = CodePointSet(base).add((35, 38))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 38), (40, 60) ])
        # Join following range
        c = CodePointSet(base).add((35, 39))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 60) ])
        c = CodePointSet(base).add((35, 40))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 60) ])

        # 0 1 15 16 20 31 40 61
        # Insert into middle of existing range
        c = CodePointSet(base).add((22, 25))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (40, 60) ])
        # Extend existing range
        c = CodePointSet(base).add((22, 35))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 35), (40, 60) ])
        c = CodePointSet(base).add((22, 38))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 38), (40, 60) ])
        # Span missing range
        c = CodePointSet(base).add((22, 39))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])
        c = CodePointSet(base).add((22, 40))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])
        c = CodePointSet(base).add((22, 41))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 60) ])
        
        # 0 1 15 16 20 31 40 61
        c = CodePointSet(base).add((15, 18))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 18), (20, 30), (40, 60) ])
        c = CodePointSet(base).add((35, 65))
        self.assertEqual(c.asTuples(), [ (0, 0), (15, 15), (20, 30), (35, 65) ])
        c = CodePointSet(base).add((12, 16))
        self.assertEqual(c.asTuples(), [ (0, 0), (12, 16), (20, 30), (40, 60) ])
        

if '__main__' == __name__:
    unittest.main()
            
        
