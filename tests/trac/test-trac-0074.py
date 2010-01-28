import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import xml.dom.minidom
import StringIO

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:trac-0074">
<xs:element name="top" type="xs:string"/>
</xs:schema>'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0074 (unittest.TestCase):
    def test (self):
        t0p = Namespace.createExpandedName('t0p')
        xmls = '<ns:t0p xmlns:ns="urn:trac-0074">content</ns:t0p>'
        dom = xml.dom.minidom.parseString(xmls)
        try:
            dom_instance = CreateFromDOM(dom.documentElement)
            self.fail('DOM creation succeeded')
        except pyxb.UnrecognizedElementError, e:
            self.assertEqual(t0p, e.element_name)
            self.assertEqual(dom.documentElement, e.dom_node)

        saxdom = pyxb.utils.saxdom.parseString(xmls)
        try:
            saxdom_instance = CreateFromDOM(saxdom)
            self.fail('SAXDOM creation succeeded')
        except pyxb.UnrecognizedElementError, e:
            self.assertEqual(t0p, e.element_name)
            self.assertEqual(saxdom.documentElement, e.dom_node)

        saxer = pyxb.binding.saxer.make_parser()
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xmls))
        try:
            sax_instance = handler.rootObject()
            self.fail('SAXER creation succeeded')
        except pyxb.UnrecognizedElementError, e:
            self.assertEqual(t0p, e.element_name)

if __name__ == '__main__':
    unittest.main()
