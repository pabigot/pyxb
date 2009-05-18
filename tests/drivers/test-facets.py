import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-facets.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestFacets (unittest.TestCase):
    def testQuantity (self):
        xml = '<quantity>35</quantity>'
        instance = CreateFromDOM(pyxb.utils.domutils.StringToDOM(xml).documentElement)
        self.assertEqual(35, instance.content())
        for (k,v) in globals().items():
            if k.startswith('_STD_ANON'):
                break
        self.assertEqual(v, instance._TypeDefinition)
        self.assertRaises(Exception, v, -52)
        self.assertRaises(Exception, v, 100)

if __name__ == '__main__':
    unittest.main()
    
