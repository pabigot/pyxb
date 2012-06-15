# Coding declaration for unicode strings
# -*- coding: utf-8 -*-
# See also:
# http://www.evanjones.ca/python-utf8.html
# http://bytes.com/topic/python/answers/41153-xml-unicode-what-am-i-doing-wrong

import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import xml.sax
import StringIO

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">
    <xs:element name="foo" type="xs:string"/>
    <xs:element name="bar">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="e" type="xs:string" minOccurs="0"/>
            </xs:sequence>
            <xs:attribute name="a" type="xs:string"/>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0131 (unittest.TestCase):
    # Unicode string, UTF-8 encoding (per declaration at script top)
    textu = u'Sign of Leser-Tr\xc3\xa9lat'
    # Which is not the same as this; see below
    #textu = unicode('Sign of Leser-Tr\xc3\xa9lat', 'utf-8')
    texts = textu.encode('utf-8')
    base_xmlu = '<bar><e>' + textu + '</e></bar>'
    declared_xmlu = '<?xml version="1.0" encoding="UTF-8"?>' + base_xmlu

    ExpectedUnicodeErrors = ( UnicodeEncodeError, xml.sax.SAXParseException )

    def setUp (self):
        self.__xmlStyle = pyxb._XMLStyle

    def tearDown (self):
        pyxb._SetXMLStyle(self.__xmlStyle)

    def testRepresentation (self):
        self.assertEqual(self.texts, 'Sign of Leser-Tr\xc3\x83\xc2\xa9lat')

    def testBasicParse (self):
        xmlu = self.base_xmlu
        xmls = xmlu.encode('utf-8')
        self.assertTrue(isinstance(xmlu, unicode))
        self.assertTrue(isinstance(xmls, str))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        self.assertRaises(self.ExpectedUnicodeErrors, CreateFromDocument, xmlu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        if sys.version_info[:2] == (2, 7):
            self.assertRaises(self.ExpectedUnicodeErrors, CreateFromDocument, xmlu)
        else:
            instance = CreateFromDocument(xmlu)
            self.assertEqual(instance.e, self.textu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlu)
        self.assertEqual(instance.e, self.textu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        
    def testDeclaredParse (self):
        xmlu = self.declared_xmlu
        xmls = xmlu.encode('utf-8')
        self.assertTrue(isinstance(xmlu, unicode))
        self.assertTrue(isinstance(xmls, str))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        self.assertRaises(self.ExpectedUnicodeErrors, CreateFromDocument, xmlu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        self.assertRaises(self.ExpectedUnicodeErrors, CreateFromDocument, xmlu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlu)
        self.assertEqual(instance.e, self.textu)
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.e, self.textu)
        
    def testElementEncode (self):
        instance = bar()
        instance.e = self.textu
        self.assertEqual(instance.e, self.textu)

    def testAttributeEncode (self):
        instance = bar()
        instance.a = self.textu
        self.assertEqual(instance.a, self.textu)
        
    def testuEncode (self):
        instance = foo(self.textu)
        self.assertEqual(instance, self.textu)

if __name__ == '__main__':
    unittest.main()
