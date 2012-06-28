import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" 
           xmlns="http://schema.omg.org/spec/CTS2/1.0/Core" 
           targetNamespace="http://schema.omg.org/spec/CTS2/1.0/Core" 
           elementFormDefault="qualified">
    <xs:complexType mixed="true" name="tsAnyType">
        <xs:sequence>
            <xs:any maxOccurs="unbounded" minOccurs="0" namespace="##any" processContents="lax"/>
        </xs:sequence>
    </xs:complexType>

    <xs:element name="OpaqueData">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="v" type="tsAnyType" minOccurs="1"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>'''

file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class Test_Mixed2 (unittest.TestCase):
    testxml = """<?xml version="1.0" encoding="UTF-8"?>
<OpaqueData xmlns="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:core="http://schema.omg.org/spec/CTS2/1.0/Core"
    xmlns:html="http://www.w3.org/1999/xhtml"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <core:v xmlns="http://www.w3.org/1999/xhtml"><ul><li>entry1</li><li>entry2</li></ul></core:v>
</OpaqueData> """

    def test (self):
	""" This fails because namespaces continue to be assigned """
	
	# It can sort of be fixed by changing:
	#
	# domutils.py line 250:
	# def declareNamespace (self, namespace, prefix=None, add_to_map=False):
	# -to-
	# def declareNamespace (self, namespace, prefix=None, add_to_map=True):
	#
	# and domutils line 280:
	# if prefix in self.__prefixes:
	# -to-
	# if prefix in self.__prefixes and not add_to_map:
	#
	# it still assigns namespaces to <li>, but it is at least semantically correct
    	pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(Namespace.uri())
        txml = CreateFromDocument(self.testxml)
	print "-" * 10
	print txml.toxml()
	print "-" * 10
	self.assertEqual(txml.toxml(), """<?xml version="1.0" ?>
<OpaqueData xmlns="http://schema.omg.org/spec/CTS2/1.0/Core" xmlns:ns1="http://www.w3.org/1999/xhtml"><v><ns1:ul><li>entry1</li><li>entry2</li></ns1:ul></v></OpaqueData>""")


if __name__ == '__main__':
    unittest.main()
