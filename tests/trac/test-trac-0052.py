import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
<xs:element name="testElt">
  <xs:complexType>
  <xs:sequence>
    <xs:any minOccurs="0" maxOccurs="unbounded"/>
  </xs:sequence>
  </xs:complexType>
</xs:element>
</xs:schema>'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import xml.dom

class TestTrac_0052 (unittest.TestCase):
    def testInternalDOM (self):
        xmls = '<testElt><wc1/><wc2 wca="3"/></testElt>'
        instance = CreateFromDocument(xmls);
        self.assertEqual(2, len(instance.wildcardElements()))
        wc2 = instance.wildcardElements()[1]
        self.assertTrue(isinstance(wc2, xml.dom.Node))
        self.assertEqual(xml.dom.Node.ELEMENT_NODE, wc2.nodeType)
        self.assertEqual('3', wc2.attributes.get(pyxb.namespace.ExpandedName('wca').uriTuple()))
        

if __name__ == '__main__':
    unittest.main()
