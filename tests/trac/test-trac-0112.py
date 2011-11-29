import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns="urn:trac0112"
xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified"
targetNamespace="urn:trac0112" version="1.0">
     <xs:complexType name="BaseT" abstract="true"/>
     <xs:element name="Element" type="ElementType"/>
     <xs:complexType name="ElementType">
        <xs:complexContent>
            <xs:extension base="BaseT">
                <xs:sequence>
                    <xs:element name="Inner" minOccurs="0" maxOccurs="1">
                        <xs:complexType>
                            <xs:choice>
                                <xs:sequence>
                                    <xs:element maxOccurs="1" minOccurs="0" name="A1" type="xs:boolean"/>
                                    <xs:element maxOccurs="1" minOccurs="0" name="A2" type="xs:boolean"/>
                                </xs:sequence>
                                <xs:element maxOccurs="1" minOccurs="0" name="B" type="xs:boolean"/>
                                <xs:element maxOccurs="1" minOccurs="0" name="C" type="xs:boolean"/>
                            </xs:choice>
                        </xs:complexType>
                    </xs:element>
                </xs:sequence>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
</xs:schema>
'''

xmls = '''<?xml version="1.0" encoding="UTF-8"?>
<Element xmlns="urn:trac0112">
  <Inner>
    <C>true</C>
  </Inner>
</Element>'''


code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0112 (unittest.TestCase):
    def testExample (self):
        print "NOTE: THIS TEST ACTUALLY FAILS (we're validating that it does fail)"
        self.assertRaises(pyxb.BindingValidationError, CreateFromDocument, xmls)


if __name__ == '__main__':
    unittest.main()
    
