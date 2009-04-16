import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-mg-choice.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

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
        xml = '<choice><first/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyFirst(instance)
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<choice><second/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlySecond(instance)
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<choice><third/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.onlyThird(instance)
        self.assertEqual(instance.toDOM().toxml(), xml)

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
        xml = '<multiplechoice/>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<multiplechoice><first/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<multiplechoice><first/><first/><first/><third/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(3, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

    def testMultichoiceOrderImportant (self):
        xml = '<multiplechoice><first/><third/><first/></multiplechoice>'
        dom = minidom.parseString(xml)
        instance = multiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        # @todo This test will fail because both firsts will precede the second.
        #self.assertEqual(instance.toDOM().toxml(), xml)


    def testAltMultichoice (self):
        xml = '<altmultiplechoice/>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(0, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<altmultiplechoice><first/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(1, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(0, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<altmultiplechoice><first/><first/><third/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        instance = altmultiplechoice.CreateFromDOM(dom.documentElement)
        self.assertEqual(2, len(instance.first()))
        self.assertEqual(0, len(instance.second()))
        self.assertEqual(1, len(instance.third()))
        self.assertEqual(instance.toDOM().toxml(), xml)

    def testTooManyChoices (self):
        xml = '<altmultiplechoice><first/><first/><first/><third/></altmultiplechoice>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, altmultiplechoice.CreateFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
