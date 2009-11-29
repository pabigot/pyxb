import unittest
import common

class Test (unittest.TestCase):
    def testBase (self):
        b = common.base('hi')
        self.assertEqual(b.elt, 'hi')

    def testNamespaceInfo (self):
        ns = common.Namespace
        ns.validateComponentModel()
        self.assertEqual(1, len(ns.moduleRecords()))

if '__main__' == __name__:
    unittest.main()
        
