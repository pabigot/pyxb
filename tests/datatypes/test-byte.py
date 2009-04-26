from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_byte (unittest.TestCase):
    def testParentage (self):
        self.assertTrue(xsd.short == xsd.byte.XsdSuperType())
        
    def testRange (self):
        self.assertRaises(BadTypeValueError, xsd.byte, -129)
        self.assertEquals(-128, xsd.byte(-128))
        self.assertEquals(0, xsd.byte(0))
        self.assertEquals(127, xsd.byte(127))
        self.assertRaises(BadTypeValueError, xsd.byte, 128)

    def testConversion (self):
        numbers = [ -129, -128, 0, 127, 128 ]
        for n in numbers:
            s = '%d' % (n,)
            if (-128 <= n) and (n <= 127):
                b = xsd.byte(s)
                self.assertEquals(n, b)
                self.assertEquals(s, b.xsdLiteral())
            else:
                self.assertRaises(BadTypeValueError, xsd.byte, s)
        
if __name__ == '__main__':
    unittest.main()
