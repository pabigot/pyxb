# Undeclared XML namespace
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path

xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:attributeGroup name="required">
    <xs:attribute name="rattr" use="required" type="xs:int"/>
    <xs:attribute name="rattr_fixed" type="xs:int" fixed="30" use="required"/>
  </xs:attributeGroup>
  <xs:attributeGroup name="optional">
    <xs:attribute name="attr" type="xs:int"/>
    <xs:attribute name="attr_def" type="xs:int" default="10"/>
    <xs:attribute name="attr_fixed" type="xs:int" fixed="20"/>
  </xs:attributeGroup>
  <xs:complexType name="opt_struct">
    <xs:attributeGroup ref="optional"/>
  </xs:complexType>
  <xs:complexType name="req_struct">
    <xs:attributeGroup ref="required"/>
  </xs:complexType>
  <xs:element name="ireq_struct" type="req_struct"/>
  <xs:element name="iopt_struct" type="opt_struct"/>
  <xs:complexType name="opt_def">
    <xs:complexContent>
      <xs:restriction base="opt_struct">
        <xs:attribute name="attr" type="xs:int" default="5"/>
      </xs:restriction>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="iopt_def" type="opt_def"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0027 (unittest.TestCase):
    def testRequired (self):
        self.assertEqual(2, len(req_struct._AttributeMap))
        i = ireq_struct()
        self.assertRaises(pyxb.MissingAttributeError, i.validateBinding)
        self.assertTrue(i.rattr() is None)
        i.setRattr(-4)
        self.assertEqual(-4, i.rattr())
        self.assertTrue(i._AttributeMap['rattr'].provided(i))

        self.assertRaises(pyxb.MissingAttributeError, i.validateBinding) # Should fail because rattr_fixed was not explicitly set

        self.assertFalse(i._AttributeMap['rattr_fixed'].provided(i))
        self.assertEqual(30, i.rattr_fixed())

        self.assertRaises(pyxb.AttributeChangeError, i.setRattr_fixed, 41)
        self.assertFalse(i._AttributeMap['rattr_fixed'].provided(i))

        i.setRattr_fixed(30)
        self.assertTrue(i._AttributeMap['rattr_fixed'].provided(i))
        self.assertEqual(30, i.rattr_fixed())
        self.assertTrue(i.validateBinding())

        self.assertRaises(pyxb.AttributeChangeError, i.setRattr_fixed, 41)

    def testRequiredCTor (self):
        i = ireq_struct(rattr=11, rattr_fixed=30)
        self.assertTrue(i.validateBinding())

        self.assertRaises(pyxb.AttributeChangeError, ireq_struct, rattr=11, rattr_fixed=31)

    def testOptional (self):
        self.assertEqual(3, len(opt_struct._AttributeMap))
        i = iopt_struct()

        self.assertFalse(i._AttributeMap['attr_def'].provided(i))
        self.assertEqual(10, i.attr_def())
        i.setAttr_def(11)
        self.assertEqual(11, i.attr_def())
        self.assertTrue(i._AttributeMap['attr_def'].provided(i))

        self.assertFalse(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed())

        self.assertRaises(pyxb.AttributeChangeError, i.setAttr_fixed, 21)
        self.assertFalse(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed())

        i.setAttr_fixed(20)
        self.assertTrue(i._AttributeMap['attr_fixed'].provided(i))
        self.assertEqual(20, i.attr_fixed())

    def testOptDef (self):
        self.assertEqual(1, len(opt_def._AttributeMap))
        i = opt_def()
        

if __name__ == '__main__':
    unittest.main()
    
