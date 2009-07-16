import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

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
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0032 (unittest.TestCase):
    """Storage of non-plural simple lists broken"""
    def testBasic (self):
        instance = aggregate()
        instance.setLi([1,2,3])
        self.assertEqual(1, len(instance.content()))
        instance = aggregate([1,2,3])
        self.assertEqual(1, len(instance.content()))

if __name__ == '__main__':
    unittest.main()
    
