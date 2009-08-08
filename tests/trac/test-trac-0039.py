import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node
import pyxb.binding.datatypes as xs

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="wrapper">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="holding">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="optional" minOccurs="0">
                <xs:complexType>
                  <xs:simpleContent>
                    <xs:extension base="xs:int">
                      <xs:attribute name="deep" type="xs:int"/>
                    </xs:extension>
                  </xs:simpleContent>
                </xs:complexType>
              </xs:element>
              <xs:element name="required">
                <xs:complexType>
                  <xs:simpleContent>
                    <xs:extension base="xs:string">
                      <xs:attribute name="deep" type="xs:int"/>
                    </xs:extension>
                  </xs:simpleContent>
                </xs:complexType>
              </xs:element>
            </xs:sequence>
            <xs:attribute name="inner" type="xs:int"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="outer" type="xs:int"/>
    </xs:complexType>
  </xs:element>
  <xs:element name="shallow">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="optional" minOccurs="0">
          <xs:complexType>
            <xs:simpleContent>
              <xs:extension base="xs:int">
                <xs:attribute name="deep" type="xs:int"/>
              </xs:extension>
            </xs:simpleContent>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
      <xs:attribute name="outer" type="xs:int"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.binding.basis import bind as BIND

import unittest

def SET_optional (instance, value):
    instance.optional = value

class TestTrac0039 (unittest.TestCase):
    """Creating nested anonymous elements"""
    def testShallowSet (self):
        w = shallow()
        self.assertRaises(pyxb.BadTypeValueError, SET_optional, w, 5)
        w.optional = BIND(5)
        self.assertTrue(isinstance(w.optional.value(), xs.int))
        self.assertRaises(pyxb.BadTypeValueError, SET_optional, w, BIND('string'))

    def testShallowCTOR (self):
        w = shallow(BIND(5))
        self.assertTrue(isinstance(w.optional.value(), xs.int))
        self.assertRaises(pyxb.UnexpectedNonElementContentError, shallow, 5)
        self.assertRaises(pyxb.UnexpectedNonElementContentError, shallow, BIND('string'))

if __name__ == '__main__':
    unittest.main()
    
