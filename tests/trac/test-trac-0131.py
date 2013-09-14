# Coding declaration for unicode strings
# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
# See also:
# http://www.evanjones.ca/python-utf8.html
# http://bytes.com/topic/python/answers/41153-xml-unicode-what-am-i-doing-wrong

import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import xml.sax
import io

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
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0131 (unittest.TestCase):
    # Unicode string, UTF-8 encoding (per declaration at script top)
    stru = u'Sign of Leser-Tr\xc3\xa9lat'
    # Which is not the same as this; see below
    #stru = unicode('Sign of Leser-Tr\xc3\xa9lat', 'utf-8')
    strd = stru.encode('utf-8')
    base_xmlt = '<bar><e>' + stru + '</e></bar>'
    declared_xmlt = '<?xml version="1.0" encoding="UTF-8"?>' + base_xmlt

    ExpectedUnicodeErrors = ( UnicodeEncodeError, xml.sax.SAXParseException )

    def setUp (self):
        self.__xmlStyle = pyxb._XMLStyle

    def tearDown (self):
        pyxb._SetXMLStyle(self.__xmlStyle)

    def testRepresentation (self):
        self.assertEqual(self.strd, 'Sign of Leser-Tr\xc3\x83\xc2\xa9lat')

    def testBasicParse (self):
        xmlt = self.base_xmlt
        xmld = xmlt.encode('utf-8')
        self.assertTrue(isinstance(xmlt, unicode))
        self.assertTrue(isinstance(xmld, str))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)

    def testDeclaredParse (self):
        xmlt = self.declared_xmlt
        xmld = xmlt.encode('utf-8')
        self.assertTrue(isinstance(xmlt, unicode))
        self.assertTrue(isinstance(xmld, str))
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxer)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)
        pyxb._SetXMLStyle(pyxb.XMLStyle_minidom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)
        # saxdom can handle Unicode representation
        pyxb._SetXMLStyle(pyxb.XMLStyle_saxdom)
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.e, self.stru)
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.e, self.stru)

    def testElementEncode (self):
        instance = bar()
        instance.e = self.stru
        self.assertEqual(instance.e, self.stru)

    def testAttributeEncode (self):
        instance = bar()
        instance.a = self.stru
        self.assertEqual(instance.a, self.stru)

    def testuEncode (self):
        instance = foo(self.stru)
        self.assertEqual(instance, self.stru)

if __name__ == '__main__':
    unittest.main()
