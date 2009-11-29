import pyxb.binding.generate

import os.path
schema_path = '%s/../schemas/test-simplerange.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestKML (unittest.TestCase):
    def testAngle360 (self):
        self.assertEqual(25.4, angle360(25.4))
        self.assertRaises(BadTypeValueError, angle360, 420.0)
        self.assertRaises(BadTypeValueError, angle360, -361.0)
        
if __name__ == '__main__':
    unittest.main()
    
