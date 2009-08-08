# Undeclared XML namespace

import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.datatypes as xs
from xml.dom import Node

import os.path
# <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xml="http://www.w3.org/XML/1998/namespace">

xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="tEnum">
    <xs:restriction base="xs:string">
      <xs:enumeration value="one"/>
      <xs:enumeration value="two"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="tUnion">
    <xs:union memberTypes="xs:int tEnum"/>
  </xs:simpleType>
  <xs:element name="union" type="tUnion"/>
  <xs:simpleType name="tListUnion">
    <xs:list itemType="tUnion"/>
  </xs:simpleType>
  <xs:element name="listUnion" type="tListUnion"/>
  <xs:complexType name="tStructure">
    <xs:sequence/>
    <xs:attribute name="attr" type="tUnion" use="required"/>
  </xs:complexType>
  <xs:element name="structure" type="tStructure"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0037 (unittest.TestCase):
    def testElement (self):
        i = union(4)
        self.assertTrue(i.validateBinding())
        i = union('two')
        self.assertTrue(i.validateBinding())
        i = xs.int(53.42)
        i = union(52.43)
        i = listUnion([1, 3, 'one', 'two', 2])
        self.assertTrue(i.validateBinding())

    def testListMemberConversion (self):
        i = listUnion([])
        self.assertTrue(isinstance(i, list))
        self.assertEqual(0, len(i))
        i.extend([1, 3, 'one', 'two', 2])
        self.assertTrue(isinstance(i[0], xs.int))
        self.assertTrue(isinstance(i[2], tEnum))
        self.assertTrue(i.validateBinding())
        # setitem
        i[0] = 23
        self.assertTrue(isinstance(i[0], xs.int))
        self.assertEqual(23, i[0])
        self.assertTrue('one' in i)
        self.assertEqual(2, i.index('one'))
        self.assertEqual(5, len(i))
        i[2:2] = [ 37 ]
        self.assertEqual(6, len(i))
        self.assertEqual(37, i[2])
        self.assertTrue(isinstance(i[2], xs.int))
        self.assertEqual(3, i.index('one'))
        i[:2] = []
        self.assertEqual(4, len(i))
        self.assertEqual(37, i[0])
        i[1:] = [ 'two' ]
        self.assertEqual(2, len(i))
        self.assertEqual(1, i.index('two'))
        
    def testAttribute (self):
        #i = structure(attr='three')
        #self.assertRaises(pyxb.BindingValidationError, i.validateBinding)
        i = structure(attr=4)
        self.assertTrue(i.validateBinding())
        i = structure(attr='two')
        self.assertTrue(i.validateBinding())
        

if __name__ == '__main__':
    unittest.main()
    
