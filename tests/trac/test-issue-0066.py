# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
<xs:schema targetNamespace="urn:issue-0066" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="elt" type="xs:int"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIssue0066 (unittest.TestCase):
    def test (self):
        instance = elt(4);
        xmlt = '<ns1:elt xmlns:ns1="urn:issue-0066">4</ns1:elt>';
        xmld = xmlt.encode('utf-8');
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld);
        self.assertRaises(UsageError, Namespace.setPrefix, '');

if __name__ == '__main__':
    unittest.main()
