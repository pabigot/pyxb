import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-mg-sequence.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    return instance.toDOM().documentElement

import unittest

class TestMGSeq (unittest.TestCase):
    def testBad (self):
        # Second is wrong element tag
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><second/><third/><fourth_0_2/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, wrapper.CreateFromDOM, dom.documentElement)

    def testBasics (self):
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><second_opt/><third/><fourth_0_2/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first._TypeDefinition))
        self.assert_(isinstance(instance.second_opt(), sequence_second_opt._TypeDefinition))
        self.assert_(isinstance(instance.third(), sequence_third._TypeDefinition))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(1, len(instance.fourth_0_2()))
        self.assert_(isinstance(instance.fourth_0_2()[0], sequence_fourth_0_2._TypeDefinition))
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testMultiplesAtEnd (self):
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/><fourth_0_2/><fourth_0_2/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first._TypeDefinition))
        self.assert_(instance.second_opt() is None)
        self.assert_(isinstance(instance.third(), sequence_third._TypeDefinition))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(2, len(instance.fourth_0_2()))
        self.assert_(isinstance(instance.fourth_0_2()[0], sequence_fourth_0_2._TypeDefinition))
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testMultiplesInMiddle (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><second_multi/><second_multi/><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = altwrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), list))
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(2, len(instance.second_multi()))
        self.assert_(isinstance(instance.third(), altsequence_third._TypeDefinition))
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testMultiplesAtStart (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><first/><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = altwrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), list))
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second_multi()))
        self.assert_(isinstance(instance.third(), altsequence_third._TypeDefinition))
        self.assertEqual(xml, ToDOM(instance).toxml())
        instance = altwrapper(first=[ altsequence_first(), altsequence_first() ], third=[altsequence_third()])
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testMissingInMiddle (self):
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first._TypeDefinition))
        self.assert_(instance.second_opt() is None)
        self.assert_(isinstance(instance.third(), sequence_third._TypeDefinition))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(0, len(instance.fourth_0_2()))
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testMissingAtStart (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)
        instance = altwrapper(third=[altsequence_third()])
        self.assertRaises(pyxb.DOMGenerationError, ToDOM, instance)

    def testMissingAtEndLeadingContent (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testMissingAtEndNoContent (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, altwrapper.CreateFromDOM, dom.documentElement)

    def testTooManyAtEnd (self):
        xml = '<ns1:wrapper xmlns:ns1="URN:test-mg-sequence"><first/><third/><fourth_0_2/><fourth_0_2/><fourth_0_2/></ns1:wrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, wrapper.CreateFromDOM, dom.documentElement)

    def testTooManyAtStart (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><first/><first/><first/><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)
        instance = altwrapper(first=[ altsequence_first(), altsequence_first(), altsequence_first() ], third=[altsequence_third()])
        self.assertRaises(pyxb.DOMGenerationError, ToDOM, instance)

    def testTooManyInMiddle (self):
        xml = '<ns1:altwrapper xmlns:ns1="URN:test-mg-sequence"><second_multi/><second_multi/><second_multi/><third/></ns1:altwrapper>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedContentError, altwrapper.CreateFromDOM, dom.documentElement)


if __name__ == '__main__':
    unittest.main()
    
        
