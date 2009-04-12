import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-ctd.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestCTD (unittest.TestCase):

    # Make sure that name collisions are deconflicted in favor of the
    # element declaration.
    def testDeconflict (self):
        self.assert_(issubclass(structure, bindings.PyWXSB_element))
        self.assert_(issubclass(structure_, bindings.PyWXSB_CTD_element))

    def testSimple (self):
        self.assertEqual('test', simple_('test').content())

        # Note that when the element is a complex type with simple
        # content, we remove the extra level of indirection so the
        # element content is the same as the ctd content.  Otherwise,
        # you'd have to do foo.content().content() to get to the
        # interesting stuff.  I suppose that ought to be a
        # configuration option.
        self.assertEqual('test', simple('test').content())

        self.assertEqual('test', CreateFromDocument('<simple>test</simple>').content())

    def testString (self):
        self.assertEqual('test', datatypes.string('test'))
        rv = string('test')
        self.assert_(isinstance(rv.content(), datatypes.string))
        self.assertEqual('test', rv.content())
        rv = CreateFromDocument('<string>test</string>')
        self.assert_(isinstance(rv, string))
        self.assertEqual('test', rv.content())

    def testEmptyWithAttr (self):
        self.assertRaises(MissingAttributeError, CreateFromDocument, '<emptyWithAttr/>')
        instance = CreateFromDocument('<emptyWithAttr capitalized="false"/>')
        self.assertEqual('irish', instance.language())
        self.assert_(not instance.capitalized())
        instance = CreateFromDocument('<emptyWithAttr capitalized="true" language="hebrew"/>')
        self.assertEqual('hebrew', instance.language())
        self.assert_(instance.capitalized())

    def testEmptyWithAttrGroups (self):
        instance = CreateFromDocument('<emptyWithAttrGroups/>')
        self.assertEqual('gM1', instance.groupMember1())
        self.assertEqual('gM2', instance.groupMember2())
        self.assertEqual('bM1', instance.bMember1())
        self.assertEqual('lA1', instance.localAttr1())

    def testStructureElement (self):
        #self.assertEqual('test', CreateFromDocument('<structure>test</structure>'))
        pass

if __name__ == '__main__':
    unittest.main()
    
        
