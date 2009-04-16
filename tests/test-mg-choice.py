import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-mg-choice.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestMGChoice (unittest.TestCase):
    def testSingleChoice (self):
        xml = '<choice><first/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), choice_first))
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<choice><second/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(isinstance(instance.second(), choice_second))
        self.assert_(instance.third() is None)
        self.assertEqual(instance.toDOM().toxml(), xml)

        xml = '<choice><third/></choice>'
        dom = minidom.parseString(xml)
        instance = choice.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), choice_third))
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

if __name__ == '__main__':
    unittest.main()
    
        
