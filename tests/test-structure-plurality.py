# Test the infrastructure that determines whether specific element
# names should be treated as single values or collections.

import PyWXSB.XMLSchema as xs
from PyWXSB.exceptions_ import *
import PyWXSB.Namespace as Namespace

import unittest

Namespace.XMLSchema.validateSchema()

class TestED (unittest.TestCase):
    __schema = None

    def setUp (self):
        if self.__schema is None:
            self.__schema = xs.schema()
            ed = xs.structures.ElementDeclaration(name='foo', schema=self.__schema)
            ed._typeDefinition(Namespace.XMLSchema.lookupTypeDefinition('string'))
            self.__schema._addNamedComponent(ed)

    def testBasic (self):
        ed = self.__schema.lookupElement('foo')
        self.assert_(ed.isResolved())
        pd = ed.pluralityData()
        self.assertEqual(1, len(pd))
        ( tag, count ) = pd[0]
        self.assertEqual(ed.ncName(), tag)
        self.assertEqual(1, count)

class testMGD (unittest.TestCase):

    def setUp (self):
        self.__schema = xs.schema()

    def testSequence (self):
        pass

    def testAll (self):
        pass

    def testChoice (self):
        pass

if __name__ == '__main__':
    unittest.main()
    
        
