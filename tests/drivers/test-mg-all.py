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
def ToDOM (instance):
    return instance.toDOM().documentElement

import unittest

class TestMGAll (unittest.TestCase):
    def testRequired (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(MissingContentError, required.createFromDOM, dom.documentElement)

        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = required.createFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required.typeDefinition()._ElementMap['first'].element2().typeDefinition()))
        self.assert_(isinstance(instance.second(), required.typeDefinition()._ElementMap['second'].element2().typeDefinition()))
        self.assert_(isinstance(instance.third(), required.typeDefinition()._ElementMap['third'].element2().typeDefinition()))

    def testRequiredMisordered (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = required.createFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required.typeDefinition()._ElementMap['first'].element2().typeDefinition()))
        self.assert_(isinstance(instance.second(), required.typeDefinition()._ElementMap['second'].element2().typeDefinition()))
        self.assert_(isinstance(instance.third(), required.typeDefinition()._ElementMap['third'].element2().typeDefinition()))

    def testRequiredTooMany (self):
        xml = '<ns1:required xmlns:ns1="URN:test-mg-all"><third/><first/><second/><third/></ns1:required>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, required.createFromDOM, dom.documentElement)

    def testThirdOptional (self):
        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional._ElementMap['first'].element2().typeDefinition()))
        self.assert_(isinstance(instance.second(), thirdOptional._ElementMap['second'].element2().typeDefinition()))
        self.assert_(instance.third() is None)

        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional._ElementMap['first'].element2().typeDefinition()))
        self.assert_(isinstance(instance.second(), thirdOptional._ElementMap['second'].element2().typeDefinition()))
        self.assert_(isinstance(instance.third(), thirdOptional._ElementMap['third'].element2().typeDefinition()))

        xml = '<ns1:thirdOptional xmlns:ns1="URN:test-mg-all"><first/><second/><third/><first/></ns1:thirdOptional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, thirdOptional.CreateFromDOM, dom.documentElement)

    def testOptional (self):
        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"/>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.createFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><second/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.createFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional.typeDefinition()._ElementMap['first'].element2().typeDefinition()))
        self.assert_(isinstance(instance.second(), optional.typeDefinition()._ElementMap['second'].element2().typeDefinition()))
        self.assert_(isinstance(instance.third(), optional.typeDefinition()._ElementMap['third'].element2().typeDefinition()))

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.createFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional.typeDefinition()._ElementMap['first'].element2().typeDefinition()))
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional.typeDefinition()._ElementMap['third'].element2().typeDefinition()))

        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance = optional.createFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional.typeDefinition()._ElementMap['third'].element2().typeDefinition()))

    def testOptionalTooMany (self):
        xml = '<ns1:optional xmlns:ns1="URN:test-mg-all"><third/><first/><third/></ns1:optional>'
        dom = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, optional.createFromDOM, dom.documentElement)

    def stripMembers (self, xml, body):
        for b in body:
            xml = xml.replace('<%s/>' % (b,), 'X')
        return xml

    def testMany (self):
        for body in [ "abcdefgh", "fghbcd", "bfgcahd" ]:
            xml = '<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join([ '<%s/>' % (_x,) for _x in body ]),)
            dom = pyxb.utils.domutils.StringToDOM(xml)
            instance = many.createFromDOM(dom.documentElement)
            instance.validateBinding()
            xml2 = ToDOM(instance).toxml()
            rev = self.stripMembers(xml2, body)
            self.assertEqual('<ns1:many xmlns:ns1="URN:test-mg-all">%s</ns1:many>' % (''.join(len(body)*['X']),), rev)
        many_a = many.typeDefinition()._ElementMap['a'].element2()
        many_c = many.typeDefinition()._ElementMap['c'].element2()
        many_d = many.typeDefinition()._ElementMap['d'].element2()
        many_e = many.typeDefinition()._ElementMap['e'].element2()
        many_f = many.typeDefinition()._ElementMap['f'].element2()
        many_g = many.typeDefinition()._ElementMap['g'].element2()
        many_h = many.typeDefinition()._ElementMap['h'].element2()
        instance = many(a=many_a(), c=many_c(), d=many_d(), e=many_e(), f=many_f(), g=many_g(), h=many_h())
        self.assertRaises(pyxb.BindingValidationError, instance.validateBinding)
        self.assertRaises(pyxb.DOMGenerationError, ToDOM, instance)

if __name__ == '__main__':
    unittest.main()
    
        
