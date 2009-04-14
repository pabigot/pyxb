import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-ambiguous.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import types
import unittest

class TestAmbiguous (unittest.TestCase):
    def testType (self):
        self.assertEqual(1, len(tWrapper._ElementMap))
        ef = tWrapper._ElementMap['field']
        self.assertEqual('field', ef.pythonTag())
        self.assertTrue(ef.isPlural())
        self.assertEqual([], ef.defaultValue())

    def testInstance (self):
        pass
        #wr = wrapper()
        #self.assertTrue(isinstance(wr.field, types.ListType))

if __name__ == '__main__':
    unittest.main()
    
