import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/particle.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    return instance.toDOM().documentElement

class TestParticle (unittest.TestCase):
    def test_bad_creation (self):
        xml = '<h01 xmlns="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        # Creating with wrong element
        self.assertRaises(pyxb.StructuralBadDocumentError, h01b.createFromDOM, dom.documentElement)

    def test_h01_empty (self):
        xml = '<ns1:h01 xmlns:ns1="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01.createFromDOM(dom.documentElement)
        self.assert_(instance.elt is None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01_elt (self):
        xml = '<ns1:h01 xmlns:ns1="URN:test"><elt/></ns1:h01>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01.createFromDOM(dom.documentElement)
        self.assert_(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01_elt2 (self):
        xml = '<h01 xmlns="URN:test"><elt/><elt/></h01>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, h01.createFromDOM, dom.documentElement)

    def test_h01b_empty (self):
        xml = '<ns1:h01b xmlns:ns1="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01b.createFromDOM(dom.documentElement)
        self.assert_(instance.elt is None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01b_elt (self):
        xml = '<ns1:h01b xmlns:ns1="URN:test"><elt/></ns1:h01b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01b.createFromDOM(dom.documentElement)
        self.assert_(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01b_elt2 (self):
        xml = '<ns1:h01b xmlns:ns1="URN:test"><elt/><elt/></ns1:h01b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, h01b.createFromDOM, dom.documentElement)

    def test_h11_empty (self):
        xml = '<ns1:h11 xmlns:ns1="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h11.createFromDOM, dom.documentElement)

    def test_h11_elt (self):
        xml = '<ns1:h11 xmlns:ns1="URN:test"><elt/></ns1:h11>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h11.createFromDOM(dom.documentElement)
        self.assert_(instance.elt is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)


    def test_h24 (self):
        xml = '<h24 xmlns="URN:test"></h24>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h24.createFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<ns1:h24 xmlns:ns1="URN:test">%s</ns1:h24>' % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24.createFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24.createFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt))
                self.assertEqual(ToDOM(instance).toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24.createFromDOM, dom.documentElement)

    def test_h24b (self):
        xml = '<ns1:h24b xmlns:ns1="URN:test"></ns1:h24b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h24b.createFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<ns1:h24b xmlns:ns1="URN:test">%s</ns1:h24b>' % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24b.createFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24b.createFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt))
                self.assertEqual(ToDOM(instance).toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24b.createFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
