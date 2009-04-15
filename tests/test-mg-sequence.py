import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-mg-sequence.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestMGSeq (unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
    
        
