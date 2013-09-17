# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xst = u'''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
 <xs:complexType name="XsdWithHyphens">
    <xs:sequence>
        <xs:element name="username" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="xsd-with-hyphens" type="XsdWithHyphens"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0203 (unittest.TestCase):
    def testBasic (self):
        unbound = XsdWithHyphens('name')
        with self.assertRaises(pyxb.UnboundElementError) as cm:
            unbound.toxml('utf-8', root_only=True)
        e = cm.exception
        self.assertEqual(e.instance, unbound)
        self.assertEqual('Instance of type XsdWithHyphens has no bound element for start tag', str(e))

if __name__ == '__main__':
    unittest.main()
