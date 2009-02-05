"""XMLSchema bindings 

These bindings are hand-written to support the XMSchema namespace.
Maybe, if the generated code is good enough, they'll be replaced by
bindings that are generated.

"""

import structures as xsc
import datatypes as xsd
from ..Namespace import Namespace

from PyWXSB.exceptions_ import *

from xml.dom import Node
import sys
import types

NamespaceURI = 'http://www.w3.org/2001/XMLSchema'

# Hand-written classes used to get to the point where we can subclass
# generated bindings.

class schemaTop (xsc.ModelGroup):
    def __init__ (self):
        xsc.ModelGroup.__init__(self)

    def __Match (cls, wxs, node):
        rv = redefinable.Match(wxs, node)
        if rv is not None:
            return rv
        if wxs.xsQualifiedName('element') == node.nodeName:
            return wxs._processElementDeclaration(node)
        if wxs.xsQualifiedName('attribute') == node.nodeName:
            return wxs._processAttributeDeclaration(node)
        if wxs.xsQualifiedName('notation') == node.nodeName:
            print "WARNING: Ignoring notation"
            return node
        return None
    Match = classmethod(__Match)

class redefinable (xsc.ModelGroup):
    def __init__ (self):
        xsc.ModelGroup.__init__(self)

    def __Match (cls, wxs, node):
        if wxs.xsQualifiedName('simpleType') == node.nodeName:
            return wxs._processSimpleType(node)
        if wxs.xsQualifiedName('complexType') == node.nodeName:
            return wxs._processComplexType(node)
        if wxs.xsQualifiedName('group') == node.nodeName:
            return wxs._processGroup(node)
        if wxs.xsQualifiedName('attributeGroup') == node.nodeName:
            return wxs._processAttributeGroup(node)
        return None
    Match = classmethod(__Match)

class anyType:
    pass

class openAttrs (anyType):
    pass

