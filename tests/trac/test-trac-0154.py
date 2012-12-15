# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" 
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

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class Test_simple (unittest.TestCase):

    testxml = """<?xml version="1.0" encoding="UTF-8"?>
<OpaqueData
    xmlns:html="http://www.w3.org/1999/xhtml"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <v>test</v>
</OpaqueData>"""

    def test (self):
        txml = CreateFromDocument(self.testxml)
	self.assertEqual(txml.toxml(), """<?xml version="1.0" ?><OpaqueData><v>test</v></OpaqueData>""")


if __name__ == '__main__':
    unittest.main()
