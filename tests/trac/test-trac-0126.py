import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://www.w3.org/2001/XMLSchema">
  <element name="Element">
   <complexType name="tElement">
     <attribute name="Required" type="string" use="required"/>
     <attribute name="Optional" type="string" use="optional"/>
   </complexType>
  </element>
</schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0126 (unittest.TestCase):
    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testBasic (self):
        instance = Element()
        self.assertEqual(None, instance.Required)
        self.assertEqual(None, instance.Optional)
        
        pyxb.RequireValidWhenGenerating(False)
        self.assertEqual('<Element/>', instance.toDOM().documentElement.toxml("utf-8"))
        pyxb.RequireValidWhenGenerating(True)
        self.assertRaises(pyxb.MissingAttributeError, instance.toDOM)
        instance.Required = 'value'
        xmls = instance.toDOM().documentElement.toxml("utf-8");
        self.assertEqual('<Element Required="value"/>', xmls)


if __name__ == '__main__':
    unittest.main()
    
