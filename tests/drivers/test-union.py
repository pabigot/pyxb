import pyxb.binding.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-union.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestUnion (unittest.TestCase):
    def test (self):
        self.assertRaises(LogicError, myUnion, 5)
        self.assertEqual(5, myUnion.Factory(5))
        self.assertEqual(5, myUnion.Factory('5'))
        self.assertRaises(BadTypeValueError, myUnion.Factory, 10)
        self.assert_(isinstance(myUnion.Factory('5'), singleDigit))
        self.assert_(isinstance(myUnion.Factory('one'), english))
        self.assertEqual(welsh.un, myUnion.Factory('un'))
        self.assert_(isinstance(myUnion.Factory('un'), welsh))
        self.assertEqual(english.one, myUnion.Factory('one'))
        self.assertRaises(LogicError, myUnion, 'five')

    def testList (self):
        my_list = unionList([ myUnion.Factory(4), myUnion.Factory('one')])
        self.assertEqual(2, len(my_list))

    def testRestrictedUnion (self):
        self.assertEqual(ones.one, ones.Factory('one'))
        self.assertRaises(BadTypeValueError, ones.Factory, 'two')
        self.assertEqual(ones.un, ones.Factory('un'))

    def testAnonymousUnion (self):
        self.assertEqual('four', words2.Factory('four'))
        self.assertEqual('pump', words2.Factory('pump'))
        self.assertRaises(BadTypeValueError,  words2.Factory, 'one')

    def testMyElement (self):
        self.assertEqual(0, myElement('0').content())
        self.assertEqual(english.two, myElement('two').content())
        self.assertEqual(welsh.tri, myElement('tri').content())
        self.assertRaises(BadTypeValueError, myElement, 'five')

    def testValidation (self):
        # Test automated conversion
        uv = myUnion._ValidateMember('one')
        self.assertTrue(isinstance(uv, english))
        uv = myUnion._ValidateMember('tri')
        self.assertTrue(isinstance(uv, welsh))

    def testXMLErrors (self):
        self.assertEqual(welsh.un, CreateFromDocument('<myElement>un</myElement>').content())
        self.assertRaises(NotAnElementError, CreateFromDocument, '<welsh>un</welsh>')
        self.assertRaises(UnrecognizedElementError, CreateFromDocument, '<myelement>un</myelement>')

    def testMyElementDOM (self):
        self.assertEqual(0, myElement.CreateFromDOM(minidom.parseString('<myElement>0</myElement>').documentElement).content())
        self.assertEqual(0, CreateFromDocument('<myElement>0</myElement>').content())

        self.assertEqual(english.one, myElement.CreateFromDOM(minidom.parseString('<myElement>one</myElement>').documentElement).content())
        self.assertEqual(welsh.un, myElement.CreateFromDOM(minidom.parseString('<myElement>un</myElement>').documentElement).content())

        self.assertEqual(english.one, myElement.CreateFromDOM(minidom.parseString('<myElement>one<!-- with comment --></myElement>').documentElement).content())
        self.assertEqual(welsh.un, myElement.CreateFromDOM(minidom.parseString('<myElement><!-- with comment -->un</myElement>').documentElement).content())

        self.assertEqual(english.one, myElement.CreateFromDOM(minidom.parseString('<myElement> one <!-- with comment and whitespace --></myElement>').documentElement).content())
        self.assertRaises(BadTypeValueError, myElement.CreateFromDOM, minidom.parseString('<myElement><!-- whitespace is error for welsh --> un</myElement>').documentElement)

        self.assertEqual(english.one, myElement.CreateFromDOM(minidom.parseString('''<myElement><!-- whitespace is collapsed for english -->
one
</myElement>''').documentElement).content())
        self.assertRaises(BadTypeValueError, myElement.CreateFromDOM, minidom.parseString('''<myElement><!--whitespace is only reduced for welsh -->
un
</myElement>''').documentElement)

if __name__ == '__main__':
    unittest.main()
    
