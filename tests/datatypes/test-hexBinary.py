from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_hexBinary (unittest.TestCase):
    def testValues (self):
        v = xsd.hexBinary(1)
        self.assertEqual(1, v)
        self.assertEqual(1, v.length())

        v = xsd.hexBinary(0)
        self.assertEqual(0, v)
        self.assertEqual(1, v.length())

        v = xsd.hexBinary(0x123)
        self.assertEqual(0x123, v)
        self.assertEqual(2, v.length())

        v = xsd.hexBinary(0x1234)
        self.assertEqual(0x1234, v)
        self.assertEqual(2, v.length())

        v = xsd.hexBinary(0x12345)
        self.assertEqual(0x12345, v)
        self.assertEqual(3, v.length())

        v = xsd.hexBinary(0x1234567890)
        self.assertEqual(0x1234567890, v)
        self.assertEqual(5, v.length())

        v = xsd.hexBinary(0x123456789abcdef0)
        self.assertEqual(0x123456789abcdef0, v)
        self.assertEqual(8, v.length())

        v = xsd.hexBinary(0x1234567890123456789012345678901234567890)
        self.assertEqual(0x1234567890123456789012345678901234567890, v)
        self.assertEqual(20, v.length())

    def testStrings (self):
        v = xsd.hexBinary("01")
        self.assertEqual(1, v)
        self.assertEqual(1, v.length())

        v = xsd.hexBinary("00")
        self.assertEqual(0, v)
        self.assertEqual(1, v.length())

        v = xsd.hexBinary("0123")
        self.assertEqual(0x123, v)
        self.assertEqual(2, v.length())

        v = xsd.hexBinary("1234")
        self.assertEqual(0x1234, v)
        self.assertEqual(2, v.length())

        v = xsd.hexBinary('012345')
        self.assertEqual(0x12345, v)
        self.assertEqual(3, v.length())

        v = xsd.hexBinary('1234567890')
        self.assertEqual(0x1234567890, v)
        self.assertEqual(5, v.length())

        v = xsd.hexBinary('123456789abcdef0')
        self.assertEqual(0x123456789abcdef0, v)
        self.assertEqual(8, v.length())

        v = xsd.hexBinary('123456789ABCDEF0')
        self.assertEqual(0x123456789abcdef0, v)
        self.assertEqual(8, v.length())

        v = xsd.hexBinary('1234567890123456789012345678901234567890')
        self.assertEqual(0x1234567890123456789012345678901234567890, v)
        self.assertEqual(20, v.length())
        
    def testBadStrings (self):
        self.assertRaises(BadTypeValueError, xsd.hexBinary, '')
        self.assertRaises(BadTypeValueError, xsd.hexBinary, '0')
        self.assertRaises(BadTypeValueError, xsd.hexBinary, '012')
        self.assertRaises(BadTypeValueError, xsd.hexBinary, '01s')


    def testLiteralization (self):
        self.assertEqual('00', xsd.hexBinary(0).xsdLiteral())
        self.assertEqual('01', xsd.hexBinary(1).xsdLiteral())
        self.assertEqual('12', xsd.hexBinary(0x12).xsdLiteral())
        self.assertEqual('0123', xsd.hexBinary(0x123).xsdLiteral())
        self.assertEqual('1234', xsd.hexBinary(0x1234).xsdLiteral())
        self.assertEqual('1234567890', xsd.hexBinary(0x1234567890).xsdLiteral())
        self.assertEqual('1234567890123456789012345678901234567890', xsd.hexBinary(0x1234567890123456789012345678901234567890).xsdLiteral())
    


if __name__ == '__main__':
    unittest.main()
