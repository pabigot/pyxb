# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="Present">
    <xs:sequence>
      <xs:element name="pContent" minOccurs="1" maxOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="Optional">
    <xs:sequence>
      <xs:element name="oContent" minOccurs="0" maxOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="Absent">
    <xs:sequence>
      <xs:element name="aContent" minOccurs="0" maxOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="sel">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded">
        <xs:element name="present" type="Present"/>
        <xs:element name="optional" type="Optional"/>
        <xs:element name="absent" type="Absent"/>
      </xs:choice>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import sys

class TestIssue0079 (unittest.TestCase):
    def testPresent (self):
        xmlt = '<sel><present><pContent/></present></sel>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmlt);
        self.assertEqual(xmld, doc.toxml('utf-8', root_only=True))

    def testOptional (self):
        xmlt = '<sel><optional><oContent/></optional></sel>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmlt);
        self.assertEqual(xmld, doc.toxml('utf-8', root_only=True))
        xmlt = '<sel><optional/></sel>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmlt);
        self.assertEqual(xmld, doc.toxml('utf-8', root_only=True))

    def testAbsent (self):
        xmlt = '<sel><absent/></sel>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmlt);
        self.assertEqual(xmld, doc.toxml('utf-8', root_only=True))
        xmlt = '<sel><absent><aContent/></absent></sel>';
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            doc = CreateFromDocument(xmlt);

if __name__ == '__main__':
    unittest.main()
