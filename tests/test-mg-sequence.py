import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-mg-sequence.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestMGSeq (unittest.TestCase):
    def testBad (self):
        # Second is wrong elementt ag
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
        print instance.toDOM().toxml()

    def testMissing (self):
        xml = '<wrapper><first/><third/></wrapper>'
        dom = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), sequence_first))
        self.assert_(instance.second_opt() is None)
        self.assert_(isinstance(instance.third(), sequence_third))
        self.assert_(isinstance(instance.fourth_0_2(), list))
        self.assertEqual(0, len(instance.fourth_0_2()))
        self.assertEqual(xml, instance.toDOM().toxml())
        print instance.toDOM().toxml()

if __name__ == '__main__':
    unittest.main()
    
        
