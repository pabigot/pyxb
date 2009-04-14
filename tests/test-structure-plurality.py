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
    
    def _getSingleElements (self):
        return [ xs.structures.Particle(self.schema().lookupElement('selt'), schema=self.schema()),
                 xs.structures.Particle(self.schema().lookupElement('ielt'), schema=self.schema())]

    def _getMultiElements (self):
        return [ xs.structures.Particle(self.schema().lookupElement('selt'), max_occurs=4, schema=self.schema()),
                 xs.structures.Particle(self.schema().lookupElement('ielt'), max_occurs=None, schema=self.schema())]

    def _getMGSingle (self, compositor):
        return xs.structures.ModelGroup(compositor=compositor, particles=self._getSingleElements(), schema=self.schema())

    def _getMGMulti (self, compositor):
        return xs.structures.ModelGroup(compositor=compositor, particles=self._getMultiElements(), schema=self.schema())

class TestED (_TestBase):
    def testBasic (self):
        ed = self.schema().lookupElement('selt')
        self.assert_(ed.isResolved())
        pd = ed.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pd))
        ( tag, count ) = pde[0]
        self.assertEqual(ed.ncName(), tag)
        self.assertEqual(1, count)

class TestMG (_TestBase):
    def testSequenceSingleElements (self):
        mgd = self._getMGSingle(xs.structures.ModelGroup.C_SEQUENCE)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(2, len(pde))
        self.assert_( ('selt', 1) in pde )
        self.assert_( ('ielt', 1) in pde )

    def testSequenceMultiElements (self):
        mgd = self._getMGMulti(xs.structures.ModelGroup.C_SEQUENCE)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(2, len(pde))
        self.assert_( ('selt', 4) in pde )
        self.assert_( ('ielt', None) in pde )

    def testAllSingleElements (self):
        mgd = self._getMGSingle(xs.structures.ModelGroup.C_ALL)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(2, len(pde))
        self.assert_( ('selt', 1) in pde )
        self.assert_( ('ielt', 1) in pde )

    def testAllMultiElements (self):
        mgd = self._getMGMulti(xs.structures.ModelGroup.C_ALL)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(2, len(pde))
        self.assert_( ('selt', 4) in pde )
        self.assert_( ('ielt', None) in pde )

    def testChoiceSingleElements (self):
        mgd = self._getMGSingle(xs.structures.ModelGroup.C_CHOICE)
        pd = mgd.pluralityData()
        self.assertEqual(2, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        self.assert_( ('selt', 1) in pde )
        pde = pd[1]
        self.assertEqual(1, len(pde))
        self.assert_( ('ielt', 1) in pde )

    def testChoiceMultiElements (self):
        mgd = self._getMGMulti(xs.structures.ModelGroup.C_CHOICE)
        pd = mgd.pluralityData()
        self.assertEqual(2, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        self.assert_( ('selt', 4) in pde )
        pde = pd[1]
        self.assertEqual(1, len(pde))
        self.assert_( ('ielt', None) in pde )

class TestParticle (_TestBase):
    def testSingleElement (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=1, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        (name, count) = pde[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(1, count)

    def testOptionalElement (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        (name, count) = pde[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(1, count)

    def testMultipleElement (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=3, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        (name, count) = pde[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(3, count)

    def testUnboundedElement (self):
        ed = self.schema().lookupElement('selt')
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=None, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pde = pd[0]
        self.assertEqual(1, len(pde))
        (name, count) = pde[0]
        self.assertEqual(ed.ncName(), name)
        self.assertEqual(None, count)

if __name__ == '__main__':
    unittest.main()
    
        
