from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd
import binascii

class Test_hexBinary (unittest.TestCase):
    def testValues (self):
        data_values = [ '\x01', '\x00', '\x01\x23', '\x12\x34' ]
        for dv in data_values:
            v = xsd.hexBinary(dv)
            self.assertEqual(v, dv)

    def testStrings (self):
        encoded_values = [ u'01', u'00', u'ab', u'Ab', u'AB12' ]
        for ev in encoded_values:
            v = xsd.hexBinary.Factory(ev)
            self.assertEqual(v, ev)
            v = xsd.hexBinary.Factory(ev, _from_xml=True)
            self.assertEqual(len(ev)/2, len(v))
            self.assertEqual(ev.upper(), v.xsdLiteral())
        
    def testBadStrings (self):
        self.assertRaises(BadTypeValueError, xsd.hexBinary.Factory, u'0', _from_xml=True)
        self.assertRaises(BadTypeValueError, xsd.hexBinary.Factory, u'012', _from_xml=True)
        self.assertRaises(BadTypeValueError, xsd.hexBinary.Factory, u'01s', _from_xml=True)
        self.assertRaises(BadTypeValueError, xsd.hexBinary.Factory, u'sb', _from_xml=True)

    def testLiteralization (self):
        self.assertEqual('', xsd.hexBinary('').xsdLiteral())


if __name__ == '__main__':
    unittest.main()
