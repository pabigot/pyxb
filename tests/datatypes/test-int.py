from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_int (unittest.TestCase):
    THIS_TYPE = xsd.int
    PARENT_TYPE = xsd.long
    MIN_IN_RANGE = -2147483648
    MAX_IN_RANGE = 2147483647

    def testParentage (self):
        self.assertTrue(self.PARENT_TYPE == self.THIS_TYPE.XsdSuperType())
        
    def testRange (self):
        self.assertRaises(BadTypeValueError, self.THIS_TYPE, self.MIN_IN_RANGE - 1)
        self.assertEquals(self.MIN_IN_RANGE, self.THIS_TYPE(self.MIN_IN_RANGE))
        self.assertEquals(0, self.THIS_TYPE(0))
        self.assertEquals(self.MAX_IN_RANGE, self.THIS_TYPE(self.MAX_IN_RANGE))
        self.assertRaises(BadTypeValueError, self.THIS_TYPE, self.MAX_IN_RANGE+1)

    def testConversion (self):
        numbers = [ self.MIN_IN_RANGE-1, self.MIN_IN_RANGE, 0, self.MAX_IN_RANGE, self.MAX_IN_RANGE+1 ]
        for n in numbers:
            s = '%d' % (n,)
            if (self.MIN_IN_RANGE <= n) and (n <= self.MAX_IN_RANGE):
                b = self.THIS_TYPE(s)
                self.assertEquals(n, b)
                self.assertEquals(s, b.xsdLiteral())
            else:
                self.assertRaises(BadTypeValueError, self.THIS_TYPE, s)
        
if __name__ == '__main__':
    unittest.main()
import unittest
import pyxb.binding.datatypes as xsd

