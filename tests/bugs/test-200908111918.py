# Test generated documentation of attributes, elements, and classes
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:simpleType name="tEnumerations">
  <xs:annotation><xs:documentation>Documentation for type tEnumerations</xs:documentation></xs:annotation>
  <xs:restriction base="xs:string">
    <xs:enumeration value="one">
      <xs:annotation><xs:documentation>Documentation for tEnumerations.one</xs:documentation></xs:annotation>
    </xs:enumeration>
    <xs:enumeration value="two">
      <xs:annotation><xs:documentation>Documentation for tEnumerations.two</xs:documentation></xs:annotation>
    </xs:enumeration>
  </xs:restriction>
</xs:simpleType>
<xs:complexType name="tComplex">
  <xs:annotation><xs:documentation>Documentation for tComplex</xs:documentation></xs:annotation>
  <xs:complexContent>
    <xs:extension base="xs:anyType">
      <xs:sequence>
        <xs:element name="elt" type="xs:string">
          <xs:annotation><xs:documentation>Documentation for element C{elt} in C{tComplex}</xs:documentation></xs:annotation>
        </xs:element>
        <xs:element ref="element" minOccurs="0" >
          <xs:annotation><xs:documentation>How does documentation for a referenced element come out?</xs:documentation></xs:annotation>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="attr" type="xs:string">
        <xs:annotation><xs:documentation>Documentation for attribute C{attr} in C{tComplex}</xs:documentation></xs:annotation>
      </xs:attribute>
    </xs:extension>
  </xs:complexContent>
</xs:complexType>
<xs:element name="element" type="tComplex">
  <xs:annotation><xs:documentation>Documentation for element C{element}
Multi-line.
With " and ' characters even.
</xs:documentation></xs:annotation>
</xs:element>
</xs:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200908111918 (unittest.TestCase):
    def testComponent (self):
        self.assertEqual(element._description(), '''element (tComplex)
Documentation for element C{element}
Multi-line.
With " and ' characters even.
''')

        self.assertEqual(tComplex._description(), '''tComplex, element-only content
Attributes:
  attr: attr ({http://www.w3.org/2001/XMLSchema}string), optional
  Wildcard attribute(s)
Elements:
  elt: elt ({http://www.w3.org/2001/XMLSchema}string), local to tComplex
  element: element (tComplex), local to tComplex
  Wildcard element(s)''')
        self.assertEqual(tEnumerations._description(), '''tEnumerations restriction of {http://www.w3.org/2001/XMLSchema}string
Documentation for type tEnumerations''')

        # NOTE It is arguably a bug that the local annotation for the
        # reference element has been lost.  When somebody else
        # discovers this and complains, we'll think about fixing it.

        self.assertEqual(tComplex.element.__doc__, '''Documentation for element C{element}
Multi-line.
With " and ' characters even.
''')


if __name__ == '__main__':
    unittest.main()
