# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.datatypes as xs
import datetime;
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="utf-8"?>
<xs:schema elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="b" type="xs:boolean"/>
  <xs:element name="nNI" type="xs:nonNegativeInteger"/>
  <xs:element name="int" type="xs:int"/>
  <xs:element name="time" type="xs:time"/>
  <xs:element name="duration" type="xs:duration"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0071 (unittest.TestCase):
    def testNonNegativeInteger (self):
        self.assertEqual(0, xs.nonNegativeInteger());
        self.assertEqual(0, CreateFromDocument(six.u('<nNI>0</nNI>')));
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, six.u('<nNI/>'));

    def testBoolean (self):
        self.assertEqual(0, xs.boolean());
        self.assertEqual(0, CreateFromDocument(six.u('<b>0</b>')));
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, six.u('<b/>'));

    def testInt (self):
        self.assertEqual(0, xs.int());
        self.assertEqual(0, CreateFromDocument(six.u('<int>0</int>')));
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, six.u('<int/>'));

    def testTime (self):
        self.assertEqual(datetime.time(), xs.time());
        self.assertEqual(datetime.time(), CreateFromDocument(six.u('<time>00:00:00</time>')));
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, six.u('<time/>'));

    def testDuration (self):
        self.assertEqual(datetime.timedelta(), xs.duration());
        self.assertEqual(datetime.timedelta(), CreateFromDocument(six.u('<duration>P0D</duration>')));
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, six.u('<duration/>'));

if __name__ == '__main__':
    unittest.main()
