import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-empty-cstd.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestEmptyCSTD (unittest.TestCase):
    def testPresent (self):
        xmls = '<time xmlns="urn:test">http://test/something</time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("http://test/something", instance.value())
    def testMissing (self):
        xmls = '<time xmlns="urn:test"></time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("", instance.value())
    def testWhitespace (self):
        xmls = '<time xmlns="urn:test">   </time>'
        instance = CreateFromDocument(xmls)
        self.assertEqual(u'', instance.value())
    def testEmpty (self):
        xmls = '<time xmlns="urn:test"/>'
        instance = CreateFromDocument(xmls)
        self.assertEqual("", instance.value())

if __name__ == '__main__':
    unittest.main()
    
