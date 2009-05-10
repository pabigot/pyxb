import pyxb.Namespace
import pyxb.xmlschema as xs
import traceback
import sys
import urllib2

# You'll also need the DWML types
# PYTHONPATH=../.. ../../scripts/genbind DWML_ns.xsd raw DWML

WSDL_uri = 'http://www.weather.gov/forecasts/xml/DWMLgen/wsdl/ndfdXML.wsdl'
#wsdl_src = urllib2.urlopen(WSDL_uri)
wsdl_src = open('ndfdXML.wsdl')

import pyxb.standard.bindings.wsdl as wsdl
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate
import pyxb.utils.domutils as domutils

#import DWML
#print "Validating DWML %s\n%s" % (DWML.Namespace.uri(), object.__str__(DWML.Namespace),)
#DWML.Namespace.validateSchema()
#print 'Validated DWML: types %s' % ("\n".join(DWML.Namespace.typeDefinitions().keys()),)

wsdl_xml = wsdl_src.read()

doc = minidom.parseString(wsdl_xml)
root = doc.documentElement

attribute_map = domutils.AttributeMap(root)

try:
    spec = wsdl.definitions.CreateFromDOM(doc.documentElement, process_schema=True)
    open('raw/ndfd.py', 'w').write(pyxb.binding.generate.GeneratePython(schema=spec.schema()))
except Exception, e:
    print 'ERROR building schema: %s' % (e,)
    traceback.print_exception(*sys.exc_info())

