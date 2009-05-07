import pyxb.binding.generate
from xml.dom import minidom
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
        self.assert_(isinstance(instance.first(), choice_first))
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)

    def onlySecond (self, instance):
        self.assert_(instance.first() is None)
        self.assert_(isinstance(instance.second(), choice_second))
        self.assert_(instance.third() is None)

    def onlyThird (self, instance):
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), choice_third))

    def testSingleChoice (self):
        xml = '<choice xmlns="URN:test-mg-choice"><first/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyFirst(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<choice xmlns="URN:test-mg-choice"><second/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlySecond(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<choice xmlns="URN:test-mg-choice"><third/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyThird(instance)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testMissingSingle (self):
        xml = '<choice/>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, choice.CreateFromDOM, dom.documentElement)

    def testTooManySingle (self):
        xml = '<choice><first/><second/></choice>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, choice.CreateFromDOM, dom.documentElement)

        xml = '<choice><second/><third/></choice>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, choice.CreateFromDOM, dom.documentElement)

    def testMultichoice (self):
        xml = '<multiplechoice xmlns="URN:test-mg-choice"/>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<multiplechoice xmlns="URN:test-mg-choice"><first/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<multiplechoice xmlns="URN:test-mg-choice"><first/><first/><first/><third/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(3, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testMultichoiceOrderImportant (self):
        xml = '<multiplechoice xmlns="URN:test-mg-choice"><first/><third/><first/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        # @todo This test will fail because both firsts will precede the second.
        #self.assertEqual(ToDOM(instance).toxml(), xml)


    def testAltMultichoice (self):
        xml = '<altmultiplechoice xmlns="URN:test-mg-choice"/>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<altmultiplechoice xmlns="URN:test-mg-choice"><first/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

        xml = '<altmultiplechoice xmlns="URN:test-mg-choice"><first/><first/><third/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def testTooManyChoices (self):
        xml = '<altmultiplechoice xmlns="URN:test-mg-choice"><first/><first/><first/><third/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, altmultiplechoice.CreateFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
