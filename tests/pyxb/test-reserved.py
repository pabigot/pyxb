import unittest
import pyxb.binding.basis

class TestReserved (unittest.TestCase):
    def testSTD (self):
        tSTD = pyxb.binding.basis.simpleTypeDefinition
        for k in tSTD.__dict__.keys():
            if not k.startswith('_'):
                self.assertTrue(k in tSTD._ReservedSymbols, k)

    def testCTD (self):
        tCTD = pyxb.binding.basis.complexTypeDefinition
        for k in tCTD.__dict__.keys():
            if not k.startswith('_'):
                self.assertTrue(k in tCTD._ReservedSymbols, k)

if '__main__' == __name__:
    unittest.main()
    
