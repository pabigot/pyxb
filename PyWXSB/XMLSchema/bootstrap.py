"""XMLSchema bindings 

These bindings are hand-written to support the XMSchema namespace.
Maybe, if the generated code is good enough, they'll be replaced by
bindings that are generated.

"""

import PyWXSB.Namespace as Namespace

import structures as xsc

import datatypes as xsd

from PyWXSB.exceptions_ import *

from xml.dom import Node
import sys
import types

# Hand-written classes used to get to the point where we can subclass
# generated bindings.

class schemaTop (xsc.ModelGroup):
    def __init__ (self, *args, **kw):
        super(schemaTop, self).__init__(*args, **kw)

    @classmethod
    def Match (cls, wxs, node):
        rv = redefinable.Match(wxs, node)
        if rv is not None:
            return rv
        if node.nodeName in wxs.xsQualifiedNames('element'):
            return wxs._processElementDeclaration(node)
        if node.nodeName in wxs.xsQualifiedNames('attribute'):
            return wxs._processAttributeDeclaration(node)
        if node.nodeName in wxs.xsQualifiedNames('notation'):
            print "WARNING: Ignoring notation"
            return node
        return None

class redefinable (xsc.ModelGroup):
    def __init__ (self, *args, **kw):
        super(redefinable, self).__init__(*args, **kw)

    @classmethod
    def Match (cls, wxs, node):
        if node.nodeName in wxs.xsQualifiedNames('simpleType'):
            return wxs._processSimpleType(node)
        if node.nodeName in wxs.xsQualifiedNames('complexType'):
            return wxs._processComplexType(node)
        if node.nodeName in wxs.xsQualifiedNames('group'):
            return wxs._processGroup(node)
        if node.nodeName in wxs.xsQualifiedNames('attributeGroup'):
            return wxs._processAttributeGroup(node)
        return None

