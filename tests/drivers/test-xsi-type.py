import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/xsi-type.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):
    def testFailsNoType (self):
        xml = '<elt/>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, doc.documentElement)

    def testDirect (self):
        xml = '<notAlt attrOne="low"><first>content</first></notAlt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        print xml
        print instance.first()
        print instance.attrOne()

    def testSubstitutions (self):
        xml = '<elt attrOne="low" xsi:type="alt1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><first>content</first></elt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        print xml
        print instance.first()
        print instance.attrOne()
        xml = '<elt attrTwo="hi" xsi:type="alt2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><second/></elt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        print instance.second()
        print instance.attrTwo()

if __name__ == '__main__':
    unittest.main()
    
        
