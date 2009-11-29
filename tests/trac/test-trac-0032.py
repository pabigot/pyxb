import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node
import pyxb.binding.datatypes as xs

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
	<xs:simpleType name="intList">
		<xs:list itemType="xs:int"/>
	</xs:simpleType>
	<xs:element name="li" type="intList"/>
	<xs:complexType name="tAggregate">
		<xs:sequence>
			<xs:element ref="li"/>
		</xs:sequence>
	</xs:complexType>
	<xs:element name="aggregate" type="tAggregate"/>
	<xs:complexType name="tMultiAggregate">
		<xs:sequence>
			<xs:element ref="li" maxOccurs="unbounded"/>
		</xs:sequence>
	</xs:complexType>
	<xs:element name="multi" type="tMultiAggregate"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

def SET_li (instance, v):
    instance.li = v

class TestTrac0032 (unittest.TestCase):
    """Storage of non-plural simple lists broken"""
    def testBasic (self):
        instance = aggregate()
        instance.li = [1,2,3]
        self.assertEqual(3, len(instance.li))
        self.assertEqual(1, len(instance.content()))
        self.assertTrue(instance.validateBinding())

        self.assertRaises(pyxb.BadTypeValueError, SET_li, instance, 1)
        self.assertRaises(pyxb.BadTypeValueError, SET_li, instance, [[1,2,3], [2,3,4]])

        instance = aggregate([1,2,3])
        self.assertEqual(3, len(instance.li))
        self.assertEqual(1, len(instance.content()))
        self.assertTrue(instance.validateBinding())

        instance = aggregate(li=[1,2,3])
        self.assertEqual(3, len(instance.li))
        self.assertEqual(1, len(instance.content()))
        self.assertTrue(instance.validateBinding())

        instance = aggregate()
        instance.li = []
        instance.li.append(1)
        instance.li.append(2)
        instance.li.append(3)
        self.assertEqual(3, len(instance.li))
        # Yes, the content is a single value; the members of the
        # simple type list are not visible at the content model level.
        self.assertEqual(1, len(instance.content()))
        self.assertTrue(instance.validateBinding())

    def testMulti (self):
        instance = multi()
        self.assertRaises(pyxb.BadTypeValueError, SET_li, instance, 1)
        self.assertRaises(pyxb.BadTypeValueError, SET_li, instance, [1, 2, 3])
        instance.li = [[1,2,3], [2,3,4]]
        self.assertEqual(2, len(instance.li))
        self.assertTrue(instance.validateBinding())
        self.assertEqual(1, len(instance.content()))

        instance = multi([1,2,3], [1,2,3]) # two li values
        self.assertEqual(2, len(instance.li))
        self.assertTrue(instance.validateBinding())
        self.assertEqual(2, len(instance.content()))

        self.assertRaises(pyxb.UnrecognizedContentError, multi, [[1,2,3], [2,3,4]])
        self.assertRaises(pyxb.BadTypeValueError, multi, li=[1,2,3])

        instance = multi(li=[[1,2,3],[2,3,4]])
        self.assertEqual(2, len(instance.li))
        self.assertTrue(instance.validateBinding())
        self.assertEqual(1, len(instance.content()))

        instance = multi(li=[])
        instance.li.append(xs.int(1))
        self.assertRaises(pyxb.BindingValidationError, instance.validateBinding)

        instance = CreateFromDocument('<multi><li>1</li></multi>')
        self.assertEqual(1, len(instance.li))
        self.assertTrue(instance.validateBinding())
        self.assertEqual(1, len(instance.content()))
        
        instance.li = []
        instance.li.append([1,2,3])
        instance.li.append([2,3,4])
        self.assertEqual(2, len(instance.li))
        self.assertTrue(instance.validateBinding())
        self.assertEqual(2, len(instance.content()))

if __name__ == '__main__':
    unittest.main()
    
