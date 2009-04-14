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
        self.assertEqual(1, len(tWrapper._ElementNameMap))
        self.assertEqual(('field', True), tWrapper._ElementNameMap['field'])
        self.assertTrue(isinstance(tWrapper.field, types.ListType))

    def testInstance (self):
        pass
        #wr = wrapper()
        #self.assertTrue(isinstance(wr.field, types.ListType))

if __name__ == '__main__':
    unittest.main()
    
