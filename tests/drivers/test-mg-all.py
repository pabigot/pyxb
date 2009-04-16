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

        xml = '<required><first/><third/></required>'
        dom = minidom.parseString(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first))
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), required_third))

    def testRequiredMisordered (self):
        xml = '<required><third/><first/><second/></required>'
        dom = minidom.parseString(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first))
        self.assert_(isinstance(instance.second(), required_second))
        self.assert_(isinstance(instance.third(), required_third))

        xml = '<required><third/><first/></required>'
        dom = minidom.parseString(xml)
        instance = required.CreateFromDOM(dom.documentElement)
        self.assert_(isinstance(instance.first(), required_first))
        self.assert_(instance.second() is None)
        self.assert_(isinstance(instance.third(), required_third))

    def testRequiredTooMany (self):
        xml = '<required><third/><first/><third/></required>'
        dom = minidom.parseString(xml)
        self.assertRaises(ExtraContentError, required.CreateFromDOM, dom.documentElement)

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

    

if __name__ == '__main__':
    unittest.main()
    
        
