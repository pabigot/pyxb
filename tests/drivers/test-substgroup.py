import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.saxer
import StringIO

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/substgroup.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):
    def testISO8601 (self):
        xml = '<when><ISO8601>2009-06-15T17:50:00Z</ISO8601></when>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(dom.documentElement)
        self.assertEqual(instance.sgTime()._element(), ISO8601)
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
 
    def testPairTime (self):
        xml = '<when><pairTime><seconds>34.0</seconds><fractionalSeconds>0.21</fractionalSeconds></pairTime></when>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(dom.documentElement)
        self.assertEqual(instance.sgTime()._element(), pairTime)
        self.assertEqual(instance.sgTime().seconds(), 34)
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
 
    def testSGTime (self):
        xml = '<when><sgTime>2009-06-15T17:50:00Z</sgTime></when>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(pyxb.AbstractElementError, CreateFromDOM, dom.documentElement)

        xml = '<sgTime>2009-06-15T17:50:00Z</sgTime>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(pyxb.AbstractElementError, sgTime.createFromDOM, dom.documentElement)

        xml = '<ISO8601>2009-06-15T17:50:00Z</ISO8601>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = sgTime.createFromDOM(dom.documentElement)
        self.assertEqual(instance._element(), ISO8601)

    def testGenAbstract (self):
        xml = '<when><pairTime><seconds>34.0</seconds><fractionalSeconds>0.21</fractionalSeconds></pairTime></when>'
        instance = when(pairTime(34, 0.21))
        self.assertEqual(instance.sgTime()._element(), pairTime)
        self.assertEqual(instance.sgTime().seconds(), 34)
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
        # Loss of element association kills DOM generation
        instance.sgTime()._setElement(None)
        self.assertRaises(pyxb.DOMGenerationError, instance.toDOM)
        self.assertRaises(pyxb.AbstractElementError, sgTime)


if __name__ == '__main__':
    unittest.main()
    
        
