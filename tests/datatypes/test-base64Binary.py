# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import binascii
import pyxb
import pyxb.binding.datatypes as xsd

class Test_base64Binary (unittest.TestCase):
    RFC4648_S9 = ( (u'14fb9c03d97e', u'FPucA9l+'),
                   (u'14fb9c03d9', u'FPucA9k='),
                   (u'14fb9c03', u'FPucAw==') )
    RFC4648_S10 = ( (u'', u''),
                    (u'f', u'Zg=='),
                    (u'fo', u'Zm8='),
                    (u'foo', u'Zm9v'),
                    (u'foob', u'Zm9vYg=='),
                    (u'fooba', u'Zm9vYmE='),
                    (u'foobar', u'Zm9vYmFy') )
    def testVectors (self):
        """RFC4648 section 10."""
        for (plaintext, ciphertext) in self.RFC4648_S10:
            self.assertEqual(xsd.base64Binary(plaintext).xsdLiteral(), ciphertext)
            self.assertEqual(xsd.base64Binary(ciphertext, _from_xml=True), plaintext)
        for (hextext, ciphertext) in self.RFC4648_S9:
            plaintext = binascii.unhexlify(hextext)
            self.assertEqual(xsd.base64Binary(plaintext).xsdLiteral(), ciphertext)
            self.assertEqual(xsd.base64Binary(ciphertext, _from_xml=True), plaintext)

    def testInvalid (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'Z', _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'Zg', _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'Zg=', _from_xml=True)
        self.assertEqual(u'f', xsd.base64Binary(u'Zg==', _from_xml=True))
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'ZZZ=', _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'ZZ==', _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, u'ZE==', _from_xml=True)

if __name__ == '__main__':
    unittest.main()
