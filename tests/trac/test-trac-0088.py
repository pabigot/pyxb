# -*- coding: utf-8 -*-

import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd=u'''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:simpleType name="tEnum">
                <xs:restriction base="xs:token">
                        <xs:enumeration value="%s"/> > <!-- u'\xb0' -->
                        <xs:enumeration value="m%s"/>
                        <xs:enumeration value="m%s"/>
                </xs:restriction>
        </xs:simpleType>
</xs:schema>
''' % (u'\xb0', u'\xb2', u'\xb3')

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0088 (unittest.TestCase):
    def test (self):
        enums = tEnum._CF_enumeration.items()
        self.assertEqual(3, len(enums))
        self.assertEqual(enums[0].tag(), 'emptyString')
        self.assertEqual(enums[0].value(), u'\xb0')
        self.assertEqual(enums[1].tag(), 'm')
        self.assertEqual(enums[1].value(), u'm\xb2')
        self.assertEqual(enums[2].tag(), 'm_')
        self.assertEqual(enums[2].value(), u'm\xb3')

if __name__ == '__main__':
    unittest.main()
