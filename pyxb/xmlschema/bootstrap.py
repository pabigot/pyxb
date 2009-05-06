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

import pyxb.utils.domutils

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

    def __init__ (self, **kw):
        super(schema, self).__init__(self, **kw)
        self.__namespaces = set()

    def initializeBuiltins (self):
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
            assert (self.targetNamespace().schema() is None) or (self.targetNamespace() in (Namespace.XMLSchema, Namespace.XML) )
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

    # Compile-time spelling check
    __QUALIFIED = 'qualified'
    # Compile-time spelling check
    __UNQUALIFIED = 'unqualified'

    def namespaces (self):
        """Return the set of namespaces associated with this schema."""
        return self.__namespaces

    def createDOMNodeInNamespace (self, dom_document, nc_name, namespace=None):
        if namespace is None:
            namespace = self.defaultNamespace()
        uri = None
        if namespace is not None:
            uri = namespace.uri()
        return dom_document.createElementNS(uri, nc_name)

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

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        pyxb.utils.domutils.SetInScopeNamespaces(node)

        default_namespace = None
        root_node = node
        if xml.dom.Node.DOCUMENT_NODE == node.nodeType:
            root_node = root_node.documentElement
        if xml.dom.Node.ELEMENT_NODE != root_node.nodeType:
            raise LogicError('Must be given a DOM node of type ELEMENT')

        if attributes is None:
            attributes = root_node.attributes
        attribute_map = { }
        default_namespace = None
        for attr in attributes.values():
            if 'xmlns' == attr.prefix:
                Namespace.NamespaceForURI(attr.nodeValue, create_if_missing=True)
            elif 'xmlns' == attr.name:
                default_namespace = Namespace.NamespaceForURI(attr.nodeValue, create_if_missing=True)
            else:
                attribute_map[attr.name] = attr.nodeValue

        tns_uri = attribute_map.get('targetNamespace', None)
        if tns_uri is None:
            tns = Namespace.CreateAbsentNamespace()
        else:
            tns = Namespace.NamespaceForURI(tns_uri, create_if_missing=True)
        assert tns is not None
        schema = tns.schema()
        if schema is None:
            schema = cls(target_namespace=tns, default_namespace=default_namespace)
        assert schema.targetNamespace() == tns
        assert schema.defaultNamespace() == default_namespace

        # Update the attribute map
        schema._setAttributesFromMap(attribute_map)

        # Now pre-load the namespaces that must be available.
        schema.initializeBuiltins()

        # Verify that the root node is an XML schema element
        if not xs.nodeIsNamed(root_node, 'schema'):
            raise SchemaValidationError('Root node %s of document is not an XML schema element' % (root_node.nodeName,))

        schema.__domRootNode = root_node

        for cn in root_node.childNodes:
            if xml.dom.Node.ELEMENT_NODE == cn.nodeType:
                rv = schema.processTopLevelNode(cn)
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

        schema._resolveDefinitions()

        return schema

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
        namespace = Namespace.NamespaceForURI(uri, create_if_missing=True)
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
