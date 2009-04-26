from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_short (unittest.TestCase):
    def testParentage (self):
        self.assertTrue(xsd.int == xsd.short.XsdSuperType())
        
    def testRange (self):
        self.assertRaises(BadTypeValueError, xsd.short, -32769)
        self.assertEquals(-32768, xsd.short(-32768))
        self.assertEquals(0, xsd.short(0))
        self.assertEquals(32767, xsd.short(32767))
        self.assertRaises(BadTypeValueError, xsd.short, 32768)

    def testConversion (self):
        numbers = [ -32769, -32768, 0, 32767, 32768 ]
        for n in numbers:
            s = '%d' % (n,)
            if (-32768 <= n) and (n <= 32767):
                b = xsd.short(s)
                self.assertEquals(n, b)
                self.assertEquals(s, b.xsdLiteral())
            else:
                self.assertRaises(BadTypeValueError, xsd.short, s)
        
if __name__ == '__main__':
    unittest.main()
import unittest
import pyxb.binding.datatypes as xsd

