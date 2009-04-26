from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class _TestIntegerType (object):
    """Base class for testing any datatype that descends from integer.

    Subclasses should define class variables:
    THIS_TYPE = the xsd datatype class
    PARENT_TYPE = the next dominating type in the hierarchy
    MIN_IN_RANGE = the minimum expressible value
    MAX_IN_RANGE = the maximum expressible value
    """
    def testParentage (self):
        self.assertTrue(self.PARENT_TYPE == self.THIS_TYPE.XsdSuperType())
        
    def testRange (self):
        self.assertRaises(BadTypeValueError, self.THIS_TYPE, self.MIN_IN_RANGE - 1)
        self.assertEquals(self.MIN_IN_RANGE, self.THIS_TYPE(self.MIN_IN_RANGE))
        self.assertEquals(0, self.THIS_TYPE(0))
        self.assertEquals(self.MAX_IN_RANGE, self.THIS_TYPE(self.MAX_IN_RANGE))
        self.assertRaises(BadTypeValueError, self.THIS_TYPE, self.MAX_IN_RANGE+1)

    PARENT_EXCLUDE = []

    def testStringConversion (self):
        numbers = [ self.MIN_IN_RANGE-1, self.MIN_IN_RANGE, 0, self.MAX_IN_RANGE, self.MAX_IN_RANGE+1 ]
        for n in numbers:
            s = '%d' % (n,)
            p = None
            if not (n in self.PARENT_EXCLUDE):
                p = self.PARENT_TYPE(n)
                self.assertEquals(n, p)
            if (self.MIN_IN_RANGE <= n) and (n <= self.MAX_IN_RANGE):
                bs = self.THIS_TYPE(s)
                self.assertEquals(n, bs)
                self.assertEquals(s, bs.xsdLiteral())
                bp = self.THIS_TYPE(p)
                self.assertEquals(n, bp)
            else:
                self.assertRaises(BadTypeValueError, self.THIS_TYPE, s)
                self.assertRaises(BadTypeValueError, self.THIS_TYPE, p)

class Test_int (unittest.TestCase, _TestIntegerType):
    THIS_TYPE = xsd.int
    PARENT_TYPE = xsd.long
    MIN_IN_RANGE = -2147483648
    MAX_IN_RANGE = 2147483647

if __name__ == '__main__':
    unittest.main()
