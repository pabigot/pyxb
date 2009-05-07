import pyxb.Namespace
import pyxb.xmlschema as xs
import sys
import urllib2

WSDL_uri = 'http://ws.cdyne.com/WeatherWS/Weather.asmx?wsdl'

import pyxb.standard.bindings.wsdl as wsdl
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate
import pyxb.utils.domutils as domutils

wsdl_xml = urllib2.urlopen(WSDL_uri).read()

doc = minidom.parseString(wsdl_xml)
root = doc.documentElement

attribute_map = domutils.AttributeMap(root)

try:
    spec = wsdl.definitions.CreateFromDOM(doc.documentElement, process_schema=True)
except Exception, e:
    print 'ERROR building schema: %s' % (e,)
    sys.exit(1)

open('raw_weather.py', 'w').write(pyxb.binding.generate.GeneratePython(schema=spec.schema()))
