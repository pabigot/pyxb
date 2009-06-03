import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-mg-all.xsd' % (os.path.dirname(__file__),)
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

class TestMGAll (unittest.TestCase):
    def testRequired (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, required.CreateFromDOM, dom.documentElement)

        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first._TypeDefinition))
        self.assert_(isinstance(instance.second(), required_second._TypeDefinition))
        self.assert_(isinstance(instance.third(), required_third._TypeDefinition))

    def testRequiredMisordered (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first._TypeDefinition))
        self.assert_(isinstance(instance.second(), required_second._TypeDefinition))
        self.assert_(isinstance(instance.third(), required_third._TypeDefinition))

    def testRequiredTooMany (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, required.CreateFromDOM, dom.documentElement)

    def testThirdOptional (self):
        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional_first._TypeDefinition))
        self.assert_(isinstance(instance.second(), thirdOptional_second._TypeDefinition))
        self.assert_(instance.third() is None)

        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional_first._TypeDefinition))
        self.assert_(isinstance(instance.second(), thirdOptional_second._TypeDefinition))
        self.assert_(isinstance(instance.third(), thirdOptional_third._TypeDefinition))

        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/><first/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, thirdOptional.CreateFromDOM, dom.documentElement)

    def testOptional (self):
        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional_first._TypeDefinition))
        self.assert_(isinstance(instance.second(), optional_second._TypeDefinition))
        self.assert_(isinstance(instance.third(), optional_third._TypeDefinition))

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional_first._TypeDefinition))
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional_third._TypeDefinition))

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional_third._TypeDefinition))

    def testOptionalTooMany (self):
        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, optional.CreateFromDOM, dom.documentElement)

    def stripMembers (self, xml, body):
        for b in body:
            xml = xml.replace('<%s/>' % (b,), 'X')
        return xml

    def testMany (self):
        for body in [ "abcdefgh", "fghbcd", "bfgcahd" ]:
            xml = '<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join([ '<%s/>' % (_x,) for _x in body ]),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            instance = many.CreateFromDOM(dom.documentElement)
            rev = self.stripMembers(ToDOM(instance).toxml(), body)
            self.assertEqual('<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join(len(body)*['X']),), rev)

if __name__ == '__main__':
    unittest.main()
    
        
