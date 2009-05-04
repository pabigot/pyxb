import pyxb.Namespace
import pyxb.xmlschema as xs

import pyxb.standard.bindings.wsdl as wsdl
import pyxb.standard.bindings.soaphttp as soaphttp
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate

doc = minidom.parse('weather.wsdl')
root = doc.documentElement

#for ai in range(0, root.attributes.length):
#    attr = root.attributes.item(ai)
#    print '%s = %s [%s]' % (attr.name, attr.value, attr.namespaceURI)

spec = wsdl.definitions.CreateFromDOM(doc.documentElement)

print pyxb.Namespace.AvailableForLoad()

for t in spec.types():
    for t2 in t.wildcardElements():
        if isinstance(t2, Node):
            print t2.namespaceURI
            ns = pyxb.Namespace.NamespaceForURI(t2.namespaceURI)
            type_spec = xs.schema().CreateFromDOM(t2, root.attributes)
            print type_spec
            open('weather.py', 'w').write(pyxb.binding.generate.GeneratePython(schema=type_spec))
            sys.exit(0)
