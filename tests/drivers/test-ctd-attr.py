import pywxsb.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ctd-attr.xsd' % (os.path.dirname(__file__),)
code = pywxsb.generate.GeneratePython(schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestCTD (unittest.TestCase):

    # Make sure that name collisions are deconflicted in favor of the
    # element declaration.
    def testDeconflict (self):
        self.assert_(issubclass(structure, pywxsb.binding.basis.element))
        self.assert_(issubclass(structure_, pywxsb.binding.basis.CTD_element))

    def testSimple (self):
        self.assertEqual('test', simple_('test').content())

        # Note that when the element is a complex type with simple
        # content, we remove the extra level of indirection so the
        # element content is the same as the ctd content.  Otherwise,
        # you'd have to do foo.content().content() to get to the
        # interesting stuff.  I suppose that ought to be a
        # configuration option.
        self.assertEqual('test', simple('test').content())
        xml = '<simple>test</simple>'
        instance = CreateFromDocument(xml)
        self.assertEqual('test', instance.content())
        self.assertEqual(xml, instance.toDOM().toxml())

    def testString (self):
        self.assertEqual('test', datatypes.string('test'))
        rv = string('test')
        self.assert_(isinstance(rv.content(), datatypes.string))
        self.assertEqual('test', rv.content())
        rv = CreateFromDocument('<string>test</string>')
        self.assert_(isinstance(rv, string))
        self.assertEqual('test', rv.content())

    def testEmptyWithAttr (self):
        self.assertEqual(3, len(emptyWithAttr._TypeDefinition._AttributeMap))
        self.assertRaises(MissingAttributeError, CreateFromDocument, '<emptyWithAttr/>')
        instance = CreateFromDocument('<emptyWithAttr capitalized="false"/>')
        self.assertEqual('irish', instance.language())
        self.assert_(not instance.capitalized())
        self.assertEqual(5432, instance.port())
        instance = CreateFromDocument('<emptyWithAttr capitalized="true" language="hebrew"/>')
        self.assertEqual('hebrew', instance.language())
        self.assert_(instance.capitalized())
        self.assertEqual(5432, instance.port())
        # Raw constructor generates default everything; optional
        # attributes may have value None.
        instance = emptyWithAttr()
        self.assertEqual('irish', instance.language())
        self.assert_(instance.capitalized() is None)
        self.assertEqual(5432, instance.port())
        self.assertEqual('<emptyWithAttr/>', instance.toDOM().toxml())

        # Create another instance, to make sure the attributes are different
        instance2 = emptyWithAttr()
        self.assertEqual('irish', instance2.language())
        instance2.setLanguage('french')
        self.assertEqual('<emptyWithAttr language="french"/>', instance2.toDOM().toxml())
        self.assertNotEqual(instance.language(), instance2.language())


    def testEmptyWithAttrGroups (self):
        xml = '<emptyWithAttrGroups bMember1="xxx"/>'
        instance = CreateFromDocument(xml)
        self.assertEqual('gM1', instance.groupMember1())
        self.assertEqual('gM2', instance.groupMember2())
        self.assertEqual('xxx', instance.bMember1())
        self.assertEqual('lA1', instance.localAttr1())
        # Note that defaulted attributes are not generated in the DOM.
        self.assertEqual(xml, instance.toDOM().toxml())

    def testStructureElement (self):
        #self.assertEqual('test', CreateFromDocument('<structure>test</structure>'))
        pass

if __name__ == '__main__':
    unittest.main()
    
        
