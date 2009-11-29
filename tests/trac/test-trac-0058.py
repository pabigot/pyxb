import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="iopt" nillable="true" type="xs:integer"/>
</xs:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0058 (unittest.TestCase):
    def testRoundTrip (self):
        xml = '<iopt xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"></iopt>'
        instance = CreateFromDocument(xml)
        self.assertTrue(instance._isNil())
        self.assertEqual(0, instance)
        self.assertEqual('', instance.xsdLiteral())
        self.assertEqual(xml, instance.toxml(root_only=True))

if __name__ == '__main__':
    unittest.main()
