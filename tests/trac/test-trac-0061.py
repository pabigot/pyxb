import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:simpleType name="tla">
  <xs:annotation><xs:documentation>Simple type to represent a three-letter acronym</xs:documentation></xs:annotation>
  <xs:restriction base="xs:string">
    <xs:length value="3"/>
  </xs:restriction>
</xs:simpleType>
<xs:simpleType name="Atla">
  <xs:annotation><xs:documentation>A three-letter acronym that starts with A</xs:documentation></xs:annotation>
  <xs:restriction base="tla">
    <xs:pattern value="A.."/>
  </xs:restriction>
</xs:simpleType>
<xs:simpleType name="tlaZ">
  <xs:annotation><xs:documentation>A three-letter acronym that ends with Z</xs:documentation></xs:annotation>
  <xs:restriction base="tla">
    <xs:pattern value="..Z"/>
  </xs:restriction>
</xs:simpleType>
<xs:simpleType name="combAtlaZ">
  <xs:annotation><xs:documentation>A three-letter acronym that either starts with A or ends with Z</xs:documentation></xs:annotation>
  <xs:restriction base="tla">
    <xs:pattern value="A.."/>
    <xs:pattern value="..Z"/>
  </xs:restriction>
</xs:simpleType>
<xs:simpleType name="dervAtlaZ">
  <xs:annotation><xs:documentation>A three-letter acronym that starts with A and ends with Z</xs:documentation></xs:annotation>
  <xs:restriction base="Atla">
    <xs:pattern value="..Z"/>
  </xs:restriction>
</xs:simpleType>

</xs:schema>'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0061 (unittest.TestCase):
    def testDocString (self):
        self.assertEquals("Simple type to represent a three-letter acronym", tla._Documentation.strip())
        self.assertEquals("Simple type to represent a three-letter acronym", tla.__doc__.strip())

    def testTLA (self):
        self.assertEquals("tla", tla('tla'))
        self.assertRaises(pyxb.BadTypeValueError, tla, 'four')
        self.assertRaises(pyxb.BadTypeValueError, tla, '1')

    def testAtla (self):
        self.assertRaises(pyxb.BadTypeValueError, Atla, 'four')
        self.assertRaises(pyxb.BadTypeValueError, Atla, '1')
        self.assertEquals("A23", Atla('A23'))
        self.assertEquals("A2Z", Atla('A2Z'))
        self.assertRaises(pyxb.BadTypeValueError, Atla, 'B12')

    def testtlaZ (self):
        self.assertRaises(pyxb.BadTypeValueError, tlaZ, 'four')
        self.assertRaises(pyxb.BadTypeValueError, tlaZ, '1')
        self.assertEquals("12Z", tlaZ('12Z'))
        self.assertEquals("A2Z", tlaZ('A2Z'))
        self.assertRaises(pyxb.BadTypeValueError, tlaZ, '12X')

    def testcombAtlaZ (self):
        self.assertRaises(pyxb.BadTypeValueError, combAtlaZ, 'four')
        self.assertRaises(pyxb.BadTypeValueError, combAtlaZ, '1')
        self.assertEquals("A2Z", combAtlaZ('A2Z'))
        self.assertEquals("A23", combAtlaZ('A23'))
        self.assertEquals("12Z", combAtlaZ('12Z'))
        self.assertRaises(pyxb.BadTypeValueError, combAtlaZ, '12X')
        self.assertRaises(pyxb.BadTypeValueError, combAtlaZ, 'X23')

    def testdervAtlaZ (self):
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, 'four')
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, '1')
        self.assertEquals("A2Z", dervAtlaZ('A2Z'))
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, 'A23')
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, '12Z')
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, '12X')
        self.assertRaises(pyxb.BadTypeValueError, dervAtlaZ, 'X23')

if __name__ == '__main__':
    unittest.main()
