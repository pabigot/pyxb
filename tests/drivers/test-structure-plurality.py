# Test the infrastructure that determines whether specific element
# names should be treated as single values or collections.

import pyxb
import pyxb.xmlschema as xs
import pyxb.namespace as Namespace
from pyxb.xmlschema.structures import _PluralityData
from pyxb.xmlschema.structures import ModelGroup

import unittest

Namespace.XMLSchema.validateComponentModel()

class _TestBase (unittest.TestCase):
    __schema = None
    def schema (self): return self.__schema

    def _edKW (self):
        return self.__edKW
    __edKW = None

    def _prtKW (self):
        return self.__prtKW
    __prtKW = None

    def _mgKW (self):
        return self.__mgKW
    __mgKW = None

    def setUp (self):
        target_namespace=Namespace.CreateAbsentNamespace()
        self.__generationUID = pyxb.utils.utility.UniqueIdentifier()
        self.__schema = xs.schema(namespace_context=target_namespace.initialNamespaceContext(), schema_location=str(target_namespace), generation_uid=self.__generationUID)
        self.__edKW = { 'namespace_context' : self.__schema.targetNamespace().initialNamespaceContext()
                      , 'scope' : xs.structures._ScopedDeclaration_mixin.SCOPE_global
                      , 'schema' : self.__schema
                      , 'context' : xs.structures._ScopedDeclaration_mixin.SCOPE_global }
        self.__prtKW = { 'namespace_context' : self.__schema.targetNamespace().initialNamespaceContext()
                       , 'scope' : xs.structures._ScopedDeclaration_mixin.XSCOPE_indeterminate
                       , 'schema' : self.__schema
                       , 'context' : xs.structures._ScopedDeclaration_mixin.SCOPE_global }
        self.__mgKW = { 'namespace_context' : self.__schema.targetNamespace().initialNamespaceContext()
                      , 'scope' : xs.structures._ScopedDeclaration_mixin.XSCOPE_indeterminate
                      , 'schema' : self.__schema
                      , 'context' : xs.structures._ScopedDeclaration_mixin.SCOPE_global }

        for ( name, type ) in [ ( 'selt', 'string' ), ( 'ielt', 'int' ), ( 'belt', 'boolean' ) ]:
            ed = xs.structures.ElementDeclaration(name=name, **self._edKW())
            ed._typeDefinition(Namespace.XMLSchema.typeDefinitions().get(type, None))
            # Fake out resolution, which we don't care about for this test
            ed._ElementDeclaration__isResolved = True
            self.__schema._addNamedComponent(ed)
            setattr(self, name, ed)

    def _getSingleElements (self):
        return [ xs.structures.Particle(self.selt, **self._prtKW()),
                 xs.structures.Particle(self.ielt, **self._prtKW())]

    def _getMultiElements (self):
        return [ xs.structures.Particle(self.selt, max_occurs=4, **self._prtKW()),
                 xs.structures.Particle(self.ielt, max_occurs=None, **self._prtKW()),
                 xs.structures.Particle(self.belt, **self._prtKW())]

    def _getRepeatedElements (self):
        return [xs.structures.Particle(self.selt, **self._prtKW()),
                xs.structures.Particle(self.selt, **self._prtKW()),
                xs.structures.Particle(self.belt, **self._prtKW())]

    def _getMGRepeated (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getRepeatedElements(), **self._mgKW())

    def _getMGSingle (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getSingleElements(), **self._mgKW())

    def _getMGMulti (self, compositor):
        return ModelGroup(compositor=compositor, particles=self._getMultiElements(), **self._mgKW())

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
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=0, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        self.assertEqual({}, pd[0])

    def testSingleElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=1, max_occurs=1, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[ed])

    def testOptionalElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=0, max_occurs=1, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertFalse(pdm[ed])

    def testMultipleElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=3, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[ed])

    def testUnboundedElement (self):
        ed = self.selt
        prt = xs.structures.Particle(ed, min_occurs=3, max_occurs=None, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(1, len(pdm))
        self.assertTrue(pdm[ed])

    def testZeroMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=0, max_occurs=0, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        self.assertEqual({}, pd[0])
        
    def testOptionalMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=0, max_occurs=1, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertFalse(pdm[self.belt])
        
    def testMultipleMGSeq (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=3, max_occurs=3, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])
        
    def testUnboundedMGSeq (self):
        ed = self.selt
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_SEQUENCE), min_occurs=3, max_occurs=None, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])

    def testOptionalMGChoice (self):
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_CHOICE), min_occurs=0, max_occurs=1, **self._prtKW())
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
        prt = xs.structures.Particle(self._getMGMulti(ModelGroup.C_CHOICE), min_occurs=3, max_occurs=3, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(3, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.ielt])
        self.assertTrue(pdm[self.belt])

    def testSingleSequenceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_SEQUENCE), **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertFalse(pdm[self.belt])
        
    def testSingleChoiceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_CHOICE), **self._prtKW())
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
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_SEQUENCE), max_occurs=2, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.belt])
        
    def testMultiChoiceRepeated (self):
        prt = xs.structures.Particle(self._getMGRepeated(ModelGroup.C_CHOICE), max_occurs=2, **self._prtKW())
        pd = prt.pluralityData()
        self.assertEqual(1, len(pd))
        pdm = pd[0]
        self.assertEqual(2, len(pdm))
        self.assertTrue(pdm[self.selt])
        self.assertTrue(pdm[self.belt])

if __name__ == '__main__':
    unittest.main()
    
        
