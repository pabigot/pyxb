import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-ambiguous.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestDeconflict (unittest.TestCase):
    def testAttributes (self):
        self.assertEqual(1, len(tWrapper._ElementNameMap))
        self.assertEqual(('field', True), tWrapper._ElementNameMap['field'])

if __name__ == '__main__':
    unittest.main()
    
