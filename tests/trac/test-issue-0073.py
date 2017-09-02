# -*- coding: utf-8 -*-
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
  <xs:element name="di" default="32" type="xs:int"/>
  <xs:element name="fi" fixed="21" type="xs:int"/>
  <xs:element name="cfi">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:int"/>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="cdi">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:int"/>
      </xs:simpleContent>
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

class TestIssue0073 (unittest.TestCase):
    def testDefault (self):
        xmlt = six.u('<di/>');
        self.assertEqual(CreateFromDocument(xmlt), 32)
        xmlt = six.u('<di>32</di>');
        self.assertEqual(CreateFromDocument(xmlt), 32)
        xmlt = six.u('<cdi>32</cdi>');
        self.assertEqual(CreateFromDocument(xmlt).value(), 32)

    def testFixed (self):
        xmlt = six.u('<fi/>');
        self.assertEqual(CreateFromDocument(xmlt), 21)
        xmlt = six.u('<fi>21</fi>');
        self.assertEqual(CreateFromDocument(xmlt), 21)
        xmlt = six.u('<cfi>21</cfi>');
        self.assertEqual(CreateFromDocument(xmlt).value(), 21)

if __name__ == '__main__':
    unittest.main()
