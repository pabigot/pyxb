import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-mg-choice.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    dom_support = domutils.BindingDOMSupport()
    parent = None
    if tag is not None:
        parent = dom_support.document().appendChild(dom_support.document().createElement(tag))
    dom_support = instance.toDOM(dom_support, parent)
    return dom_support.finalize().documentElement

import unittest

class TestMGChoice (unittest.TestCase):
    def onlyFirst (self, instance):
        self.assert_(isinstance(instance.first(), choice_first._TypeDefinition))
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)

    def onlySecond (self, instance):
        self.assert_(instance.first() is None)
        self.assert_(isinstance(instance.second(), choice_second._TypeDefinition))
        self.assert_(instance.third() is None)

    def onlyThird (self, instance):
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), choice_third._TypeDefinition))

    def testSingleChoice (self):
        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"><first/></ns1:choice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyFirst(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"><second/></ns1:choice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlySecond(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"><third/></ns1:choice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyThird(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testMissingSingle (self):
        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, choice.CreateFromDOM, dom.documentElement)

    def testTooManySingle (self):
        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"><first/><second/></ns1:choice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, choice.CreateFromDOM, dom.documentElement)

        xml = '<ns1:choice xmlns:ns1="URN:test-mg-choice"><second/><third/></ns1:choice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, choice.CreateFromDOM, dom.documentElement)

    def testMultichoice (self):
        xml = '<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/></ns1:multiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/><first/><first/><third/></ns1:multiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(3, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testMultichoiceOrderImportant (self):
        xml = '<ns1:multiplechoice xmlns:ns1="URN:test-mg-choice"><first/><third/><first/></ns1:multiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        # @todo This test will fail because both firsts will precede the second.
        #self.assertEqual(ToDOM(instance).toxml(), xml)


    def testAltMultichoice (self):
        xml = '<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"><first/></ns1:altmultiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<ns1:altmultiplechoice xmlns:ns1="URN:test-mg-choice"><first/><first/><third/></ns1:altmultiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testTooManyChoices (self):
        xml = '<altmultiplechoice xmlns="URN:test-mg-choice"><first/><first/><first/><third/></altmultiplechoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, altmultiplechoice.CreateFromDOM, dom.documentElement)

    def testFixedMultichoice (self):
        xml = '<fixedMultichoice xmlns="URN:test-mg-choice"></fixedMultichoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = fixedMultichoice.CreateFromDOM(dom.documentElement)
        xml = '<ns1:fixedMultichoice xmlns:ns1="URN:test-mg-choice"><A/><A/></ns1:fixedMultichoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = fixedMultichoice.CreateFromDOM(dom.documentElement)
        xml = '<ns1:fixedMultichoice xmlns:ns1="URN:test-mg-choice"><A/><B/></ns1:fixedMultichoice>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, fixedMultichoice.CreateFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
