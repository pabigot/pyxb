import PyWXSB.generate

code = PyWXSB.generate.GeneratePython('schemas/kml21.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestKML (unittest.TestCase):
    def testAngle180 (self):
        self.assertEqual(25.4, angle360(25.4))
        self.assertRaises(BadTypeValueError, angle360, 420.0)
        self.assertRaises(BadTypeValueError, angle360, -361.0)
        
if __name__ == '__main__':
    unittest.main()
    
