import pyxb.binding.generate
import pyxb.binding.datatypes as xsd
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ctd-simple.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestCTDSimple (unittest.TestCase):

    def testClause4 (self):
        self.assertTrue(clause4._IsSimpleTypeContent())
        self.assertTrue(clause4._TypeDefinition == xsd.string)

if __name__ == '__main__':
    unittest.main()
    
        
