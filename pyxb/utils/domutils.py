import pyxb
import pyxb.Namespace
import xml.dom

# The DOM implementation to be used for all processing.  Default is whatever
# your Python install uses.  If it's minidom, it should work.
__DOMImplementation = xml.dom.getDOMImplementation()

def GetDOMImplementation ():
    """Return the DOMImplementation object used for pyxb operations.

    This is primarily used as the default implementation when generating DOM
    trees from a binding instance.  It defaults to whatever
    xml.dom.getDOMImplementation() returns in your installation (often
    xml.dom.minidom).  It can be overridden with SetDOMImplementation()."""

    global __DOMImplementation
    return __DOMImplementation

def SetDOMImplementation (dom_implementation):
    """Override the default DOMImplementation object."""
    global __DOMImplementation
    __DOMImplementation = dom_implementation
    return __DOMImplementation

# Unfortunately, the DOMImplementation interface doesn't provide a parser.  So
# abstract this in case somebody wants to substitute a different one.  Haven't
# decided how to express that yet.
def StringToDOM (text):
    """Convert string to a DOM instance.

    This is abstracted to allow future use of alternative parsers.
    Unfortunately, the interface for parsing a string does not appear to be
    consistent across implementations, so for now this always uses
    xml.dom.minidom."""
    return xml.dom.minidom.parseString(text)

def NodeAttribute (node, attribute_ncname, attribute_ns=pyxb.Namespace.XMLSchema):
    """Namespace-aware search for an attribute in a node.

    Be aware that the default namespace does not apply to attributes.

    NEVER EVER use node.hasAttribute or node.getAttribute directly.
    The attribute tag can often be in multiple forms.

    This gets tricky because the attribute tag may or may not be
    qualified with a namespace.  The qualifier may be elided if the
    attribute is defined in the namespace of the containing element,
    even if that is not the default namespace for the schema.

    Return the requested attribute, or None if the attribute is not
    present in the node.  Raises SchemaValidationError if the
    attribute appears multiple times.  @todo Not sure that's right.

    An example of where this is necessary is the attribute declaration
    for "lang" in http://www.w3.org/XML/1998/namespace, The simpleType
    includes a union clause whose memberTypes attribute is
    unqualified, and XMLSchema is not the default namespace."""

    assert node.namespaceURI
    if node.namespaceURI == attribute_ns.uri():
        if node.hasAttributeNS(None, attribute_ncname):
            return node.getAttributeNS(None, attribute_ncname)
    if node.hasAttributeNS(attribute_ns.uri(), attribute_ncname):
        assert False
        return node.getAttributeNS(attribute_ns.uri(), attribute_ncname)
    return None

def LocateUniqueChild (node, tag, absent_ok=True, namespace=pyxb.Namespace.XMLSchema):
    """Locate a unique child of the DOM node.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  tag is
    the NCName of an element in the namespace, which defaults to the
    XMLSchema namespace.  This function returns the sole child of node
    which is an ELEMENT_NODE instance and has a tag consistent with
    the given tag.  If multiple nodes with a matching tag are found,
    or abesnt_ok is False and no matching tag is found, an exception
    is raised.

    @throw SchemaValidationError if multiple elements are identified
    @throw SchemaValidationError if absent_ok is False and no element is identified.
    """
    candidate = None
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
            if candidate:
                raise SchemaValidationError('Multiple %s elements nested in %s' % (name, node.nodeName))
            candidate = cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('Expected %s elements nested in %s' % (name, node.nodeName))
    return candidate

def LocateMatchingChildren (node, tag, namespace=pyxb.Namespace.XMLSchema):
    """Locate all children of the DOM node that have a particular tag.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  tag is
    the NCName of an element in the namespace, which defaults to the
    XMLSchema namespace.  This function returns a list of children of
    node which are an ELEMENT_NODE instances and have a tag consistent
    with the given tag.
    """
    matches = []
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
            matches.append(cn)
    return matches

