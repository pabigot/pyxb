# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="f13p8">
    <xs:restriction base="xs:decimal">
      <xs:totalDigits value="13"/>
      <xs:fractionDigits value="8"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="fv" type="f13p8"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0091 (unittest.TestCase):
    def assertAlmostEqual (self, v1, v2, *args, **kw):
        from decimal import Decimal
        if (isinstance(v1, Decimal)
            or isinstance(v2, Decimal)):
            if not isinstance(v1, Decimal):
                v1 = Decimal(str(v1))
            if not isinstance(v2, Decimal):
                v2 = Decimal(str(v2))
        return super(TestTrac_0091, self).assertAlmostEqual(v1, v2, *args, **kw)

    def testBasic (self):
        if sys.version_info[:2] >= (2, 7):
            # Prior to 2.7 float/Decimal comparisons returned invalid results.
            self.assertEqual(1.0, fv(1.0))
            self.assertEqual(1.0, fv('1.0'))
            self.assertEqual(1234567890123.0, fv('1234567890123'))
            self.assertEqual(1234567890123.0, CreateFromDocument('<fv>1234567890123</fv>'))
        self.assertRaises(SimpleFacetValueError, fv, '12345678901234')
        self.assertAlmostEqual(1.00000001, fv('1.00000001'))
        self.assertRaises(SimpleFacetValueError, fv, '1.000000001')

    def testBadCase (self):
        # Prior to fix, this raised a facet violation due to rounding
        self.assertAlmostEqual(0.00790287, fv('0.00790287'))

if __name__ == '__main__':
    unittest.main()
