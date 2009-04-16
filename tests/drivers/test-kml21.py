import pywxsb.binding.generate

import os.path
schema_path = '%s/../../pywxsb/standard/schemas/kml21.xsd' % (os.path.dirname(__file__),)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest

class TestKML (unittest.TestCase):
    def testAngle180 (self):
        self.assertEqual(25.4, angle360(25.4))
        self.assertRaises(BadTypeValueError, angle360, 420.0)
        self.assertRaises(BadTypeValueError, angle360, -361.0)
        
if __name__ == '__main__':
    unittest.main()
    
