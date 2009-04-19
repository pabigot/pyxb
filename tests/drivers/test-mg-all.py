import pywxsb.binding.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-mg-all.xsd' % (os.path.dirname(__file__),)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestMGAll (unittest.TestCase):
    def testRequired (self):
        xml = '<required/>'
        dom = minidom.parseString(xml)
        self.assertRaises(MissingContentError, required.CreateFromDOM, dom.documentElement)

        xml = '<required><first/><second/><third/></required>'
        dom = minidom.parseString(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first))
        self.assert_(isinstance(instance.second(), required_second))
        self.assert_(isinstance(instance.third(), required_third))

    def testRequiredMisordered (self):
        xml = '<required><third/><first/><second/></required>'
        dom = minidom.parseString(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first))
        self.assert_(isinstance(instance.second(), required_second))
        self.assert_(isinstance(instance.third(), required_third))

    def testRequiredTooMany (self):
        xml = '<required><third/><first/><second/><third/></required>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, required.CreateFromDOM, dom.documentElement)

    def testThirdOptional (self):
        xml = '<thirdOptional><first/><second/></thirdOptional>'
        dom = minidom.parseString(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional_first))
        self.assert_(isinstance(instance.second(), thirdOptional_second))
        self.assert_(instance.third() is None)

        xml = '<thirdOptional><first/><second/><third/></thirdOptional>'
        dom = minidom.parseString(xml)
        instance = thirdOptional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), thirdOptional_first))
        self.assert_(isinstance(instance.second(), thirdOptional_second))
        self.assert_(isinstance(instance.third(), thirdOptional_third))

        xml = '<thirdOptional><first/><second/><third/><first/></thirdOptional>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, thirdOptional.CreateFromDOM, dom.documentElement)

    def testOptional (self):
        xml = '<optional/>'
        dom = minidom.parseString(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(instance.third() is None)

        xml = '<optional><first/><second/><third/></optional>'
        dom = minidom.parseString(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional_first))
        self.assert_(isinstance(instance.second(), optional_second))
        self.assert_(isinstance(instance.third(), optional_third))

        xml = '<optional><first/><third/></optional>'
        dom = minidom.parseString(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), optional_first))
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional_third))

        xml = '<optional><third/></optional>'
        dom = minidom.parseString(xml)
        instance = optional.CreateFromDOM(dom.documentElement)
        self.assert_(instance.first() is None)
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), optional_third))

    def testOptionalTooMany (self):
        xml = '<optional><third/><first/><third/></optional>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, optional.CreateFromDOM, dom.documentElement)

    def stripMembers (self, xml, body):
        for b in body:
            xml = xml.replace('<%s/>' % (b,), 'X')
        return xml

    def testMany (self):
        for body in [ "abcdefgh", "fghbcd", "bfgcahd" ]:
            xml = '<many>%s</many>' % (''.join([ '<%s/>' % (_x,) for _x in body ]),)
            dom = minidom.parseString(xml)
            instance = many.CreateFromDOM(dom.documentElement)
            rev = self.stripMembers(instance.toDOM().toxml(), body)
            self.assertEqual('<many>%s</many>' % (''.join(len(body)*['X']),), rev)

if __name__ == '__main__':
    unittest.main()
    
        
