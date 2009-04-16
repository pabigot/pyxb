import pywxsb.binding.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-mg-sequence.xsd' % (os.path.dirname(__file__),)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestMGSeq (unittest.TestCase):
    def testBad (self):
        # Second is wrong element tag
        xml = '<wrapper><first/><second/><third/><fourth_0_2/></wrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(UnrecognizedContentError, wrapper.CreateFromDOM, dom.documentElement)

    def testBasics (self):
        xml = '<wrapper><first/><second_opt/><third/><fourth_0_2/></wrapper>'
        dom = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first))
        self.assert_(isinstance(instance.second_opt(), sequence_second_opt))
        self.assert_(isinstance(instance.third(), sequence_third))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(1, len(instance.fourth_0_2()))
        self.assert_(isinstance(instance.fourth_0_2()[0], sequence_fourth_0_2))
        self.assertEqual(xml, instance.toDOM().toxml())

    def testMultiplesAtEnd (self):
        xml = '<wrapper><first/><third/><fourth_0_2/><fourth_0_2/></wrapper>'
        dom = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first))
        self.assert_(instance.second_opt() is None)
        self.assert_(isinstance(instance.third(), sequence_third))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(2, len(instance.fourth_0_2()))
        self.assert_(isinstance(instance.fourth_0_2()[0], sequence_fourth_0_2))
        self.assertEqual(xml, instance.toDOM().toxml())

    def testMultiplesInMiddle (self):
        xml = '<altwrapper><first/><second_multi/><second_multi/><third/></altwrapper>'
        dom = minidom.parseString(xml)
        instance = altwrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), list))
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(2, len(instance.second_multi()))
        self.assert_(isinstance(instance.third(), altsequence_third))
        self.assertEqual(xml, instance.toDOM().toxml())

    def testMultiplesAtStart (self):
        xml = '<altwrapper><first/><first/><third/></altwrapper>'
        dom = minidom.parseString(xml)
        instance = altwrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), list))
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second_multi()))
        self.assert_(isinstance(instance.third(), altsequence_third))
        self.assertEqual(xml, instance.toDOM().toxml())

    def testMissingInMiddle (self):
        xml = '<wrapper><first/><third/></wrapper>'
        dom = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first))
        self.assert_(instance.second_opt() is None)
        self.assert_(isinstance(instance.third(), sequence_third))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(0, len(instance.fourth_0_2()))
        self.assertEqual(xml, instance.toDOM().toxml())

    def testMissingAtStart (self):
        xml = '<altwrapper><third/></altwrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testMissingAtEndLeadingContent (self):
        xml = '<altwrapper><first/></altwrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testMissingAtEndNoContent (self):
        xml = '<altwrapper></altwrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testTooManyAtEnd (self):
        xml = '<wrapper><first/><third/><fourth_0_2/><fourth_0_2/><fourth_0_2/></wrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, wrapper.CreateFromDOM, dom.documentElement)

    def testTooManyAtStart (self):
        xml = '<altwrapper><first/><first/><first/><third/></altwrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testTooManyInMiddle (self):
        xml = '<altwrapper><second_multi/><second_multi/><second_multi/><third/></altwrapper>'
        dom = minidom.parseString(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)


if __name__ == '__main__':
    unittest.main()
    
        
