__author__ = 'Harold Solbrig'

# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="http://foo.org/test" targetNamespace="http://foo.org/test" elementFormDefault="qualified">
    <xs:complexType name="Outer">
        <xs:complexContent>
            <xs:extension base="Inner">
                <xs:sequence>
                    <xs:element name="c" type="xs:string" minOccurs="0" maxOccurs="1"/>
                </xs:sequence>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
    <xs:element name="Test" type="Outer"/>
    <xs:complexType name="Inner">
        <xs:sequence>
            <xs:element name="a" type="xs:string" minOccurs="0"/>
            <xs:element name="b" type="xs:string" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

#pyxb.GlobalValidationConfig._setContentInfluencesGeneration(pyxb.GlobalValidationConfig.NEVER)

class TestTrac0184(unittest.TestCase):
   def testNesting(selfs):
       xml = """<?xml version="1.0" encoding="UTF-8"?>
<Test xmlns="http://foo.org/test">
<a>A</a>
<b>B</b>
<c>C</c>
</Test>"""
       instance = CreateFromDocument(xml)
       try:
           print instance.toxml()
       except pyxb.ValidationError, e:
           print e.details()

if __name__ == '__main__':
    unittest.main()

