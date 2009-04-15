import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/particle.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestParticle (unittest.TestCase):
    def test_bad_creation (self):
        xml = '<h01/>'
        dom = minidom.parseString(xml)
        # Creating with wrong element
        self.assertRaises(LogicError, h01b.CreateFromDOM, dom.documentElement)

    def test_h01_empty (self):
        xml = '<h01/>'
        dom = minidom.parseString(xml)
        instance = h01.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is None)
        self.assertEqual(instance.toDOM().toxml(), xml)

    def test_h01_elt (self):
        xml = '<h01><elt/></h01>'
        dom = minidom.parseString(xml)
        instance = h01.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(instance.toDOM().toxml(), xml)

    def test_h01b_empty (self):
        xml = '<h01b/>'
        dom = minidom.parseString(xml)
        instance = h01b.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is None)
        self.assertEqual(instance.toDOM().toxml(), xml)

    def test_h01b_elt (self):
        xml = '<h01b><elt/></h01b>'
        dom = minidom.parseString(xml)
        instance = h01b.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(instance.toDOM().toxml(), xml)

if __name__ == '__main__':
    unittest.main()
    
        
