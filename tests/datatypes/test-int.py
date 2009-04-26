from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_int (unittest.TestCase):
    MIN_IN_RANGE = -2147483648
    MAX_IN_RANGE = 2147483647

    def testParentage (self):
        self.assertTrue(xsd.long == xsd.int.XsdSuperType())
        
    def testRange (self):
        self.assertRaises(BadTypeValueError, xsd.int, self.MIN_IN_RANGE - 1)
        self.assertEquals(self.MIN_IN_RANGE, xsd.int(self.MIN_IN_RANGE))
        self.assertEquals(0, xsd.int(0))
        self.assertEquals(self.MAX_IN_RANGE, xsd.int(self.MAX_IN_RANGE))
        self.assertRaises(BadTypeValueError, xsd.int, self.MAX_IN_RANGE+1)

    def testConversion (self):
        numbers = [ self.MIN_IN_RANGE-1, self.MIN_IN_RANGE, 0, self.MAX_IN_RANGE, self.MAX_IN_RANGE+1 ]
        for n in numbers:
            s = '%d' % (n,)
            if (self.MIN_IN_RANGE <= n) and (n <= self.MAX_IN_RANGE):
                b = xsd.int(s)
                self.assertEquals(n, b)
                self.assertEquals(s, b.xsdLiteral())
            else:
                self.assertRaises(BadTypeValueError, xsd.int, s)
        
if __name__ == '__main__':
    unittest.main()
import unittest
import pyxb.binding.datatypes as xsd

