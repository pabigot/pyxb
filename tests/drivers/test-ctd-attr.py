import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ctd-attr.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

class TestCTD (unittest.TestCase):


    # Make sure that name collisions are deconflicted in favor of the
    # element declaration.
    def testDeconflict (self):
        self.assert_(issubclass(structure, pyxb.binding.basis.element))
        self.assert_(issubclass(structure_, pyxb.binding.basis.complexTypeDefinition))
        self.assert_(pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY == structure_._ContentTypeTag)

    def testSimple (self):
        self.assertEqual('test', simple_('test').content())

        # Note that when the element is a complex type with simple
        # content, we remove the extra level of indirection so the
        # element content is the same as the ctd content.  Otherwise,
        # you'd have to do foo.content().content() to get to the
        # interesting stuff.  I suppose that ought to be a
        # configuration option.
        self.assertEqual('test', simple('test').content())
        xml = '<ns1:simple xmlns:ns1="URN:testCTD">test</ns1:simple>'
        instance = CreateFromDocument(xml)
        self.assertEqual('test', instance.content())
        self.assertEqual(xml, ToDOM(instance).toxml())

    def testString (self):
        self.assertEqual('test', pyxb.binding.datatypes.string('test'))
        rv = string('test')
        self.assert_(isinstance(rv.content(), pyxb.binding.datatypes.string))
        self.assertEqual('test', rv.content())
        rv = CreateFromDocument('<string xmlns="URN:testCTD">test</string>')
        self.assert_(isinstance(rv, string))
        self.assertEqual('test', rv.content())

    def testEmptyWithAttr (self):
        self.assertEqual(5, len(emptyWithAttr._TypeDefinition._AttributeMap))
        self.assertRaises(MissingAttributeError, CreateFromDocument, '<emptyWithAttr xmlns="URN:testCTD"/>')
        instance = CreateFromDocument('<emptyWithAttr capitalized="false" xmlns="URN:testCTD"/>')
        self.assertEqual('irish', instance.language())
        self.assert_(not instance.capitalized())
        self.assertEqual(5432, instance.port())
        self.assertEqual('top default', instance.tlAttr())
        self.assertEqual('stone', instance.immutable())

        instance.setTlAttr('new value')
        self.assertEqual('new value', instance.tlAttr())

        # Can't change immutable attributes
        self.assertRaises(AttributeChangeError, instance.setImmutable, 'water')
        self.assertRaises(AttributeChangeError, CreateFromDocument, '<emptyWithAttr capitalized="true" immutable="water"  xmlns="URN:testCTD"/>')

        instance = CreateFromDocument('<emptyWithAttr capitalized="true" language="hebrew"  xmlns="URN:testCTD"/>')
        self.assertEqual('hebrew', instance.language())
        self.assert_(instance.capitalized())
        self.assertEqual(5432, instance.port())
        # Raw constructor generates default everything; optional
        # attributes may have value None.
        instance = emptyWithAttr()
        self.assertEqual('irish', instance.language())
        self.assert_(instance.capitalized() is None)
        self.assertEqual(5432, instance.port())
        self.assertEqual('<ns1:emptyWithAttr xmlns:ns1="URN:testCTD"/>', ToDOM(instance).toxml())

        # Test reference attribute
        self.assertEqual('top default', instance.tlAttr())

        # Create another instance, to make sure the attributes are different
        instance2 = emptyWithAttr()
        self.assertEqual('irish', instance2.language())
        instance2.setLanguage('french')
        self.assertEqual('<ns1:emptyWithAttr language="french" xmlns:ns1="URN:testCTD"/>', ToDOM(instance2).toxml())
        self.assertNotEqual(instance.language(), instance2.language())

        # Verify the use.  Note reference through CTD not element.
        au = emptyWithAttr_._AttributeMap['language']
        self.assertFalse(au.required())
        self.assertFalse(au.prohibited())
        au = emptyWithAttr_._AttributeMap['capitalized']
        self.assertTrue(au.required())
        self.assertFalse(au.prohibited())

    def testRestrictedEWA (self):
        # Verify the use.  Note reference through CTD not element.
        self.assertNotEqual(restrictedEWA_._AttributeMap['language'], emptyWithAttr_._AttributeMap['language'])
        au = restrictedEWA_._AttributeMap['language']
        self.assertFalse(au.required())
        self.assertTrue(au.prohibited())
        self.assertNotEqual(restrictedEWA_._AttributeMap['capitalized'], emptyWithAttr_._AttributeMap['capitalized'])

    def testEmptyWithAttrGroups (self):
        xml = '<ns1:emptyWithAttrGroups bMember1="xxx" xmlns:ns1="URN:testCTD"/>'
        instance = CreateFromDocument(xml)
        self.assertEqual('gM1', instance.groupMember1())
        self.assertEqual('gM2', instance.groupMember2())
        self.assertEqual('xxx', instance.bMember1())
        self.assertEqual('lA1', instance.localAttr1())
        # Note that defaulted attributes are not generated in the DOM.
        self.assertEqual(xml, ToDOM(instance).toxml())

        # Test reference attribute with changed default
        self.assertEqual('refDefault', instance.tlAttr())

    def testUnrecognizedAttribute (self):
        xml = '<emptyWithAttr capitalized="false" garbage="what is this" xmlns="URN:testCTD"/>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(UnrecognizedAttributeError, emptyWithAttr.CreateFromDOM, doc.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
