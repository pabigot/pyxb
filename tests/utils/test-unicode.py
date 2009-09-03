import unittest
from pyxb.utils.unicode import *

class TestCodePointSet (unittest.TestCase):
    def testConstructor (self):
        c = CodePointSet()
        self.assertEqual(c.asTuples(), [])

    def testNegate (self):
        c = CodePointSet().negate()
        self.assertEqual(c.asTuples(), [ (0, 0x10FFFF) ])

    def testAdd (self):
        c = CodePointSet()
        c.add(15)
        print c._codepoints()
        self.assertEqual(c.asTuples(), [ (15, 15) ])
        self.assertRaises(CodePointSetError, c.add, 15)
            

if '__main__' == __name__:
    unittest.main()
            
        
