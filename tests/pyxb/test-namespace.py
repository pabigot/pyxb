import unittest
import pyxb
from pyxb.namespace import ExpandedName

class TestExpandedName (unittest.TestCase):
    
    def testEquivalence (self):
        en1 = ExpandedName(pyxb.namespace.XMLSchema, 'string')
        en2 = ExpandedName(pyxb.namespace.XMLSchema, 'string')
        self.assertEqual(en1, en2)
        mymap = { }
        mymap[en1] = 'Yes'
        self.assertEqual(mymap[en2], 'Yes')

if '__main__' == __name__:
    unittest.main()
    
