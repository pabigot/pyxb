import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/particle.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    dom_support = domutils.BindingDOMSupport()
    parent = None
    if tag is not None:
        parent = dom_support.document().appendChild(dom_support.document().createElement(tag))
    dom_support = instance.toDOM(dom_support, parent)
    return dom_support.finalize().documentElement

class TestParticle (unittest.TestCase):
    def test_bad_creation (self):
        xml = '<h01 xmlns="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        # Creating with wrong element
        self.assertRaises(UnrecognizedContentError, h01b.CreateFromDOM, dom.documentElement)

    def test_h01_empty (self):
        xml = '<h01 xmlns="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01_elt (self):
        xml = '<h01 xmlns="URN:test"><elt/></h01>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01_elt2 (self):
        xml = '<h01 xmlns="URN:test"><elt/><elt/></h01>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, h01.CreateFromDOM, dom.documentElement)

    def test_h01b_empty (self):
        xml = '<h01b xmlns="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01b.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01b_elt (self):
        xml = '<h01b xmlns="URN:test"><elt/></h01b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h01b.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)

    def test_h01b_elt2 (self):
        xml = '<h01b xmlns="URN:test"><elt/><elt/></h01b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, h01b.CreateFromDOM, dom.documentElement)

    def test_h11_empty (self):
        xml = '<h11 xmlns="URN:test"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h11.CreateFromDOM, dom.documentElement)

    def test_h11_elt (self):
        xml = '<h11 xmlns="URN:test"><elt/></h11>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = h11.CreateFromDOM(dom.documentElement)
        self.assert_(instance.elt() is not None)
        self.assertEqual(ToDOM(instance).toxml(), xml)


    def test_h24 (self):
        xml = '<h24 xmlns="URN:test"></h24>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h24.CreateFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<h24 xmlns="URN:test">%s</h24>' % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24.CreateFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24.CreateFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt()))
                self.assertEqual(ToDOM(instance).toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24.CreateFromDOM, dom.documentElement)

    def test_h24b (self):
        xml = '<h24b xmlns="URN:test"></h24b>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, h24b.CreateFromDOM, dom.documentElement)
        
        for num_elt in range(0, 5):
            xml = '<h24b xmlns="URN:test">%s</h24b>' % (''.join(num_elt * ['<elt/>']),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            if 2 > num_elt:
                self.assertRaises(MissingContentError, h24b.CreateFromDOM, dom.documentElement)
            elif 4 >= num_elt:
                instance = h24b.CreateFromDOM(dom.documentElement)
                self.assertEqual(num_elt, len(instance.elt()))
                self.assertEqual(ToDOM(instance).toxml(), xml)
            else:
                self.assertRaises(ExtraContentError, h24b.CreateFromDOM, dom.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
