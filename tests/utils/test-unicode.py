import unittest
from pyxb.utils.unicode import *

class TestCodePointSet (unittest.TestCase):
    def testConstructor (self):
        c = CodePointSet()
        self.assertEqual(c.asTuples(), [])

    def testNegate (self):
        c = CodePointSet().negate()
        self.assertEqual(c.asTuples(), [ (0, 0x10FFFF) ])
        

if '__main__' == __name__:
    unittest.main()
            
        