class schema (xsc.Schema):
    """Class corresponding to a W3C XML Schema instance.

    This class is a subclass of the corresponding schema component.
    """
    
    __domRootNode = None
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
    # prefix used for that namespace.
    __namespaceToPrefixMap = None

    # Map from the namespace URI to the instance that represents it.
    # Note: This is not redundant with Namespace.NamespaceForURI,
    # since the latter may include namespaces not available to this
    # schema.
    __namespaceURIMap = None    # Map from URI to a namespace instance

    # Default namespace for current schema.  Will be None unless
    # schema has an 'xmlns' attribute.
    __defaultNamespace = None 

    # Target namespace for current schema.  Will be None unless schema
    # has a 'targetNamespace' attribute.
    __targetNamespace = None

    # The prefix used for qualified names in the XMLSchema namespace,
    # or None if the default namespace is XMLSchema.
    __xsPrefix = None

    def __init__ (self):
        xsc.Schema.__init__(self)
        self.__namespaces = set()
        self.__namespaceToPrefixMap = { }
        self.__prefixToNamespaceMap = { }
        self.__namespaceURIMap = { }

    def initializeBuiltins (self):
        # If there's a target namespace, use this as its schema
        if self.__targetNamespace:
            if self.__targetNamespace.schema():
                raise LogicError('Cannot change schema assocation with target namespace %s' % (self.__targetNamespace,))
            self.__targetNamespace.schema(self)

        # These two are built-in; make sure they're present
        self.lookupOrCreateNamespace(Namespace.XML.uri())
        self.lookupOrCreateNamespace(Namespace.XMLSchema_instance.uri())

        # We're certainly going to need this one, too.  Presumably
        # it's already been added, with whatever prefix is required
        # for it in this schema.
        xs = self.namespaceForURI(Namespace.XMLSchema.uri())
        if xs is None:
            raise LogicError('No access to XMLSchema namespace')

        # If we're targeting the XMLSchema namespace, define the
        # built-in types.  Otherwise, allocate and associate a schema
        # instance for the XMLSchema namespace so we get access to
        # those built-in types.
        if self.__xs == self.__targetNamespace:
            xsd.DefineSimpleTypes(self)
        else:
            self.__xs.schema(SchemaForXS(self))

    def __getNamespaceForLookup (self, type_name):
        """Resolve a QName or NCName appropriately for this schema.

        Returns a pair consisting of the namespace to be used for
        lookup, and the NCName to be used in that namespace.  Neither
        comopnent may be None.  This method will raise an exception if
        the appropriate namespace cannot be identified.
        """
        ns = None
        local_name = type_name
        if 0 <= type_name.find(':'):
            ( prefix, local_name ) = type_name.split(':', 1)
            ns = self.namespaceForPrefix(prefix)
        elif (self.__defaultNamespace is not None) and (self.__defaultNamespace != self.__targetNamespace):
            ns = self.__defaultNamespace
        if ns is None:
            # Not sure but that this isn't actually allowable.  If so,
            # do we use the target namespace?
            raise SchemaValidationError('Unable to identify a namespace for %s' % (type_name,))
        return (ns, local_name)

    def lookupType (self, qualified_name):
        """Lookup a type by name.

        If the name is a QName, the prefix part is used identify a
        namespace, using the prefix map for this schema.  If the name
        is an NCName, the default namespace for this schema is used.
        If the name cannot be resolved in the appropriate namespace,
        an exception is thrown."""

        (ns, local_name) = self.__getNamespaceForLookup(qualified_name)
        assert 0 > local_name.find(':')
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
        (ns, local_name) = self.__getNamespaceForLookup(qualified_name)
        rv = ns.lookupAttributeGroupDefinition(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupAttributeGroup: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupGroup (self, qualified_name):
        """Like lookupType, but for groups."""
        (ns, local_name) = self.__getNamespaceForLookup(qualified_name)
        rv = ns.lookupModelGroupDefinition(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupGroup: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupAttribute (self, qualified_name):
        """Like lookupType, but for attributes."""
        (ns, local_name) = self.__getNamespaceForLookup(qualified_name)
        rv = ns.lookupAttributeDeclaration(local_name)
        if rv is None:
            raise NotInNamespaceError('lookupAttributeDeclaration: No match for "%s" in %s' % (qualified_name, ns))
        return rv

    def lookupElement (self, qualified_name):
        """Like lookupType, but for elements."""
        (ns, local_name) = self.__getNamespaceForLookup(qualified_name)
        rv = ns.lookupElementDeclaration(local_name)
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
                old_prefix = self.__namespaceToPrefixMap.get(namespace, None)
                if old_prefix is not None:
                    # This is not a LogicError because I'm not convinced doing this
                    # isn't legal.  Even if it does seem a little nonsensical.
                    raise IncompleteImplementationError('Namespace %s cannot have multiple prefixes (%s, %s)' % (namespace, prefix, old_prefix))
                self.__prefixToNamespaceMap[prefix] = namespace
                self.__namespaceToPrefixMap[namespace] = prefix

        return namespace

    def setDefaultNamespace (self, namespace):
        """Specify the namespace that should be used for non-qualified
        lookups.  """
        print 'DEFAULT: %s' % (namespace,)
        self.__defaultNamespace = namespace
        return namespace

    def getDefaultNamespace (self):
        return self.__defaultNamespace

    def setTargetNamespace (self, namespace):
        """Specify the namespace for which this schema provides
        information."""
        print 'TARGET: %s' % (namespace,)
        self.__targetNamespace = namespace
        return namespace

    def getTargetNamespace (self):
        return self.__targetNamespace

    def targetNamespaceFromDOM (self, node, default_tag):
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
        assert self.hasAttribute(default_tag)
        form = self.getAttribute(default_tag)
        assert form is not None
        if node.hasAttribute('form'):
            form = node.getAttribute('form')
        if not form in [ 'qualified', 'unqualified' ]:
            raise SchemaValidationError('form attribute must be "qualified" or "unqualified"')
        if 'qualifled' == form:
            return self.getTargetNamespace()
        return None

    def targetPrefix (self):
        if self.__targetNamespace:
            return self.__targetNamespace.prefix()
        return None

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
        return self.__namespaceToPrefixMap.get(namespace, None)

    def xsQualifiedNames (self, nc_name):
        """Returns a tuple containing all valid names for this schema
        that refer to the named component in the XMLSchema namespace.
        If XMLSchema is the default namespace and has an associated
        prefix, both the NCName and QName versions are included;
        otherwise if XMLSchema is the default namespace the NCName
        variant is included; otherwise an exception is thrown.
        """
        if self.__xsPrefix:
            qname = '%s:%s' % (self.__xsPrefix, nc_name)
            if self.__defaultNamespace == Namespace.XMLSchema:
                return (qname, nc_name)
            return (qname,)
        if self.__defaultNamespace == Namespace.XMLSchema:
            return (nc_name,)
        print self.__defaultNamespace
        raise SchemaValidationError('No prefix available to qualify %s in XMLSchema namespace' % (nc_name,))

    def xsQualifiedName (self, nc_name):
        """Given a NCName in the XMLSchema namespace, return a name
        (QName or NCName) that identifies the component within this
        schema."""
        return self.xsQualifiedNames(nc_name)[0]

    # @todo put these in base class
    def processDocument (self, doc):
        """Take the root element of the document, and scan its attributes under
        the assumption it is an XMLSchema schema element.  That means
        recognize namespace declarations and process them.  Also look for
        and set the default namespace.  All other attributes are passed up
        to the parent class for storage."""
        default_namespace = None
        root_node = doc.documentElement
        for attr in root_node.attributes.values():
            if 'xmlns' == attr.prefix:
                print 'Created namespace %s for %s' % (attr.nodeValue, attr.localName)
                self.lookupOrCreateNamespace(attr.nodeValue, attr.localName)
            elif 'xmlns' == attr.name:
                default_namespace = attr.nodeValue
            else:
                self._setAttributeFromDOM(attr)
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
        assert self.hasAttribute('targetNamespace')
        target_namespace = self.getAttribute('targetNamespace')
        if target_namespace is not None:
            self.setTargetNamespace(self.lookupOrCreateNamespace(target_namespace))

        # Now pre-load the namespaces that must be available.
        self.initializeBuiltins()

        # Verify that the root node is an XML schema element
        if root_node.nodeName not in self.xsQualifiedNames('schema'):
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
        """Throw a SchemaValidationException referencing the given
        node if we have passed the sequence point representing the end
        of prolog elements."""
        if self.__pastProlog:
            raise SchemaValidationError('Unexpected node %s after prolog' % (node_name,))

    def _processInclude (self, node):
        self._requireInProlog(node.nodeName)
        raise IncompleteImplementationException('include directive not implemented')

    def _processImport (self, node):
        """Process an import directive.

        This attempts to locate schema (named entity) information for
        a namespace that is referenced by this schema.
        """

        self._requireInProlog(node.nodeName)
        if not node.hasAttribute('namespace'):
            raise SchemaValidationError('import directive must provide namespace')
        uri = node.getAttribute('namespace')
        namespace = self.namespaceForURI(uri)
        # @todo 
        namespace.checkInitialized()
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
        an = xsc.AttributeDeclaration.CreateFromDOM(self, node)
        self._addNamedComponent(an)
        return an

    def _processSimpleType (self, node):
        """Walk a simpleType element to create a simple type definition component.
        """
        # Node should be a topLevelSimpleType
        assert node.nodeName in self.xsQualifiedNames('simpleType')
        assert node.parentNode.nodeName in self.xsQualifiedNames('schema')

        rv = xsc.SimpleTypeDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processComplexType (self, node):
        """Walk a complexType element to create a complex type definition component.
        """
        # Node should be a topLevelComplexType
        assert node.nodeName in self.xsQualifiedNames('complexType')
        assert node.parentNode.nodeName in self.xsQualifiedNames('schema')

        rv = xsc.ComplexTypeDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processAttributeGroup (self, node):
        # Node should be a namedAttributeGroup
        assert node.nodeName in self.xsQualifiedNames('attributeGroup')
        assert node.parentNode.nodeName in self.xsQualifiedNames('schema')
        rv = xsc.AttributeGroupDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    def _processGroup (self, node):
        # Node should be a namedGroup
        assert node.nodeName in self.xsQualifiedNames('group')
        assert node.parentNode.nodeName in self.xsQualifiedNames('schema')
        rv = xsc.ModelGroupDefinition.CreateFromDOM(self, node)
        self._addNamedComponent(rv)
        return rv

    # @todo make process* private
    def _processElementDeclaration (self, node):
        # Node should be a named element
        assert node.nodeName in self.xsQualifiedNames('element')
        assert node.parentNode.nodeName in self.xsQualifiedNames('schema')
        ed = xsc.ElementDeclaration.CreateFromDOM(self, node)
        self._addNamedComponent(ed)
        return ed

    def processTopLevelNode (self, node):
        """Process a DOM node from the top level of the schema.

        This should return a non-None value if the node was
        successfully recognized."""
        if node.nodeName in self.xsQualifiedNames('include'):
            return self._processInclude(node)
        if node.nodeName in self.xsQualifiedNames('import'):
            return self._processImport(node)
        if node.nodeName in self.xsQualifiedNames('redefine'):
            return self._processRedefine(node)
        if node.nodeName in self.xsQualifiedNames('annotation'):
            return self._processAnnotation(node)
        rv = schemaTop.Match(self, node)
        if rv is not None:
            self.__pastProlog = True
            return rv
        raise SchemaValidationError('Unexpected top-level element %s' % (node.nodeName,))

    def domRootNode (self):
        return self.__domRootNode

# @todo Replace this with a reference to Namespace.XMLSchema
def SchemaForXS (wxs):
    '''Create a Schema instance that targets the XMLSchema namespace.
    Preload all its elements.  Note that we only need to do this in
    the bootstrap code.'''
    rv = schema()
    rv.setTargetNamespace(wxs.xs())
    xsd.DefineSimpleTypes(rv)
    return rv

Namespace.SetStructuresModule(xsc, schema)
