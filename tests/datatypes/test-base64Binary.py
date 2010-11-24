import unittest
import binascii
import pyxb
import pyxb.binding.datatypes as xsd

class Test_base64Binary (unittest.TestCase):
    RFC4648_S9 = ( ('14fb9c03d97e', 'FPucA9l+'),
                   ('14fb9c03d9', 'FPucA9k='),
                   ('14fb9c03', 'FPucAw==') )
    RFC4648_S10 = ( ('', ''),
                    ('f', 'Zg=='),
                    ('fo', 'Zm8='),
                    ('foo', 'Zm9v'),
                    ('foob', 'Zm9vYg=='),
                    ('fooba', 'Zm9vYmE='),
                    ('foobar', 'Zm9vYmFy') )
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
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'Z', _from_xml=True)
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'Zg', _from_xml=True)
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'Zg=', _from_xml=True)
        self.assertEqual('f', xsd.base64Binary('Zg==', _from_xml=True))
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'ZZZ=', _from_xml=True)
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'ZZ==', _from_xml=True)
        self.assertRaises(pyxb.BadTypeValueError, xsd.base64Binary, 'ZE==', _from_xml=True)

if __name__ == '__main__':
    unittest.main()
