import pywxsb.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/particle.xsd' % (os.path.dirname(__file__),)
code = pywxsb.generate.GeneratePython(schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestParticle (unittest.TestCase):
    def test_bad_creation (self):
        xml = '<h01/>'
        dom = minidom.parseString(xml)
        # Creating with wrong element
        self.assertRaises(UnrecognizedContentError, h01b.CreateFromDOM, dom.documentElement)

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

    def test_h01_elt2 (self):
        xml = '<h01><elt/><elt/></h01>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, h01.CreateFromDOM, dom.documentElement)

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

    def test_h01b_elt2 (self):
        xml = '<h01b><elt/><elt/></h01b>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, h01b.CreateFromDOM, dom.documentElement)

    def test_h11_empty (self):
        xml = '<h11/>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, h11.CreateFromDOM, dom.documentElement)

    def test_h11_elt (self):
        xml = '<h11><elt/></h11>'
        dom = minidom.parseString(xml)
        instance = h11.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(instance.toDOM().toxml(), xml)


    def test_h24 (self):
        xml = '<h24></h24>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, h24.CreateFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<h24>%s</h24>' % (''.join(num_elt * ['<elt/>']),)
            dom = minidom.parseString(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24.CreateFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24.CreateFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt()))
                self.assertEqual(instance.toDOM().toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24.CreateFromDOM, dom.documentElement)

    def test_h24b (self):
        xml = '<h24b></h24b>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, h24b.CreateFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<h24b>%s</h24b>' % (''.join(num_elt * ['<elt/>']),)
            dom = minidom.parseString(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24b.CreateFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24b.CreateFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt()))
                self.assertEqual(instance.toDOM().toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24b.CreateFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
