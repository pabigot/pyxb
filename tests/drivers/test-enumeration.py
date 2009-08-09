import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/enumerations.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestEnumerations (unittest.TestCase):
    def testString (self):
        self.assertRaises(pyxb.BadTypeValueError, eString, 'fourteen')
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, '<eString>fourteen</eString>')
        self.assertEqual('one', eString('one'))
        self.assertEqual('one', CreateFromDocument('<eString>one</eString>'))
        self.assertEqual(eString.typeDefinition().one, 'one')

    def testInteger (self):
        self.assertRaises(pyxb.BadTypeValueError, eInteger, 4)
        self.assertRaises(pyxb.BadTypeValueError, eInteger, '4')
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, '<eInteger>4</eInteger>')
        self.assertRaises(pyxb.BadTypeValueError, eInteger) # Value defaults to zero, not in enumeration
        self.assertEqual(3, eInteger(3))
        self.assertEqual(3, CreateFromDocument('<eInteger>3</eInteger>'))
        self.assertEqual(21, eInteger(21))
        self.assertEqual(21, CreateFromDocument('<eInteger>21</eInteger>'))

    def testDouble (self):
        self.assertRaises(pyxb.BadTypeValueError, eDouble, 2)
        self.assertRaises(pyxb.BadTypeValueError, eDouble, 2.0)
        self.assertRaises(pyxb.BadTypeValueError, eDouble, '2')
        self.assertRaises(pyxb.BadTypeValueError, eDouble, '2.0')
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, '<eDouble>2</eDouble>')
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, '<eDouble>2.0</eDouble>')
        self.assertRaises(pyxb.BadTypeValueError, eDouble) # Value defaults to zero, not in enumeration
        self.assertEqual(1.0, eDouble(1.0))
        self.assertEqual(1.0, CreateFromDocument('<eDouble>1</eDouble>'))
        self.assertEqual(1.0, CreateFromDocument('<eDouble>1.0</eDouble>'))
        self.assertEqual(1.5, eDouble(1.5))
        self.assertEqual(1.5, CreateFromDocument('<eDouble>1.5</eDouble>'))
        self.assertEqual(1.7, eDouble(1.7))
        self.assertEqual(1.7, CreateFromDocument('<eDouble>1.7</eDouble>'))

    def testAny (self):
        self.assertRaises(pyxb.BadTypeValueError, eAny, 2)
        self.assertRaises(pyxb.BadTypeValueError, eAny, '2')
        self.assertRaises(pyxb.BadTypeValueError, CreateFromDocument, '<eAny>2</eAny>')
        self.assertEqual('one', eAny('one'))
        self.assertEqual('one', CreateFromDocument('<eAny>one</eAny>'))
        self.assertEqual(eAny.typeDefinition().one, eAny('one'))
        self.assertEqual('1', eAny('1'))
        self.assertEqual(eAny.typeDefinition().n1, eAny('1'))
        self.assertEqual('1.0', eAny('1.0'))
        self.assertEqual(eAny.typeDefinition().n1_0, eAny('1.0'))

if __name__ == '__main__':
    unittest.main()
    
        
