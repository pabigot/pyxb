# Test the infrastructure that determines whether specific element
# names should be treated as single values or collections.

import pywxsb.xmlschema as xs
from pywxsb.exceptions_ import *
import pywxsb.Namespace as Namespace
from pywxsb.xmlschema.structures import _PluralityData
from pywxsb.xmlschema.structures import ModelGroup

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
            setattr(self, name, ed)

    def _getSingleElements (self):
        return [ xs.structures.Particle(self.selt, schema=self.schema()),
                 xs.structures.Particle(self.ielt, schema=self.schema())]

    def _getMultiElements (self):
        return [ xs.structures.Particle(self.selt, max_occurs=4, schema=self.schema()),
                 xs.structures.Particle(self.ielt, max_occurs=None, schema=self.schema()),
                 xs.structures.Particle(self.belt, schema=self.schema())]

    def _getRepeatedElements (self):
        return [xs.structures.Particle(self.selt, schema=self.schema()),
                xs.structures.Particle(self.selt, schema=self.schema()),
                xs.structures.Particle(self.belt, schema=self.schema())]

    def _getMGRepeated (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getRepeatedElements(), schema=self.schema())

    def _getMGSingle (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getSingleElements(), schema=self.schema())

    def _getMGMulti (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getMultiElements(), schema=self.schema())

class TestPluralityData (unittest.TestCase):

    def testMapUnion (self):
        m1 = { 'm1false' : False,
               'm1true' : True,
               'm12' : False }
        m2 = { 'm12' : False }
        m3 = { 'm12' : True,
               'm3' : False }
        rv = _PluralityData._MapUnion(m1, { })
        self.assertEqual(3, len(rv))
        self.assertTrue(rv['m1true'])
        self.assertFalse(rv['m1false'])
        rv = _PluralityData._MapUnion(m1, m1)
        self.assertEqual(3, len(rv))
        self.assertTrue(rv['m1true'])
        self.assertTrue(rv['m1false'])
        self.assertTrue(rv['m12'])
        rv = _PluralityData._MapUnion(m1, m2)
        self.assertEqual(3, len(rv))
        self.assertTrue(rv['m1true'])
        self.assertFalse(rv['m1false'])
        self.assertTrue(rv['m12'])
        rv = _PluralityData._MapUnion(m1, m3)
        self.assertEqual(4, len(rv))
        self.assertTrue(rv['m1true'])
        self.assertFalse(rv['m1false'])
        self.assertTrue(rv['m12'])
        self.assertFalse(rv['m3'])

class TestED (_TestBase):
    def testBasic (self):
        ed = self.selt
        self.assert_(ed.isResolved())
        pd = _PluralityData(ed)
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[ed])

class TestMG (_TestBase):
    def testSequenceSingleElements (self):
        mgd = self._getMGSingle(ModelGroup.C_SEQUENCE)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertFalse(pdm[self.selt])
        self.assertFalse(pdm[self.ielt])

    def testSequenceMultiElements (self):
        mgd = self._getMGMulti(ModelGroup.C_SEQUENCE)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertFalse(pdm[self.belt])

    def testSequenceRepeatedElements (self):
        mgd = self._getMGRepeated(ModelGroup.C_SEQUENCE)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertFalse(pdm[self.belt])

    def testAllSingleElements (self):
        mgd = self._getMGSingle(ModelGroup.C_ALL)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertFalse(pdm[self.selt])
        self.assertFalse(pdm[self.ielt])

    def testAllMultiElements (self):
        mgd = self._getMGMulti(ModelGroup.C_ALL)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertFalse(pdm[self.belt])

    def testAllRepeatedElements (self):
        mgd = self._getMGRepeated(ModelGroup.C_ALL)
        pd = mgd.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertFalse(pdm[self.belt])

    def testChoiceSingleElements (self):
        mgd = self._getMGSingle(ModelGroup.C_CHOICE)
        pd = mgd.pluralityData()
        self.assertEqual(2, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.selt])
        pdm = pd[1]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.ielt])

    def testChoiceMultiElements (self):
        mgd = self._getMGMulti(ModelGroup.C_CHOICE)
        pd = mgd.pluralityData()
        self.assertEqual(3, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[self.selt])
        pdm = pd[1]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[self.ielt])
        pdm = pd[2]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.belt])

    def testChoiceRepeatedElements (self):
        mgd = self._getMGRepeated(ModelGroup.C_CHOICE)
        pd = mgd.pluralityData()
        self.assertEqual(3, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.selt])
        pdm = pd[1]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.selt])
        pdm = pd[2]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.belt])

class TestParticle (_TestBase):
    def testZeroElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=0, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(0, len(pd))

    def testSingleElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=1, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[ed])

    def testOptionalElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[ed])

    def testMultipleElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=3, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[ed])

    def testUnboundedElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=None, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[ed])

    def testZeroMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=0, max_occurs=0, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(0, len(pd))
        
    def testOptionalMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=0, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertFalse(pdm[self.belt])
        
    def testMultipleMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=3, max_occurs=3, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])
        
    def testUnboundedMGSeq (self):
        ed = self.selt
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=3, max_occurs=None, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])

    def testOptionalMGChoice (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_CHOICE), min_occurs=0, max_occurs=1, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(3, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[self.selt])
        pdm = pd[1]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[self.ielt])
        pdm = pd[2]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.belt])
        
    def testMultiMGChoice (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_CHOICE), min_occurs=3, max_occurs=3, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])

    def testSingleSequenceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_SEQUENCE), schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertFalse(pdm[self.belt])
        
    def testSingleChoiceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_CHOICE), schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(3, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.selt])
        pdm = pd[1]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.selt])
        pdm = pd[2]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[self.belt])
        
    def testMultiSequenceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_SEQUENCE), max_occurs=2, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.belt])
        
    def testMultiChoiceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_CHOICE), max_occurs=2, schema=self.schema())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.belt])

if __name__ == '__main__':
    unittest.main()
    
        
