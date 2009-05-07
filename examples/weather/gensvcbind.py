import pyxb.Namespace
import pyxb.xmlschema as xs
import sys

import pyxb.standard.bindings.wsdl as wsdl
import pyxb.standard.bindings.soaphttp as soaphttp
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate
import pyxb.utils.domutils as domutils

doc = minidom.parse('weather.wsdl')
root = doc.documentElement

attribute_map = domutils.AttributeMap(root)

spec = wsdl.definitions.CreateFromDOM(doc.documentElement)

print pyxb.Namespace.AvailableForLoad()

for t in spec.types():
    for t2 in t.wildcardElements():
        if isinstance(t2, Node):
            print t2.namespaceURI
            attribute_map.update(domutils.AttributeMap(t2))
            ns = pyxb.Namespace.NamespaceForURI(t2.namespaceURI)
            type_spec = xs.schema.CreateFromDOM(t2, attribute_map)
            print type_spec
            open('weather.py', 'w').write(pyxb.binding.generate.GeneratePython(schema=type_spec))
            sys.exit(0)
