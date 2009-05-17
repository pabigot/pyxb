import pyxb.binding.generate
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ambiguous.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import types
import unittest

class TestAmbiguous (unittest.TestCase):
    def testType (self):
        self.assertEqual(1, len(tWrapper._ElementMap))
        ef = tWrapper._ElementMap['field']
        self.assertEqual('field', ef.pythonField())
        self.assertTrue(ef.isPlural())
        self.assertEqual([], ef.defaultValue())

    def testInstance (self):
        pass
        #wr = wrapper()
        #self.assertTrue(isinstance(wr.field, types.ListType))

if __name__ == '__main__':
    unittest.main()
    
