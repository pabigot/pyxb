import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
from pyxb.namespace.builtin import XMLSchema_instance as XSI

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:complexType name="BaseT" abstract="true"/>
<xs:complexType name="String">
  <xs:complexContent>
    <xs:extension base="BaseT">
      <xs:sequence>
        <xs:element name="child" type="xs:string"/>
      </xs:sequence>
    </xs:extension>
  </xs:complexContent>
</xs:complexType>
<xs:complexType name="Integer">
  <xs:complexContent>
    <xs:extension base="BaseT">
      <xs:sequence>
        <xs:element name="child" type="xs:integer"/>
      </xs:sequence>
    </xs:extension>
  </xs:complexContent>
</xs:complexType>
<xs:element name="base" type="BaseT"/>
<xs:element name="string" type="String"/>
<xs:element name="integer" type="Integer"/>
<xs:element name="wildcard">
  <xs:complexType>
    <xs:sequence>
      <xs:any/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
</xs:schema>'''

file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0060 (unittest.TestCase):
    def tearDown (self):
        pass

    NotAnInteger = 'not an integer'
    AnInteger = 34
    CorrectString = '<string><child>hi</child></string>'
    CorrectInteger = '<integer><child>%d</child></integer>' % (AnInteger,)
    BadInteger = '<integer><child>%s</child></integer>' % (NotAnInteger,)
    ConflictString = '<integer xsi:type="String" xmlns:xsi="%s"><child>%s</child></integer>' % (XSI.uri(), NotAnInteger)
    UntypedIntegerElement = '<element><child>%d</child></element>' % (AnInteger,)
    TypedElement = '<element xsi:type="Integer" xmlns:xsi="%s"><child>%d</child></element>' % (XSI.uri(), AnInteger)

    def testWildcardString (self):
        xmls = '<wildcard>%s</wildcard>' % (self.CorrectString,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual('hi', instance.child)

    def testWildcardInteger (self):
        xmls = '<wildcard>%s</wildcard>' % (self.CorrectInteger,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))
        self.assertTrue(isinstance(instance.child, long))
        self.assertEqual(self.AnInteger, instance.child)

    def testWildcardIntegerBad (self):
        xmls = '<wildcard>%s</wildcard>' % (self.BadInteger,)
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, xmls)

    def testWildcardUntyped (self):
        xmls = '<wildcard>%s</wildcard>' % (self.UntypedIntegerElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertFalse(isinstance(instance, pyxb.binding.basis._TypeBinding_mixin))

    def testWildcardTyped (self):
        xmls = '<wildcard>%s</wildcard>' % (self.TypedElement,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, Integer))

    def testStrict (self):
        xmls = '<wildcard>%s</wildcard>' % (self.ConflictString,)
        wc = CreateFromDocument(xmls)
        instance = wc.wildcardElements()[0]
        self.assertTrue(isinstance(instance, String))
        self.assertEqual(self.NotAnInteger, instance.child)


if __name__ == '__main__':
    unittest.main()
