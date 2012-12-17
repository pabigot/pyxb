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
  <xs:element name="uncs" type="xs:string"/>
  <xs:element name="complex">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="uncs" default="value"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

import unittest

class TestTrac0099a (unittest.TestCase):
    def testProcessing (self):
        self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_text=xsd)

if __name__ == '__main__':
    unittest.main()
    
