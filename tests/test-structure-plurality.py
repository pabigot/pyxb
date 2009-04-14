# Test the infrastructure that determines whether specific element
# names should be treated as single values or collections.

import PyWXSB.XMLSchema as xs
from PyWXSB.exceptions_ import *
import PyWXSB.Namespace as Namespace

import unittest

Namespace.XMLSchema.validateSchema()

class _TestBase (unittest.TestCase):
    __schema = None
    def schema (self): return self.__schema

    def setUp (self):
        self.__schema = xs.schema()
        for ( name, type ) in [ ( 'selt', 'string' ), ( 'ielt', 'int' ), ( 'belt', 'boolean' ) ]:
            ed = xs.structures.ElementDeclaration(name=name, schema=self.__schema)
            ed._typeDefinition(Namespace.XMLSchema.lookupTypeDefinition(type))
            self.__schema._addNamedComponent(ed)
    
class TestED (_TestBase):
    def testBasic (self):
        ed = self.schema().lookupElement('selt')
        self.assert_(ed.isResolved())
        pd = ed.pluralityData()
        self.assertEqual(1, len(pd))
        ( tag, count ) = pd[0]
        self.assertEqual(ed.ncName(), tag)
        self.assertEqual(1, count)

class testMG (_TestBase):
    def testSequence (self):
        pass

    def testAll (self):
        pass

    def testChoice (self):
        pass

class testParticle (_TestBase):
    def testSingle (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=1, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        (name, count) = pd[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(1, count)

    def testOptional (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        (name, count) = pd[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(1, count)

    def testMultiple (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=3, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        (name, count) = pd[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(3, count)

    def testUnbounded (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=None, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        (name, count) = pd[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(None, count)

if __name__ == '__main__':
    unittest.main()
    
        
