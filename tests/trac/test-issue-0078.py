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
  <xs:simpleType name="tla">
    <xs:restriction base="xs:string">
      <xs:length value="3"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="tla" type="tla"/>
  <xs:simpleType name="lctla">
    <xs:restriction base="tla">
      <xs:length value="3"/>
      <xs:pattern value="\p{Ll}*"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="lctla" type="lctla"/>
  <xs:complexType name="env">
    <xs:sequence>
      <xs:element name="tla" type="tla" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="env" type="env"/>
  <xs:complexType name="lcenv">
    <xs:complexContent>
      <xs:restriction base="env">
        <xs:sequence>
          <xs:element name="tla" type="lctla" minOccurs="0"/>
        </xs:sequence>
      </xs:restriction>
    </xs:complexContent>
  </xs:complexType>
  <xs:element name="lcenv" type="lcenv"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import sys

class TestIssue0078 (unittest.TestCase):
    def testInheritance (self):
        self.assertTrue(issubclass(lctla_, tla_))
        self.assertTrue(issubclass(lcenv_, env_))

    def testSimpleTypes (self):
        self.assertEqual('FOO', tla('FOO'))
        self.assertEqual('foo', lctla('foo'))
        self.assertRaises(SimpleFacetValueError, lctla, 'FOO');

    def testBase (self):
        instance = env();
        instance.tla = 'FOO';
        xmlt = '<env><tla>FOO</tla></env>';
        xmld = xmlt.encode('utf-8');
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld);

    def testRestr (self):
        instance = lcenv();
        instance.tla = 'foo';
        xmlt = '<lcenv><tla>foo</tla></lcenv>';
        xmld = xmlt.encode('utf-8');
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)

    def testRestrValidation (self):
        instance = lcenv();
        with self.assertRaises(SimpleFacetValueError) as cm:
            instance.tla = 'FOO';
        self.assertTrue(isinstance(cm.exception, SimpleFacetValueError))

if __name__ == '__main__':
    unittest.main()
