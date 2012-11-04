import pyxb
import trac26
import unittest

class TestAbstractElementError (unittest.TestCase):
    def testSchemaSupport (self):
        cym1 = trac26.eConcCardCymru('un')
        eng3 = trac26.eConcCardEnglish('three')
        instance = trac26.eCardinals()
        self.assertEqual(0, len(instance.eAbstractCard))
        instance.append(cym1)
        self.assertEqual(1, len(instance.eAbstractCard))
        instance.append(eng3)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(instance.validateBinding())
        xmls = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmls, '<eCardinals><eConcCardCymru>un</eConcCardCymru><eConcCardEnglish>three</eConcCardEnglish></eCardinals>')

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.AbstractElementError) as cm:
            instance = trac26.eAbstractCard('un')
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertEqual(e.element, trac26.eAbstractCard)
        self.assertEqual(e.value, ('un',))
        self.assertEqual(str(e), 'AbstractElementError: Cannot instantiate element eAbstractCard directly')

if __name__ == '__main__':
    unittest.main()
