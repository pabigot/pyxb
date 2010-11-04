import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd=u'''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
	<xs:element name="anything" type="xs:anyType" nillable="true"/>
</xs:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

import pyxb.utils.domutils
import pyxb.namespace
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(pyxb.namespace.XMLSchema, 'xs')

class TestTrac_0094 (unittest.TestCase):
    body = 'something'
    xmls = '''<anything xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:string">%s</anything>''' % (body,)

    def testFromXML (self):
        instance = CreateFromDocument(self.xmls)
        self.assertTrue(isinstance(instance, xs.string))
        self.assertEqual(instance, self.body)
        #self.assertEqual(instance._element(), anything)

    def testToXML (self):
        instance = xs.string(self.body, _element=anything)
        self.assertEqual(instance.toxml(root_only=True), self.xmls)
        

if __name__ == '__main__':
    unittest.main()