class schema (xsc.Schema):
    """Class corresponding to a W3C XML Schema instance.

    This class is a subclass of the corresponding schema component.
    """
    
    __domRootNode = None
    __pastProlog = False

    __namespaceList = None      # List of namespace instances
    __namespacePrefixMap = None # Map from prefix to a namespace instance
    __namespaceURIMap = None    # Map from URI to a namespace instance

    __xs = None                 # http://www.w3.org/2001/XMLSchema
    __xml = None                # http://www.w3.org/XML/1998/namespace
    __defaultNamespace = None   # Default namespace for current schema
    __targetNamespace = None    # Target namespace for current schema

    def __init__ (self):
        xsc.Schema.__init__(self)
        self.__namespaceList = []
        self.__namespacePrefixMap = { }
        self.__namespaceURIMap = { }

    def initializeBuiltins (self):
        self.__xml = self.lookupOrCreateNamespace('http://www.w3.org/XML/1998/namespace', 'xml')
        self.__xs = self.lookupOrCreateNamespace('http://www.w3.org/2001/XMLSchema')
        self.__xsi = self.lookupOrCreateNamespace('http://www.w3.org/2001/XMLSchema-instance')
        void = xsc.AttributeDeclaration.CreateBaseInstance('type', self.__xsi)
        void = xsc.AttributeDeclaration.CreateBaseInstance('nil', self.__xsi)
        void = xsc.AttributeDeclaration.CreateBaseInstance('schemaLocation', self.__xsi)
        void = xsc.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self.__xsi)

        # If there's a target namespace, use this as its schema
        if self.__targetNamespace:
            self.__targetNamespace.schema(self)

        # If we're targeting the XMLSchema namespace, define the
        # built-in types.  Otherwise, allocate and associate a schema
        # instance for the XMLSchema namespace so we get access to
        # those built-in types.
        if self.__xs == self.__targetNamespace:
            xsd.DefineSimpleTypes(self)
        else:
            self.__xs.schema(SchemaForXS(self))

    def lookupType (self, type_name):
        if 0 <= type_name.find(':'):
            ( prefix, local_name ) = type_name.split(':', 1)
            return self.namespaceForPrefix(prefix).lookupType(local_name)
        # Invoke superclass lookup
        rv = self._lookupTypeDefinition(type_name)
        if rv is None:
            raise Exception('lookupType: No match for "%s" in %s' % (type_name, self.__targetNamespace))
        return rv

    def lookupSimpleType (self, type_name):
        rv = self.lookupType(type_name)
        if isinstance(rv, xsc.SimpleTypeDefinition):
            return rv
        raise Exception('lookupSimpleType: Name "%s" in %s is not a simple type' % (type_name, self.__targetNamespace))

    def lookupAttributeGroup (self, ref_name):
        if 0 <= ref_name.find(':'):
            ( prefix, local_name ) = ref_name.split(':', 1)
            return self.namespaceForPrefix(prefix).lookupAttributeGroup(local_name)
        rv = self._lookupAttributeGroupDefinition(ref_name)
        if rv is None:
            raise SchemaValidationError('lookupAttributeGroup: No match for "%s" in %s' % (ref_name, self.__targetNamespace))
        return rv

    def lookupAttributeDeclaration (self, ref_name):
        if 0 <= ref_name.find(':'):
            ( prefix, local_name ) = ref_name.split(':', 1)
            return self.namespaceForPrefix(prefix).lookupAttributeDeclaration(local_name)
        rv = self._lookupAttributeDeclaration(ref_name)
        if rv is None:
            raise SchemaValidationError('lookupAttributeDeclaration: No match for "%s" in %s' % (ref_name, self.__targetNamespace))
        return rv

    def lookupGroup (self, group_name):
        if 0 <= group_name.find(':'):
            ( prefix, local_name ) = group_name.split(':', 1)
            return self.namespaceForPrefix(prefix).lookupGroup(local_name)
        rv = self._lookupModelGroupDefinition(group_name)
        if rv is None:
            raise SchemaValidationError('lookupGroup: No match for "%s" in %s' % (group_name, self.__targetNamespace))
        return rv

    def lookupElement (self, element_name):
        if 0 <= element_name.find(':'):
            ( prefix, local_name ) = element_name.split(':', 1)
            return self.namespaceForPrefix(prefix).lookupElement(local_name)
        rv = self._lookupElementDeclaration(element_name)
        if rv is None:
            raise SchemaValidationError('lookupElement: No match for "%s" in %s' % (element_name, self.__targetNamespace))
        return rv

    def addNamespace (self, namespace):
        old_namespace = self.__namespacePrefixMap.get(namespace.prefix(), None)
        return namespace
        
    def lookupOrCreateNamespace (self, uri, prefix=None):
        try:
            namespace = self.namespaceForURI(uri)
        except Exception, e:
            namespace = Namespace(uri, prefix)
            self.__namespaceList.append(namespace)
            self.__namespaceURIMap[namespace.uri()] = namespace
        if namespace.prefix() is None:
            namespace.prefix(prefix)
        if namespace.prefix() is not None:
            self.__namespacePrefixMap[namespace.prefix()] = namespace
        return namespace

    def setDefaultNamespace (self, namespace):
        self.__defaultNamespace = namespace
        print "DEFAULT namespace %s" % (namespace,)
        return namespace

    def getDefaultNamespace (self):
        return self.__defaultNamespace

    def setTargetNamespace (self, namespace):
        self.__targetNamespace = namespace
        print "TARGET namespace %s" % (namespace,)
        return namespace

    def getTargetNamespace (self):
        return self.__targetNamespace

    def targetPrefix (self):
        if self.__targetNamespace:
            return self.__targetNamespace.prefix()
        return None

    def namespaceForURI (self, uri):
        if self.__namespaceURIMap.has_key(uri):
            return self.__namespaceURIMap.get(uri, None)
        raise Exception('Namespace "%s" not recognized' % (uri,))

    def namespaceForPrefix (self, prefix):
        if self.__namespacePrefixMap.has_key(prefix):
            return self.__namespacePrefixMap.get(prefix, None)
        raise Exception('Namespace prefix "%s" not recognized' % (prefix,))

    def processDocument (self, doc):
        """Take the root element of the document, and scan its attributes under
        the assumption it is an XMLSchema schema element.  That means
        recognize namespace declarations and process them.  Also look for
        and set the default namespace.  If we see an attribute that looks
        like a targetNamespace, save its value."""
        target_namespace = None
        default_namespace = None
        root_node = doc.documentElement
        for attr in root_node.attributes.values():
            if 'xmlns' == attr.prefix:
                self.lookupOrCreateNamespace(attr.nodeValue, attr.localName)
            elif 'xmlns' == attr.name:
                default_namespace = attr.nodeValue
            elif 'targetNamespace' == attr.name:
                target_namespace = attr.nodeValue
        if default_namespace is not None:
            # TODO: Is it required that the default namespace be recognized?
            # Does not hold for http://www.w3.org/2001/xml.xsd
            ns = self.lookupOrCreateNamespace(default_namespace)
            #ns = self.namespaceForURI(default_namespace)
            self.setDefaultNamespace(ns)
        # If we got a targetNamespace attribute, save it.
        if target_namespace is not None:
            self.setTargetNamespace(self.lookupOrCreateNamespace(target_namespace))

        # Now install all the standard types, including fleshing out
        # the xs() namespace schema.
        self.initializeBuiltins()

        # Verify that the root node is an XML schema element
        if self.xsQualifiedName('schema') != root_node.nodeName:
            raise SchemaValidationError('Root node %s of document is not an XML schema element' % (root_node.nodeName,))

        self.__domRootNode = root_node

        for cn in root_node.childNodes:
            if Node.ELEMENT_NODE == cn.nodeType:
                rv = self.processTopLevelNode(cn)
                if rv is None:
                    print 'Unrecognized: %s' % (cn.nodeName,)
            elif Node.TEXT_NODE == cn.nodeType:
                # Non-element content really should just be whitespace.
                # If something else is seen, print it for inspection.
                text = cn.data.strip()
                if text:
                    print 'Ignored text: %s' % (text,)
            elif Node.COMMENT_NODE == cn.nodeType:
                #print 'comment: %s' % (cn.data.strip(),)
                pass
            else:
                # ATTRIBUTE_NODE
                # CDATA_SECTION_NODE
                # ENTITY_NODE
                # PROCESSING_INSTRUCTION
                # DOCUMENT_NODE
                # DOCUMENT_TYPE_NODE
                # NOTATION_NODE
                print 'Ignoring non-element: %s' % (cn,)

        self._resolveDefinitions()

        return self

    def reset (self):
        self.__pastProlog = False

    def _requireInProlog (self, node_name):
        if self.__pastProlog:
            raise SchemaValidationError('Unexpected node %s after prolog' % (node_name,))

    def _processInclude (self, node):
        self._requireInProlog(node.nodeName)
        sys.stderr.write("warning: include directive not handled\n")
        return node

    def _processImport (self, node):
        self._requireInProlog(node.nodeName)
        sys.stderr.write("warning: import directive not handled\n")
        return node

    def _processRedefine (self, node):
        self._requireInProlog(node.nodeName)
        sys.stderr.write("warning: redefine directive not handled\n")
        return node

    def _processAnnotation (self, node):
        an = self._addAnnotation(xsc.Annotation.CreateFromDOM(self, node))
        return self

    def _processAttributeDeclaration (self, node):
        # NB: This is an attribute of the schema itself
        an = xsc.AttributeDeclaration.CreateFromDOM(self, node)
        self._addNamedComponent(an)
        return an

    def _processSimpleType (self, node):
        """Walk a simpleType element to create a simple type definition component.
        """
        # Node should be a topLevelSimpleType
        assert self.xsQualifiedName('simpleType') == node.nodeName
        assert self.xsQualifiedName('schema') == node.parentNode.nodeName

        rv = xsc.SimpleTypeDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processComplexType (self, node):
        """Walk a complexType element to create a complex type definition component.
        """
        # Node should be a topLevelComplexType
        assert self.xsQualifiedName('complexType') == node.nodeName
        assert self.xsQualifiedName('schema') == node.parentNode.nodeName

        rv = xsc.ComplexTypeDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processAttributeGroup (self, node):
        # Node should be a namedAttributeGroup
        assert self.xsQualifiedName('attributeGroup') == node.nodeName
        assert self.xsQualifiedName('schema') == node.parentNode.nodeName
        rv = xsc.AttributeGroupDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processGroup (self, node):
        # Node should be a namedGroup
        assert self.xsQualifiedName('group') == node.nodeName
        assert self.xsQualifiedName('schema') == node.parentNode.nodeName
        rv = xsc.ModelGroupDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processElementDeclaration (self, node):
        # Node should be a named element
        assert self.xsQualifiedName('element') == node.nodeName
        assert self.xsQualifiedName('schema') == node.parentNode.nodeName
        ed = xsc.ElementDeclaration.CreateFromDOM(self, node)
        self._addNamedComponent(ed)
        return ed

    def processTopLevelNode (self, node):
        """Process a DOM node from the top level of the schema.

        This should return a non-None value if the node was
        successfully recognized."""
        if self.xsQualifiedName('include') == node.nodeName:
            return self._processInclude(node)
        if self.xsQualifiedName('import') == node.nodeName:
            return self._processImport(node)
        if self.xsQualifiedName('redefine') == node.nodeName:
            return self._processRedefine(node)
        if self.xsQualifiedName('annotation') == node.nodeName:
            return self._processAnnotation(node)
        rv = schemaTop.Match(self, node)
        if rv is not None:
            self.__pastProlog = True
            return rv
        raise SchemaValidationError('Unexpected top-level element %s' % (node.nodeName,))

    def domRootNode (self):
        return self.__domRootNode

    def xs (self):
        return self.__xs

    def xsQualifiedName (self, local_name):
        return self.xs().qualifiedName(local_name, self.getDefaultNamespace())

    def xsAttribute (self, dom_node, attr_name):
        return self.nsAttribute(dom_node, attr_name, self.xs())

    def dnsAttribute (self, dom_node, attr_name):
        rv = None
        if self.getDefaultNamespace():
            rv = dom_node.getAttributeNodeNS(self.getDefaultNamespace(), attr_name)

    def nsAttribute (self, dom_node, attr_name, namespace):
        rv = None
        if namespace is not None:
            rv = dom_node.getAttributeNodeNS(namespace.uri(), attr_name)
            print 'Namespace %s lookup got %s' % (namespace, rv)
        return rv

def SchemaForXS (wxs):
    '''Create a Schema instance that targets the XMLSchema namespace.
    Preload all its elements.  Note that we only need to do this in
    the bootstrap code.'''
    rv = schema()
    rv.setTargetNamespace(wxs.lookupOrCreateNamespace(NamespaceURI))
    xsd.DefineSimpleTypes(rv)
    return rv
