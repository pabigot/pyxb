from pyxb.standard.bindings.raw.wsdl import *
import pyxb.standard.bindings.raw.wsdl as raw_wsdl

import pyxb.Namespace
import pyxb.utils.domutils as domutils

# Scan for available pre-built namespaces.  The effect of this is to
# register a bunch of namespaces including the path to the module that
# implements them.  This allows the wildcard handler in the content
# model to create proper instances rather than leave them as DOM
# nodes.
pyxb.Namespace.AvailableForLoad()

class _NamespaceAwareMap (dict):
    def namespaceData (self):
        return self.__namespaceData
    __namespaceData = None

    def __init__ (self, namespace_data, *args, **kw):
        super(_NamespaceAwareMap, self).__init__(*args, **kw)
        assert namespace_data is not None
        self.__namespaceData = namespace_data

    def __keyToPair (self, key, is_definition=False):
        if isinstance(key, tuple):
            (ns, ln) = key
        else:
            ns = None
            if 0 <= key.find(':'):
                (pfx, ln) = key.split(':', 1)
                ns = self.namespaceData().inScopeNamespaces().get(pfx, None)
                assert ns is not None
            else:
                ln = key
        if ns is None:
            if is_definition:
                ns = self.namespaceData().targetNamespace()
            else:
                ns = self.namespaceData().defaultNamespace()
        return (ns, ln)

    def __pairToSet (self, qkey):
        pass

    def __getitem__ (self, key):
        qkey = self.__keyToPair(key)
        #print 'Looking up with key %s as %s uri %s' % (key, qkey, qkey[0].uri())
        return super(_NamespaceAwareMap, self).__getitem__(qkey)

    def __setitem__ (self, key, value):
        qkey = self.__keyToPair(key, is_definition=True)
        #print 'Setting with key %s as %s uri %s' % (key, qkey, qkey[0].uri())
        return super(_NamespaceAwareMap, self).__setitem__(qkey, value)

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
    pass
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
        return self.__messageMap
    __messageMap = None

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
        return rv

    def __buildMaps (self):
        self.__messageMap = _NamespaceAwareMap(self.namespaceContext())
        for m in self.message():
            name_qname = (self.targetNamespace(), m.name())
            self.__messageMap[name_qname] = m
        self.__portTypeMap = _NamespaceAwareMap(self.namespaceContext())
        for pt in self.portType():
            port_type_qname = (self.targetNamespace(), pt.name())
            self.__portTypeMap[port_type_qname] = pt
            for op in pt.operation():
                pt.operationMap()[op.name()] = op
                for p in (op.input() + op.output() + op.fault()):
                    msg_qname = domutils.InterpretQName(m._domNode(), p.message())
                    p._setMessageReference(self.__messageMap[msg_qname])
        self.__bindingMap = _NamespaceAwareMap(self.namespaceContext())
        for b in self.binding():
            binding_qname = (self.targetNamespace(), b.name())
            self.__bindingMap[binding_qname] = b
            port_type_qname = domutils.InterpretQName(b._domNode(), b.type())
            b.setPortTypeReference(self.__portTypeMap[port_type_qname])
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
        self.__serviceMap = _NamespaceAwareMap(self.namespaceContext())
        for s in self.service():
            service_qname = (self.targetNamespace(), s.name())
            self.__serviceMap[service_qname] = s
            port_map = { }
            for p in s.port():
                port_qname = domutils.InterpretQName(p._domNode(), p.name())
                port_map[port_qname] = p
                binding_qname = domutils.InterpretQName(p._domNode(), p.binding())
                p._setBindingReference(self.__bindingMap[binding_qname])
                for wc in p.wildcardElements():
                    if isinstance(wc, _WSDL_port_mixin):
                        p._setAddressReference(wc)
                        break

    def __processSchema (self):
        global pyxb
        if self.__schema is not None:
            return self.__schema
        for t in self.types():
            for wc in t.wildcardElements():
                if isinstance(wc, Node) and pyxb.Namespace.XMLSchema.nodeIsNamed(wc, 'schema'):
                    import pyxb.xmlschema
                    self.__schema = pyxb.xmlschema.schema.CreateFromDOM(wc, namespace_context=self.namespaceContext())
                    return self.__schema

raw_wsdl.definitions._SetClassRef(definitions)
