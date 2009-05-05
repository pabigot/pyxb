"""XMLSchema bindings 

These bindings are hand-written to support the XMSchema namespace.
Maybe, if the generated code is good enough, they'll be replaced by
bindings that are generated.

"""

import pyxb.Namespace as Namespace
from pyxb.Namespace import XMLSchema as xs

import structures as xsc

import pyxb.binding.datatypes as xsd

from pyxb.exceptions_ import *
import traceback

import xml.dom
import sys
import types

# Hand-written classes used to get to the point where we can subclass
# generated bindings.

class schemaTop (xsc.ModelGroup):
    """Hand-written binding to the schemaTop model group of XMLSchema."""
    def __init__ (self, *args, **kw):
        super(schemaTop, self).__init__(*args, **kw)

    @classmethod
    def Match (cls, wxs, node):
        rv = redefinable.Match(wxs, node)
        if rv is not None:
            return rv
        if xs.nodeIsNamed(node, 'element'):
            return wxs._processElementDeclaration(node)
        if xs.nodeIsNamed(node, 'attribute'):
            return wxs._processAttributeDeclaration(node)
        if xs.nodeIsNamed(node, 'notation'):
            return wxs._processNotationDeclaration(node)
        return None

class redefinable (xsc.ModelGroup):
    """Hand-written binding to the redefinable model group of XMLSchema."""
    def __init__ (self, *args, **kw):
        super(redefinable, self).__init__(*args, **kw)

    @classmethod
    def Match (cls, wxs, node):
        if xs.nodeIsNamed(node, 'simpleType'):
            return wxs._processSimpleType(node)
        if xs.nodeIsNamed(node, 'complexType'):
            return wxs._processComplexType(node)
        if xs.nodeIsNamed(node, 'group'):
            return wxs._processGroup(node)
        if xs.nodeIsNamed(node, 'attributeGroup'):
            return wxs._processAttributeGroup(node)
        return None

