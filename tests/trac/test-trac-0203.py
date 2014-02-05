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
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.UnboundElementError, unbound.toxml, 'utf-8', root_only=True)
        else:
            with self.assertRaises(pyxb.UnboundElementError) as cm:
                unbound.toxml('utf-8', root_only=True)
            e = cm.exception
            self.assertEqual(e.instance, unbound)
            self.assertEqual('Instance of type XsdWithHyphens has no bound element for start tag', str(e))

    def testOverride (self):
        unbound = XsdWithHyphens('name')
        xmls = unbound.toxml('utf-8', root_only=True, element_name='root')
        self.assertEqual(u'<root><username>name</username></root>', xmls)

if __name__ == '__main__':
    unittest.main()
