import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ctd-extension.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestCTDExtension (unittest.TestCase):

    def testStructure (self):
        # Extension should be a subclass of parent
        self.assert_(issubclass(extendedName, personName))
        # References in subclass to parent class elements/attributes
        # should be the same, unless content model requires they be
        # different.
        self.assertEqual(extendedName.title, personName.title)
        self.assertEqual(extendedName.pAttr, personName.pAttr)

    def testPersonName (self):
        xml = '''<oldAddressee pAttr="old">
   <forename>Albert</forename>
   <forename>Arnold</forename>
   <surname>Gore</surname>
  </oldAddressee>'''
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = oldAddressee.CreateFromDOM(doc.documentElement)
        self.assertEqual(2, len(instance.forename()))
        # Note double dereference required because xs:anyType was used
        # as the element type
        self.assertEqual('Albert', instance.forename()[0].content().content())
        self.assertEqual('Arnold', instance.forename()[1].content().content())
        self.assertEqual('Gore', instance.surname().content().content())
        self.assertEqual('old', instance.pAttr())

    def testExtendedName (self):
        xml = '''<addressee pAttr="new" eAttr="add generation">
   <forename>Albert</forename>
   <forename>Arnold</forename>
   <surname>Gore</surname>
   <generation>Jr</generation>
  </addressee>'''
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = addressee.CreateFromDOM(doc.documentElement)
        self.assertEqual(2, len(instance.forename()))
        self.assertEqual('Albert', instance.forename()[0].content().content())
        self.assertEqual('Arnold', instance.forename()[1].content().content())
        self.assertEqual('Gore', instance.surname().content().content())
        self.assertEqual('Jr', instance.generation().content().content())
        self.assertEqual('new', instance.pAttr())
        self.assertEqual('add generation', instance.eAttr())

    def testMidWildcard (self):
        xml = '<defs><documentation/><something/><message/><message/><import/><message/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = defs.CreateFromDOM(doc.documentElement)
        self.assertFalse(instance.documentation() is None)
        self.assertEqual(3, len(instance.message()))
        self.assertEqual(1, len(instance.import_()))
        self.assertEqual(1, len(instance.wildcardElements()))

        xml = '<defs><something/><else/><message/><message/><import/><message/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = defs.CreateFromDOM(doc.documentElement)
        self.assertTrue(instance.documentation() is None)
        self.assertEqual(3, len(instance.message()))
        self.assertEqual(1, len(instance.import_()))
        self.assertEqual(2, len(instance.wildcardElements()))

    def testEndWildcard (self):
        xml = '<defs><message/><something/></defs>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(ExtraContentError, defs.CreateFromDOM, doc.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
