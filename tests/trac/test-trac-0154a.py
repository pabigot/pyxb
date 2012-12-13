# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.datatypes as xs
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:complexType name="tAny">
    <xsd:sequence>
      <xsd:element type="xsd:int" name="pre"/>
      <xsd:choice>
        <xsd:element type="xsd:int" name="a"/>
        <xsd:element type="xsd:int" name="b"/>
      </xsd:choice>
      <xsd:choice>
        <xsd:element type="xsd:int" name="a"/>
        <xsd:element type="xsd:int" name="b"/>
      </xsd:choice>
      <xsd:element type="xsd:int" name="post"/>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:element name="eAny" type="tAny"/>
</xsd:schema>'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0154a (unittest.TestCase):
    def getInstance (self):
        instance = eAny()
        vc = instance._validationConfig.copy()
        instance._setValidationConfig(vc)
        instance.pre = -100
        # NB: The values need to be instances of _TypeBinding_mixin or
        # the content check will ignore them.
        instance.a.append(xs.int(1))
        instance.b.append(xs.int(2))
        instance.post = 100
        return instance

    def testWAIT (self):
        i = self.getInstance()
        vc = i._validationConfig
        vc._setContentInfluencesGeneration(vc.ALWAYS)
        vc._setInvalidElementInContent(vc.WAIT)

        i._resetContent().extend([i.a[0], i.b[0]])
        xmls = i.toxml('utf-8', root_only=True)
        self.assertEqual('<eAny><pre>-100</pre><a>1</a><b>2</b><post>100</post></eAny>', xmls)

        i._resetContent().extend([i.b[0], i.a[0]])
        xmls = i.toxml('utf-8', root_only=True)
        self.assertEqual('<eAny><pre>-100</pre><b>2</b><a>1</a><post>100</post></eAny>', xmls)


if __name__ == '__main__':
    unittest.main()
    
