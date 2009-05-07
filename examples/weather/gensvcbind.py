import pyxb.Namespace
import pyxb.xmlschema as xs
import sys

import pyxb.standard.bindings.wsdl as wsdl
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate
import pyxb.utils.domutils as domutils

doc = minidom.parse('weather.wsdl')
root = doc.documentElement

attribute_map = domutils.AttributeMap(root)

try:
    spec = wsdl.definitions.CreateFromDOM(doc.documentElement, process_schema=True)
except Exception, e:
    print 'ERROR building schema: %s' % (e,)
    sys.exit(1)

open('raw_weather.py', 'w').write(pyxb.binding.generate.GeneratePython(schema=spec.schema()))
