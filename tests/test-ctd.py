import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-ctd.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestCTD (unittest.TestCase):
    def testSimple (self):
        self.assertEqual('test', simple.Factory('test').content())

if __name__ == '__main__':
    unittest.main()
    
        
