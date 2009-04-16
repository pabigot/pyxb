import pywxsb.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-ambiguous.xsd' % (os.path.dirname(__file__),)
code = pywxsb.generate.GeneratePython(schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

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
    
