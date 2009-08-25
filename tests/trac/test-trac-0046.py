import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
schema_path = '%s/../schemas/absentns.xsd' % (os.path.dirname(__file__),)

import unittest

class TestTrac_0046 (unittest.TestCase):
    def testParsing (self):
        xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="URN:trac0046" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:include schemaLocation="%s"/>
  <xs:element name="anotherGlobalComplex" type="structure"/>
</xs:schema>''' % (schema_path,)
        code = pyxb.binding.generate.GeneratePython(schema_text=xsd)

if __name__ == '__main__':
    unittest.main()
