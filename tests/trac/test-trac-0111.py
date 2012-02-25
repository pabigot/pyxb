import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="cards">
    <xs:restriction base="xs:string">
        <xs:enumeration value="clubs"/>
        <xs:enumeration value="hearts"/>
        <xs:enumeration value="diamonds"/>
        <xs:enumeration value="spades"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="card" type="cards"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0111 (unittest.TestCase):
    Expected = set( ('clubs', 'hearts', 'diamonds', 'spades') )
    def testItems (self):
        vals = set()
        for ee in cards.items():
            self.assertTrue(isinstance(ee, cards._CF_enumeration._CollectionFacet_itemType))
            vals.add(ee.value())
        self.assertEqual(self.Expected, vals)

    def testIterItems (self):
        vals = set()
        for ee in cards.iteritems():
            self.assertTrue(isinstance(ee, cards._CF_enumeration._CollectionFacet_itemType))
            vals.add(ee.value())
        self.assertEqual(self.Expected, vals)

    def testValues (self):
        vals = set()
        for e in cards.values():
            vals.add(e)
        self.assertEqual(self.Expected, vals)

    def testIterValues (self):
        vals = set()
        for e in cards.itervalues():
            vals.add(e)
        self.assertEqual(self.Expected, vals)

if __name__ == '__main__':
    unittest.main()
    
