import pywxsb.binding.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-wildcard.xsd' % (os.path.dirname(__file__),)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestWildcard (unittest.TestCase):
    def testElement (self):
        xml = '<wrapper><first/><second/><third/></wrapper>'
        doc = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(doc.documentElement)

    def testAttribute (self):
        xml = '<wrapper myattr="true" auxattr="somevalue"/>'
        doc = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(doc.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
