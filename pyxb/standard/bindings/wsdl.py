from pyxb.standard.bindings.raw.wsdl import *
import pyxb.standard.bindings.raw.wsdl as raw_wsdl

import DWML
import pyxb.Namespace
import pyxb.utils.domutils as domutils

# Scan for available pre-built namespaces.  The effect of this is to
# register a bunch of namespaces including the path to the module that
# implements them.  This allows the wildcard handler in the content
# model to create proper instances rather than leave them as DOM
# nodes.
pyxb.Namespace.AvailableForLoad()

class _WSDL_binding_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL binding elements."""
    pass

class _WSDL_port_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL port elements."""
    pass

class _WSDL_operation_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL (binding) operation elements."""
    pass

class tPort (raw_wsdl.tPort):
    def bindingReference (self):
        return self.__bindingReference
    def _setBindingReference (self, binding_reference):
        self.__bindingReference = binding_reference
    __bindingReference = None

    def addressReference (self):
        return self.__addressReference
    def _setAddressReference (self, address_reference):
        self.__addressReference = address_reference
    __addressReference = None
raw_wsdl.tPort._SetClassRef(tPort)

class tBinding (raw_wsdl.tBinding):
    def portTypeReference (self):
        return self.__portTypeReference
    def setPortTypeReference (self, port_type_reference):
        self.__portTypeReference = port_type_reference
    __portTypeReference = None

    def protocolBinding (self):
        """Return the protocol-specific binding information."""
        return self.__protocolBinding
    def _setProtocolBinding (self, protocol_binding):
        self.__protocolBinding = protocol_binding
    __protocolBinding = None

    def operationMap (self):
        return self.__operationMap
    __operationMap = None

    def __init__ (self, *args, **kw):
        super(tBinding, self).__init__(*args, **kw)
        self.__operationMap = { }
raw_wsdl.tBinding._SetClassRef(tBinding)

class tPortType (raw_wsdl.tPortType):
    def operationMap (self):
        return self.__operationMap
    __operationMap = None

    def __init__ (self, *args, **kw):
        super(tPortType, self).__init__(*args, **kw)
        self.__operationMap = { }
raw_wsdl.tPortType._SetClassRef(tPortType)

class tParam (raw_wsdl.tParam):
    def messageReference (self):
        return self.__messageReference
    def _setMessageReference (self, message_reference):
        self.__messageReference = message_reference
    __messageReference = None
raw_wsdl.tParam._SetClassRef(tParam)

class tPart (raw_wsdl.tPart):
    def elementReference (self):
        return self.__elementReference
    def _setElementReference (self, element_reference):
        self.__elementReference = element_reference
    __elementReference = None

    def typeReference (self):
        return self.__typeReference
    def _setTypeReference (self, type_reference):
        self.__typeReference = type_reference
    __typeReference = None

raw_wsdl.tPart._SetClassRef(tPart)

class tBindingOperation (raw_wsdl.tBindingOperation):
    def operationReference (self):
        return self.__operationReference
    def _setOperationReference (self, operation_reference):
        self.__operationReference = operation_reference
    __operationReference = None
raw_wsdl.tBindingOperation._SetClassRef(tBindingOperation)

class definitions (raw_wsdl.definitions):
    def messageMap (self):
        return self.targetNamespace().messages()

    def namespaceContext (self):
        return self.__namespaceContext
    __namespaceContext = None

    def bindingMap (self):
        return self.__bindingMap
    __bindingMap = None

    def targetNamespace (self):
        return self.namespaceContext().targetNamespace()

    def namespace (self):
        return self.__namespace
    __namespace = None

    def _addToMap (self, map, qname, value):
        map[qname] = value
        (ns, ln) = qname
        if (ns == self.targetNamespace()):
            map[(None, ln)] = value
        elif (ns is None):
            map[(self.targetNamespace(), ln)] = value
        return map

    def schema (self):
        return self.__schema
    __schema = None

    @classmethod
    def CreateFromDOM (cls, node, *args, **kw):
        # Get the target namespace and other relevant information, and set the
        # per-node in scope namespaces so we can do QName resolution.
        process_schema = kw.pop('process_schema', False)
        rv = super(definitions, cls).CreateFromDOM(node, *args, **kw)
        rv.__namespaceContext = domutils.NamespaceContext(node)
        rv.__buildMaps()
        if process_schema:
            rv.__processSchema()
        rv.__finalizeReferences()
        return rv

    __WSDLCategories = ( 'service', 'port', 'message', 'binding', 'portType' )
    def __buildMaps (self):
        tns = self.namespaceContext().targetNamespace()
        tns.configureCategories(self.__WSDLCategories)
        for m in self.message():
            tns.messages()[m.name()] = m
            print 'message %s in %s' % (m.name(), tns.uri())
        for pt in self.portType():
            tns.portTypes()[pt.name()] = pt
            for op in pt.operation():
                pt.operationMap()[op.name()] = op
                for p in (op.input() + op.output() + op.fault()):
                    (msg_ns, msg_ln) = domutils.InterpretQName(m._domNode(), p.message())
                    p._setMessageReference(msg_ns.messages()[msg_ln])
        for b in self.binding():
            tns.bindings()[b.name()] = b
            port_type_qname = domutils.InterpretQName(b._domNode(), b.type())
            assert port_type_qname is not None
            (port_type_ns, port_type_ln) = port_type_qname
            b.setPortTypeReference(port_type_ns.portTypes()[port_type_ln])
            for wc in b.wildcardElements():
                if isinstance(wc, _WSDL_binding_mixin):
                    b._setProtocolBinding(wc)
                    break
            for op in b.operation():
                b.operationMap()[op.name()] = op
                for wc in op.wildcardElements():
                    if isinstance(wc, _WSDL_operation_mixin):
                        op._setOperationReference(wc)
                        break
        for s in self.service():
            tns.services()[s.name()] = s
            for p in s.port():
                port_qname = domutils.InterpretQName(p._domNode(), p.name())
                assert port_qname is not None
                (port_ns, port_ln) = port_qname
                binding_qname = domutils.InterpretQName(p._domNode(), p.binding())
                assert binding_qname is not None
                (binding_ns, binding_ln) = binding_qname
                p._setBindingReference(binding_ns.bindings()[binding_ln])
                for wc in p.wildcardElements():
                    if isinstance(wc, _WSDL_port_mixin):
                        p._setAddressReference(wc)
                        break

    def __processSchema (self):
        global pyxb
        import pyxb.xmlschema

        if self.__schema is not None:
            print 'Already have schema'
            return self.__schema
        for t in self.types():
            for wc in t.wildcardElements():
                if isinstance(wc, Node) and pyxb.Namespace.XMLSchema.nodeIsNamed(wc, 'schema'):
                    self.__schema = pyxb.xmlschema.schema.CreateFromDOM(wc, namespace_context=self.namespaceContext())
                elif isinstance(wc, pyxb.xmlschema.schema):
                    self.__schema = wc
                else:
                    print 'No match: %s %s' % (wc.namespaceURI, namepsace.localName)
                if self.__schema is not None:
                    return self.__schema
        return None

    def __finalizeReferences (self):
        tns = self.namespaceContext().targetNamespace()
        for m in tns.messages().values():
            for p in m.part():
                if (p.element() is not None) and (p.elementReference() is None):
                    elt_qname = p._namespaceContext().interpretQName(p.element())
                    assert elt_qname is not None
                    (elt_ns, elt_ln) = elt_qname
                    p._setElementReference(elt_ns.elements()[elt_ln])
                if (p.type() is not None) and (p.typeReference() is None):
                    type_qname = p._namespaceContext().interpretQName(p.type())
                    assert type_qname is not None
                    (type_ns, type_ln) = type_qname
                    type_ns.validateSchema()
                    p._setTypeReference(type_ns.typeDefinitions()[type_ln])

raw_wsdl.definitions._SetClassRef(definitions)