class schema (xsc.Schema):
    """Class corresponding to a W3C XML Schema instance.

    This class is a subclass of the corresponding schema component.
    """
    
    __domRootNode = None

    # True when we have started seeing elements, attributes, or
    # notations.
    __pastProlog = False

    # A set of namespace instances referenced by this schema.
    # Namespaces cannot be removed from this set.
    __namespaces = None

    # Map from a prefix to the namespace it represents in this schema.
    # Namespaces with bound prefixes cannot be reassigned, and the
    # prefix associated with a namespace cannot change.  This is
    # prefix->Namespace, not prefix->URI.
    __prefixToNamespaceMap = None

    # Reverse direction: given a Namespace instance, determine the
    # prefix used for that namespace.  The map is from URI->prefix; we
    # use the URI rather than the Namespace instance to lessen the
    # probability of errors due to Namespace proxies.
    __namespaceURIToPrefixMap = None

    # Map from the namespace URI to the instance that represents it.
    # Note: This is not redundant with Namespace.NamespaceForURI,
    # since the latter may include namespaces not available to this
    # schema.
    __namespaceURIMap = None    # Map from URI to a namespace instance

    # Default namespace for current schema.  Will be None unless
    # schema has an 'xmlns' attribute.
    __defaultNamespace = None 

    # The prefix used for qualified names in the XMLSchema namespace,
    # or None if the default namespace is XMLSchema.
    __xsPrefix = None

    def __init__ (self):
        xsc.Schema.__init__(self)
        self.__namespaces = set()
        self.__namespaceURIToPrefixMap = { }
        self.__prefixToNamespaceMap = { }
        self.__namespaceURIMap = { }

    def initializeBuiltins (self):
        # These two are built-in; make sure they're present
        self.lookupOrCreateNamespace(Namespace.XML.uri())
        self.lookupOrCreateNamespace(Namespace.XMLSchema_instance.uri())

        # We're certainly going to need this one, too.  Presumably
        # it's already been added, with whatever prefix is required
        # for it in this schema.
        xs = self.namespaceForURI(Namespace.XMLSchema.uri())
        if xs is None:
            raise LogicError('No access to XMLSchema namespace')

        # We're going to need the built-in types from the XMLSchema
        # namespace.  @todo This will allocate and associate a schema
        # instance with the XMLSchema namespace.  If we're trying to
        # parse the XMLSchema schema, then the namespace/schema
        # association below will fail.  To support both built-in and
        # loaded schema for XMLSchema is going to get tricky, because
        # of a dependency loop on xml:lang.
        Namespace.XMLSchema.validateSchema()

        # It's perfectly legitimate to not specify a target namespace.

        # There better be a target namespace.  Use this as its schema.
        if self.targetNamespace() is not None:
            # NB: This will blow up if we're trying to parse the XMLSchema
            # itself, because we already have the built-in schema instance
            # bound to the namespace.
            assert (self.targetNamespace().schema() is None) or (Namespace.XMLSchema == self.targetNamespace())
            if self.targetNamespace().schema() is None:
                self.targetNamespace()._schema(self)

        # Try to validate anything else we might need.  Ideally,
        # they'll all exist in pre-parsed format.  We'll need them if
        # we're going to generate code.
        for ns in self.namespaces():
            if self.targetNamespace() != ns:
                try:
                    ns.validateSchema()
                except Exception, e:
                    print 'WARNING validating schema for %s: %s' % (ns.uri(), e)
                    traceback.print_exception(*sys.exc_info())

    def getNamespaceForLookup (self, type_name):
        """Resolve a QName or NCName appropriately for this schema.

        Returns a pair consisting of the namespace to be used for
        lookup, and the NCName to be used in that namespace.  The
        NCName will never be None; the namespace will be None only if
        the schema has no target namespace and no default namespace
        and the type_name is not qualified.  This will raise an
        exception if the qualifier is present but not associated with
        a namespace.
        """
        ns = None
        local_name = type_name
        if 0 <= type_name.find(':'):
            ( prefix, local_name ) = type_name.split(':', 1)
            ns = self.namespaceForPrefix(prefix)
        elif self.__defaultNamespace is not None:
            # @todo There was some reason why it was important to not
            # do this for the target namespace...
            ns = self.__defaultNamespace
        elif self.targetNamespace() is not None:
            ns = self.targetNamespace()
        return (ns, local_name)

    def lookupType (self, qualified_name):
        """Lookup a type by name.

        If the name is a QName, the prefix part is used identify a
        namespace, using the prefix map for this schema.  If the name
        is an NCName, the default namespace for this schema is used.
        If the name cannot be resolved in the appropriate namespace,
        an exception is thrown."""

        (ns, local_name) = self.getNamespaceForLookup(qualified_name)
        assert 0 > local_name.find(':')
        if ns is None:
            rv = self.targetNamespace().lookupTypeDefinition(local_name)
        else:
            rv = ns.lookupTypeDefinition(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupType: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupSimpleType (self, qualified_name):
        """Like lookupType, but restricted to SimpleTypeDefinitions."""
        rv = self.lookupType(qualified_name)
        if isinstance(rv, xsc.SimpleTypeDefinition):
            return rv
        raise NotInNamespaceError('lookupSimpleType: Name "%s" in %s is not a simple type' % (qualified_name, ns))

    def lookupAttributeGroup (self, qualified_name):
        """Like lookupType, but for attribute groups."""
        (ns, local_name) = self.getNamespaceForLookup(qualified_name)
        if ns is None:
            rv = self.targetNamespace().lookupAttributeGroupDefinition(local_name)
        else:
            rv = ns.lookupAttributeGroupDefinition(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupAttributeGroup: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupGroup (self, qualified_name):
        """Like lookupType, but for groups."""
        (ns, local_name) = self.getNamespaceForLookup(qualified_name)
        if ns is None:
            rv = self.targetNamespace().lookupModelGroupDefinition(local_name)
        else:
            rv = ns.lookupModelGroupDefinition(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupGroup: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupAttribute (self, qualified_name, context=xsc._ScopedDeclaration_mixin.SCOPE_global):
        """Like lookupType, but for attributes."""
        (ns, local_name) = self.getNamespaceForLookup(qualified_name)
        if ns is None:
            rv = self._lookupAttributeDeclaration(local_name, context)
        else:
            rv = xsc._LookupAttributeDeclaration(ns, context, local_name)
        if rv is None:
            raise NotInNamespaceError('lookupAttributeDeclaration: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupElement (self, qualified_name, context=xsc._ScopedDeclaration_mixin.SCOPE_global):
        """Like lookupType, but for elements."""
        (ns, local_name) = self.getNamespaceForLookup(qualified_name)
        if ns is None:
            rv = self._lookupElementDeclaration(local_name, context)
        else:
            rv = xsc._LookupElementDeclaration(ns, context, local_name)
        if rv is None:
            raise NotInNamespaceError('lookupElement: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupOrCreateNamespace (self, uri, prefix=None):
        """Associate a namespace with this schema, potentially
        providing a prefix by which it will be known.

        The URI must exist.  If there is no namespace corresponding to
        that URI in the namespace registry, one is created.  The
        namespace will be known by the given prefix, or a prefix
        permanently bound to the namespace by specification (if any).
        Referring to a namespace by multiple prefixes is an error,
        though it is legitimate for a namespace to both have a prefix
        and be used as the default namespace.
        """
        namespace = Namespace.NamespaceForURI(uri)
        if namespace is None:
            # No such namespace exists.  Create one.
            namespace = Namespace.Namespace(uri)
        if namespace not in self.__namespaces:
            # Add the namespace, as well as a mapping between it and
            # the prefix by which it is known in this schema, if any.
            self.__namespaces.add(namespace)
            self.__namespaceURIMap[namespace.uri()] = namespace

            if prefix is None:
                prefix = namespace.boundPrefix()
            # The default namespace will not involve a prefix.
            if prefix is not None:
                if prefix in self.__prefixToNamespaceMap:
                    raise LogicError('Prefix %s already associated with %s' % (prefix, namespace))
                old_prefix = self.__namespaceURIToPrefixMap.get(namespace.uri(), None)
                if old_prefix is not None:
                    # This is not a LogicError because I'm not convinced doing this
                    # isn't legal.  Even if it does seem a little nonsensical.
                    raise IncompleteImplementationError('Namespace %s cannot have multiple prefixes (%s, %s)' % (namespace, prefix, old_prefix))
                self.__prefixToNamespaceMap[prefix] = namespace
                self.__namespaceURIToPrefixMap[namespace.uri()] = prefix

        return namespace

    def setDefaultNamespace (self, namespace):
        """Specify the namespace that should be used for non-qualified
        lookups.  """
        #print 'DEFAULT: %s' % (namespace,)
        self.__defaultNamespace = namespace
        return namespace

    def getDefaultNamespace (self):
        return self.__defaultNamespace

    def setTargetNamespace (self, namespace):
        """Specify the namespace for which this schema provides
        information."""
        self._setTargetNamespace(namespace)
        #print 'TARGET: %s' % (namespace,)
        return namespace

    def getTargetNamespace (self):
        return self.targetNamespace()

    # Compile-time spelling check
    __QUALIFIED = 'qualified'
    # Compile-time spelling check
    __UNQUALIFIED = 'unqualified'

    def defaultNamespaceFromDOM (self, node, default_tag):
        """Determine the approprate namespace for a local
        attribute/element in the schema.

        This takes the appropriate schema-level attribute default
        value (identified by the given tag) from the schema,
        potentially overrides it from an attribute in the node, then
        returns either this schema's target namespace or None.  See
        any discussion of the targetNamespace property in the
        component specification.
        """
        # Failure to provide a valid tag for the default is a
        # programmer error.  There's only two; surely you can get that
        # many right.  Oh, hell, probably not...
        assert default_tag in [ 'attributeFormDefault', 'elementFormDefault' ]
        assert self.schemaHasAttribute(default_tag)
        form = xsc.NodeAttribute(node, 'form')
        if form is None:
            form = self.schemaAttribute(default_tag)
        assert form is not None
        if not form in [ self.__QUALIFIED, self.__UNQUALIFIED ]:
            raise SchemaValidationError('form attribute must be "%s" or "%s"' % (self.__QUALIFIED, self.__UNQUALIFIED))
        if self.__UNQUALIFIED == form:
            return self.getTargetNamespace()
        return None

    def targetPrefix (self):
        if self.targetNamespace():
            return self.targetNamespace().prefix()
        return None

    def namespaces (self):
        """Return the set of namespaces associated with this schema."""
        return self.__namespaces

    def namespaceForURI (self, uri):
        """Return the namespace for the URI.

        Throws an exception if the namespace has not been associated
        with this schema (must be done by processing an xmlns
        attribute)."""
        if self.__namespaceURIMap.has_key(uri):
            return self.__namespaceURIMap[uri]
        raise SchemaValidationError('Namespace "%s" not recognized' % (uri,))

    def namespaceForPrefix (self, prefix):
        """Return the namespace associated with the given prefix in this schema.

        The prefix must be a non-empty string associated with a
        namespace through an xmlns attribute in the schema element."""
        if self.__prefixToNamespaceMap.has_key(prefix):
            return self.__prefixToNamespaceMap.get(prefix, None)
        raise Exception('Namespace prefix "%s" not recognized' % (prefix,))

    def prefixForNamespace (self, namespace):
        """Return the prefix used in this schema for the given namespace.

        If the namespace was not assigned a prefix in this schema,
        returns None.  If the default namespace is also available by
        prefix, the prefix is returned."""
        assert isinstance(namespace, Namespace.Namespace)
        return self.__namespaceURIToPrefixMap.get(namespace.uri(), None)

    def createDOMNodeInNamespace (self, dom_document, nc_name, namespace=None):
        if namespace is None:
            namespace = self.getDefaultNamespace()
        return dom_document.createElementNS(namespace.uri(), nc_name)

    def createDOMNodeInWXS (self, dom_document, nc_name):
        return self.createDOMNodeInNamespace(dom_document, nc_name, Namespace.XMLSchema)

    # @todo put these in base class
    @classmethod
    def CreateFromDOM (cls, node, attributes=None):
        """Take the root element of the document, and scan its attributes under
        the assumption it is an XMLSchema schema element.  That means
        recognize namespace declarations and process them.  Also look for
        and set the default namespace.  All other attributes are passed up
        to the parent class for storage."""
        default_namespace = None
        root_node = node
        if xml.dom.Node.DOCUMENT_NODE == node.nodeType:
            root_node = root_node.documentElement
        namespaces = []
        if attributes is None:
            attributes = root_node.attributes
        attribute_map = { }
        for attr in attributes.values():
            if 'xmlns' == attr.prefix:
                #print 'Created namespace %s for %s' % (attr.nodeValue, attr.localName)
                namespaces.append( (attr.nodeValue, attr.localName) )
            elif 'xmlns' == attr.name:
                default_namespace = attr.nodeValue
            else:
                attribute_map[attr.name] = attr.nodeValue

        Namespace.XMLSchema.validateSchema()

        tns_uri = attribute_map.get('targetNamespace', None)
        if tns_uri is None:
            tns = Namespace.CreateEmptyNamespace()
            assert tns is not None
        else:
            tns = Namespace.NamespaceForURI(tns_uri, create_if_missing=True)
            assert tns is not None
        assert tns is not None
        schema = None
        if tns is not None:
            schema = tns.schema()
        if schema is None:
            schema = cls()
        schema._setTargetNamespace(tns)

        return schema.__processDocumentRoot(root_node, namespaces, attribute_map, default_namespace)

    def __processDocumentRoot (self, root_node, namespaces, attribute_map, default_namespace):
        for (uri, prefix) in namespaces:
            self.lookupOrCreateNamespace(uri, prefix)
        self._setAttributesFromMap(attribute_map)

        if default_namespace is not None:
            # TODO: Is it required that the default namespace be recognized?
            # Does not hold for http://www.w3.org/2001/xml.xsd
            ns = self.lookupOrCreateNamespace(default_namespace)
            self.setDefaultNamespace(ns)
        # Cache the prefix used for XMLSchema names.  If the default
        # namespace is XMLSchema, do not use a prefix
        if self.getDefaultNamespace() != Namespace.XMLSchema:
            self.__xsPrefix = self.prefixForNamespace(Namespace.XMLSchema)

        # Apply the targetNamespace attribute.  There is a default,
        # which is to have no associated namespace.
        assert self.schemaHasAttribute('targetNamespace')
        target_namespace = self.schemaAttribute('targetNamespace')
        if target_namespace is not None:
            self.setTargetNamespace(self.lookupOrCreateNamespace(target_namespace))

        # Now pre-load the namespaces that must be available.
        self.initializeBuiltins()

        # Verify that the root node is an XML schema element
        if not xs.nodeIsNamed(root_node, 'schema'):
            raise SchemaValidationError('Root node %s of document is not an XML schema element' % (root_node.nodeName,))

        self.__domRootNode = root_node

        for cn in root_node.childNodes:
            if xml.dom.Node.ELEMENT_NODE == cn.nodeType:
                rv = self.processTopLevelNode(cn)
                if rv is None:
                    print 'Unrecognized: %s' % (cn.nodeName,)
            elif xml.dom.Node.TEXT_NODE == cn.nodeType:
                # Non-element content really should just be whitespace.
                # If something else is seen, print it for inspection.
                text = cn.data.strip()
                if text:
                    print 'Ignored text: %s' % (text,)
            elif xml.dom.Node.COMMENT_NODE == cn.nodeType:
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
        """Throw a SchemaValidationException referencing the given
        node if we have passed the sequence point representing the end
        of prolog elements."""
        if self.__pastProlog:
            raise SchemaValidationError('Unexpected node %s after prolog' % (node_name,))

    def _processInclude (self, node):
        self._requireInProlog(node.nodeName)
        # See section 4.2.1 of Structures.
        raise IncompleteImplementationException('include directive not implemented')

    def _processImport (self, node):
        """Process an import directive.

        This attempts to locate schema (named entity) information for
        a namespace that is referenced by this schema.
        """

        self._requireInProlog(node.nodeName)
        uri = xsc.NodeAttribute(node, 'namespace')
        if uri is None:
            raise SchemaValidationError('import directive must provide namespace')
        namespace = self.namespaceForURI(uri)
        # @todo 
        namespace.validateSchema()
        if namespace.schema() is None:
            # Just in case somebody imports a namespace but doesn't
            # actually use it, let this go.  If they do try to use it,
            # we'll get a NotInNamespace exception then.
            sys.stderr.write("Warning: No available schema for imported %s, forging ahead\n" % (uri,))
        return node

    def _processRedefine (self, node):
        self._requireInProlog(node.nodeName)
        raise IncompleteImplementationException('redefine not implemented')

    def _processAnnotation (self, node):
        an = self._addAnnotation(xsc.Annotation.CreateFromDOM(self, node))
        return self

    def _processAttributeDeclaration (self, node):
        # NB: This is an attribute of the schema itself.
        an = xsc.AttributeDeclaration.CreateFromDOM(self, node, xsc._ScopedDeclaration_mixin.SCOPE_global)
        return self._addNamedComponent(an)

    def _processSimpleType (self, node):
        """Walk a simpleType element to create a simple type definition component.
        """
        # Node should be a topLevelSimpleType
        assert xs.nodeIsNamed(node, 'simpleType')
        assert xs.nodeIsNamed(node.parentNode, 'schema')

        rv = xsc.SimpleTypeDefinition.CreateFromDOM(self, node)
        return self._addNamedComponent(rv)

    def _processComplexType (self, node):
        """Walk a complexType element to create a complex type definition component.
        """
        # Node should be a topLevelComplexType
        assert xs.nodeIsNamed(node, 'complexType')
        assert xs.nodeIsNamed(node.parentNode, 'schema')

        rv = xsc.ComplexTypeDefinition.CreateFromDOM(self, node)
        return self._addNamedComponent(rv)

    def _processAttributeGroup (self, node):
        # Node should be a namedAttributeGroup
        assert xs.nodeIsNamed(node, 'attributeGroup')
        assert xs.nodeIsNamed(node.parentNode, 'schema')
        rv = xsc.AttributeGroupDefinition.CreateFromDOM(self, node)
        return self._addNamedComponent(rv)

    def _processGroup (self, node):
        # Node should be a namedGroup
        assert xs.nodeIsNamed(node, 'group')
        assert xs.nodeIsNamed(node.parentNode, 'schema')
        rv = xsc.ModelGroupDefinition.CreateFromDOM(self, node)
        return self._addNamedComponent(rv)

    # @todo make process* private
    def _processElementDeclaration (self, node):
        # Node should be a named element
        assert xs.nodeIsNamed(node, 'element')
        assert xs.nodeIsNamed(node.parentNode, 'schema')
        ed = xsc.ElementDeclaration.CreateFromDOM(self, node, xsc._ScopedDeclaration_mixin.SCOPE_global)
        return self._addNamedComponent(ed)

    def _processNotationDeclaration (self, node):
        # Node should be a named notation
        assert xs.nodeIsNamed(node, 'notation')
        assert xs.nodeIsNamed(node.parentNode, 'schema')
        nd = xsc.NotationDeclaration.CreateFromDOM(self, node)
        return self._addNamedComponent(nd)

    def processTopLevelNode (self, node):
        """Process a DOM node from the top level of the schema.

        This should return a non-None value if the node was
        successfully recognized."""
        if xs.nodeIsNamed(node, 'include'):
            return self._processInclude(node)
        if xs.nodeIsNamed(node,  'import'):
            return self._processImport(node)
        if xs.nodeIsNamed(node, 'redefine'):
            return self._processRedefine(node)
        if xs.nodeIsNamed(node, 'annotation'):
            return self._processAnnotation(node)
        rv = schemaTop.Match(self, node)
        if rv is not None:
            self.__pastProlog = True
            return rv
        raise SchemaValidationError('Unexpected top-level element %s' % (node.nodeName,))

    def domRootNode (self):
        return self.__domRootNode