def LocateFirstChildElement (node, absent_ok=True, require_unique=False, ignore_annotations=True):
    """Locate the first element child of the node.

    If absent_ok is True, and there are no ELEMENT_NODE children, None
    is returned.  If require_unique is True and there is more than one
    ELEMENT_NODE child, an exception is rasied.  Unless
    ignore_annotations is False, annotation nodes are ignored.
    """
    
    candidate = None
    for cn in node.childNodes:
        if xml.dom.Node.ELEMENT_NODE == cn.nodeType:
            if ignore_annotations and pyxb.Namespace.XMLSchema.nodeIsNamed(cn, 'annotation'):
                continue
            if require_unique:
                if candidate:
                    raise SchemaValidationError('Multiple elements nested in %s' % (node.nodeName,))
                candidate = cn
            else:
                return cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('No elements nested in %s' % (node.nodeName,))
    return candidate

def HasNonAnnotationChild (node):
    """Return True iff node has an ELEMENT_NODE child that is not an
    XMLSchema annotation node."""
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and (not pyxb.Namespace.XMLSchema.nodeIsNamed(cn, 'annotation')):
            return True
    return False

def ExtractTextContent (node):
    """Walk all the children, extracting all text content and
    catenating it.  This is mainly used to strip comments out of the
    content of complex elements with simple types."""
    text = []
    for cn in node.childNodes:
        if xml.dom.Node.TEXT_NODE == cn.nodeType:
            text.append(cn.data)
        elif xml.dom.Node.CDATA_SECTION_NODE == cn.nodeType:
            text.append(cn.data)
        elif xml.dom.Node.COMMENT_NODE == cn.nodeType:
            pass
        else:
            raise BadDocumentError('Non-text node %s found in content' % (cn,))
    return ''.join(text)

class BindingDOMSupport (object):
    # Namespace declarations required on the top element
    __namespaces = None

    __namespacePrefixCounter = None

    def implementation (self):
        """The DOMImplementation object to be used.

        Defaults to pyxb.utils.domutils.GetDOMImplementation(), but can be
        overridden in the BindingDOMSupport constructor call."""
        return self.__implementation
    __implementation = None

    def document (self):
        return self.__document
    __document = None

    def __init__ (self, implementation=None):
        if implementation is None:
            implementation = GetDOMImplementation()
        self.__implementation = implementation
        self.__document = self.implementation().createDocument(None, None, None)
        self.__namespaces = { }
        self.__namespacePrefixCounter = 0

    def finalize (self):
        for ( ns_uri, pfx ) in self.__namespaces.items():
            if pfx is None:
                self.document().documentElement.setAttributeNS(pyxb.Namespace.XMLNamespaces.uri(), 'xmlns', ns_uri)
            else:
                self.document().documentElement.setAttributeNS(pyxb.Namespace.XMLNamespaces.uri(), 'xmlns:%s' % (pfx,), ns_uri)
        return self.document()

    def createChild (self, local_name, namespace=None, parent=None):
        if parent is None:
            parent = self.document().documentElement
        if parent is None:
            parent = self.__document
        ns_uri = namespace.uri()
        name = local_name
        if ns_uri is not None:
            if ns_uri in self.__namespaces:
                pfx = self.__namespaces[ns_uri]
            else:
                if 0 == len(self.__namespaces):
                    pfx = None
                else:
                    self.__namespacePrefixCounter += 1
                    pfx = 'ns%d' % (self.__namespacePrefixCounter,)
                self.__namespaces[ns_uri] = pfx
            if pfx is not None:
                name = '%s:%s' % (pfx, local_name)
        element = self.__document.createElementNS(ns_uri, name)
        return parent.appendChild(element)
    
def AttributeMap (node):
    attribute_map = { }
    for ai in range(node.attributes.length):
        attr = node.attributes.item(ai)
        attribute_map[(attr.namespaceURI, attr.localName)] = attr.value
    return attribute_map

## Local Variables:
## fill-column:78
## End:
    
