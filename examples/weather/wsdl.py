import pyxb.Namespace
import pyxb.xmlschema as xs
import sys

print pyxb.Namespace.AvailableForLoad()
import pyxb.standard.bindings.wsdl as wsdl
import pyxb.standard.bindings.soaphttp as soaphttp
import pyxb.utils.domutils as domutils
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate

class tPort (wsdl.tPort):
    def bindingReference (self):
        return self.__bindingReference
    def setBindingReference (self, binding_reference):
        self.__bindingReference = binding_reference
    __bindingReference = None
wsdl.tPort._SetClassRef(tPort)

class tBinding (wsdl.tBinding):
    def portTypeReference (self):
        return self.__portTypeReference
    def setPortTypeReference (self, port_type_reference):
        self.__portTypeReference = port_type_reference
    __portTypeReference = None
wsdl.tBinding._SetClassRef(tBinding)

class definitions (wsdl.definitions):
    __messageMap = None

    def namespaceData (self):
        return self.__namespaceData
    __namespaceData = None

    def targetNamespace (self):
        return self.namespaceData().targetNamespace()

    def _addToMap (self, map, qname, value):
        map[qname] = value
        (ns, ln) = qname
        if (ns == self.targetNamespace()):
            map[(None, ln)] = value
        elif (ns is None):
            map[(self.targetNamespace(), ln)] = value
        return map

    @classmethod
    def CreateFromDOM (cls, node, *args, **kw):
        # Get the target namespace and other relevant information, and set the
        # per-node in scope namespaces so we can do QName resolution.
        ns_data = domutils.NamespaceDataFromNode(node)
        rv = super(definitions, cls).CreateFromDOM(node, *args, **kw)
        rv.__namespaceData = ns_data
        rv.__buildMaps()
        return rv

    def __buildMaps (self):
        self.__messageMap = { }
        for m in self.message():
            name_qname = domutils.InterpretQName(m._domNode(), m.name())
            self._addToMap(self.__messageMap, name_qname, m)
            print 'Message: %s' % (name_qname,)
        self.__portTypeMap = { }
        for pt in self.portType():
            port_type_qname = domutils.InterpretQName(pt._domNode(), pt.name())
            self._addToMap(self.__portTypeMap, port_type_qname, pt)
            print 'Port type: %s' % (port_type_qname,)
        self.__bindingMap = { }
        for b in self.binding():
            binding_qname = domutils.InterpretQName(b._domNode(), b.name())
            self._addToMap(self.__bindingMap, binding_qname, b)
            print 'Binding: %s' % (binding_qname,)
            port_type_qname = domutils.InterpretQName(b._domNode(), b.type())
            b.setPortTypeReference(self.__portTypeMap[port_type_qname])
        self.__serviceMap = { }
        for s in self.service():
            service_qname = domutils.InterpretQName(s._domNode(), s.name())
            self._addToMap(self.__serviceMap, service_qname, s)
            port_map = { }
            for p in s.port():
                port_qname = domutils.InterpretQName(p._domNode(), p.name())
                port_map[port_qname] = p
                print 'Service %s port: %s' % (service_qname, port_qname)
                binding_qname = domutils.InterpretQName(p._domNode(), p.binding())
                p.setBindingReference(self.__bindingMap[binding_qname])

    def findPort (self, module):
        for s in self.service():
            for p in s.port():
                for wc in p.wildcardElements():
                    if isinstance(wc, pyxb.binding.basis.element):
                        if wc._Namespace == module.Namespace:
                            return (s, p, wc)
                    else:
                        if wc.namespaceURI == module.Namespace.uri():
                            # This shouldn't happen: if we have the module,
                            # its namespace should have the module registered,
                            # in which case when we created the wsdl document
                            # we'd have been able to create a Python instance
                            # for the wildcard rather than leave it as a DOM
                            # instance.
                            return (s, p, module.CreateFromDOM(wc))
        return None

    def findPortType (self, port):
        for pt in self.portType():
            if pt.name() == port.name():
                return pt
        return None

wsdl.definitions._SetClassRef(definitions)

doc = minidom.parse('weather.wsdl')
root = doc.documentElement

#for ai in range(0, root.attributes.length):
#    attr = root.attributes.item(ai)
#    print '%s = %s [%s]' % (attr.name, attr.value, attr.namespaceURI)

spec = definitions.CreateFromDOM(doc.documentElement)

def GenSchema (spec):
    for t in spec.types():
        for t2 in t.wildcardElements():
            if isinstance(t2, Node):
                print t2.namespaceURI
                ns = pyxb.Namespace.NamespaceForURI(t2.namespaceURI)
                type_spec = xs.schema().CreateFromDOM(t2, root.attributes)
                print type_spec
                print pyxb.binding.generate.GeneratePython(schema=type_spec)
                print "'''%s'''" % (t2.toxml(),)

binding = None
for b in spec.binding():
    for wc in b.wildcardElements():
        if isinstance(wc, soaphttp.binding):
            if 'GET' == wc.verb():
                binding = b
                print 'HTTP GET binding name %s type %s' % (binding.name(), binding.type())
                break

if binding is None:
    print 'ERROR: No HTTP GET binding found'
    sys.exit(1)

for op in binding.portTypeReference().operation():
    print '  %s: %s' % (op.name(), op.documentation())

    
# print "\n".join( [ _m.toDOM().toxml() for _m in spec.message() ])
