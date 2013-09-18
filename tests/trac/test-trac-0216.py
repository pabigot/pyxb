# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xst = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="int32">
      <xs:restriction base="xs:hexBinary">
          <xs:length value="4"/>
      </xs:restriction>
  </xs:simpleType>
  <xs:attribute name="Color" use="optional" type="int32"/>
  <xs:element name="elt">
    <xs:complexType>
      <xs:simpleContent>
        <xs:restriction base="int32">
          <xs:attribute ref="Color"/>
        </xs:restriction>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *
import pyxb.utils.types_

import unittest

class TestTrac0216 (unittest.TestCase):

    def testBasic (self):
        xmlt = u'<elt>30313233</elt>'
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(pyxb.utils.types_.DataType(u'0123'.encode('utf-8')), instance.value())
        xmlt = u'<elt Color="33323130">30313233</elt>'
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(pyxb.utils.types_.DataType(u'0123'.encode('utf-8')), instance.value())
        self.assertEqual(pyxb.utils.types_.DataType(u'3210'.encode('utf-8')), instance.Color)

if __name__ == '__main__':
    unittest.main()
