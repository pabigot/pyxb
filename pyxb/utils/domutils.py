import pyxb.Namespace as Namespace
from pyxb.exceptions_ import *
from xml.dom import Node
from xml.dom import minidom
import xml.dom as dom
from pyxb.Namespace import XMLSchema as xsd

def NodeAttribute (node, attribute_ncname, attribute_ns=Namespace.XMLSchema):
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

def LocateUniqueChild (node, tag, absent_ok=True, namespace=Namespace.XMLSchema):
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
        if (Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
            if candidate:
                raise SchemaValidationError('Multiple %s elements nested in %s' % (name, node.nodeName))
            candidate = cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('Expected %s elements nested in %s' % (name, node.nodeName))
    return candidate

def LocateMatchingChildren (node, tag, namespace=Namespace.XMLSchema):
    """Locate all children of the DOM node that have a particular tag.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  tag is
    the NCName of an element in the namespace, which defaults to the
    XMLSchema namespace.  This function returns a list of children of
    node which are an ELEMENT_NODE instances and have a tag consistent
    with the given tag.
    """
    matches = []
    for cn in node.childNodes:
        if (Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
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
        if Node.ELEMENT_NODE == cn.nodeType:
            if ignore_annotations and xsd.nodeIsNamed(cn, 'annotation'):
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
        if (Node.ELEMENT_NODE == cn.nodeType) and (not xsd.nodeIsNamed(cn, 'annotation')):
            return True
    return False

def ExtractTextContent (node):
    """Walk all the children, extracting all text content and
    catenating it.  This is mainly used to strip comments out of the
    content of complex elements with simple types."""
    text = []
    for cn in node.childNodes:
        if Node.TEXT_NODE == cn.nodeType:
            text.append(cn.data)
        elif Node.CDATA_SECTION_NODE == cn.nodeType:
            text.append(cn.data)
        elif Node.COMMENT_NODE == cn.nodeType:
            pass
        else:
            raise BadDocumentError('Non-text node %s found in content' % (cn,))
    return ''.join(text)

def ToDOM_startup (document, parent, tag=None):
    """Create the DOM infrastructure necessary to convert a binding instance to DOM.
    
    If the document and parent are not defined, a new DOM document
    instance is created from the default implementation, and it and
    the document element are returned.
    
    Otherwise, if tag is not None a new element that is a child of
    parent is created.  If tag is None, the parent is returned as the
    element.

    Returns a pair (document, element)."""
    if document is None:
        assert parent is None
        assert tag is not None
        document = minidom.getDOMImplementation().createDocument(None, tag, None)
        element = document.documentElement
    else:
        assert parent is not None
        if tag is None:
            element = parent
        else:
            element = parent.appendChild(document.createElement(tag))
    return (document, element)

# In-scope namespaces are represented as a map from a prefix to a
# Namespace instance.  The prefix is None when representing the
# default namespace.

__InScopeNamespaceAttribute = '_pyxb_utils_domutils__InScopeNamespaces'

def GetInScopeNamespaces (node):
    return getattr(node, __InScopeNamespaceAttribute, None)

def __SetInScopeNamespaces (node, namespace_map):
    adds = []
    removes = []
    if Node.ELEMENT_NODE == node.nodeType:
        attributes = node.attributes
        for attr in [ attributes.item(_ai) for _ai in range(attributes.length) ]:
            #print '%s %s %s %s' % (attr.namespaceURI, attr.prefix, attr.localName, attr.value)
            if attr.namespaceURI == Namespace.XMLNamespaces.uri():
                #print 'XMLNS %s %s %s' % (attr.prefix, attr.localName, attr.value)
                if attr.value:
                    adds.append(attr)
                else:
                    removes.append(attr)
    #overrode_map = None
    if 0 < (len(adds) + len(removes)):
        #overrode_map = namespace_map
        namespace_map = namespace_map.copy()
        for attr in removes:
            # NB: XMLNS 6.2 says that you can undefine a default
            # namespace, but does not say anything explicitly about
            # undefining a prefixed namespace.  XML-Infoset 2.2
            # paragraph 6 implies you can do this, but expat blows up
            # if you try it.  Nonetheless, we'll pretend that it's
            # legal.
            if attr.prefix is None:
                namespace_map.pop(None, None)
            else:
                namespace_map.pop(attr.localName, None)
        for attr in adds:
            ns = Namespace.NamespaceForURI(attr.value, create_if_missing=True)
            if attr.prefix is None:
                namespace_map[None] = ns
            else:
                namespace_map[attr.localName] = ns
        #print 'New xmlns map at %s: %s' % (node.nodeName, namespace_map,)
    setattr(node, __InScopeNamespaceAttribute, namespace_map)
    for cn in node.childNodes:
        __SetInScopeNamespaces(cn, namespace_map)
    #if overrode_map is not None:
    #    print 'Restoring xmlns map: %s' % (overrode_map,)

__UndeclaredNamespaces = { }
[ __UndeclaredNamespaces.setdefault(_ns.boundPrefix(), _ns) for _ns in Namespace.PredefinedNamespaces if _ns.isUndeclaredNamespace() ]

def SetInScopeNamespaces (node, in_scope_namespaces={}):
    isn = __UndeclaredNamespaces
    if in_scope_namespaces:
        isn = isn.copy()
        isn.update(in_scope_namespaces)
    __SetInScopeNamespaces(node, isn)
    return node

def InterpretQName (node, name):
    if name is None:
        return None
    # Do QName interpretation
    if 0 <= name.find(':'):
        (prefix, local_name) = name.split(':', 1)
        namespace = GetInScopeNamespaces(node).get(prefix, None)
        if namespace is None:
            raise SchemaValidationError('QName %s prefix is not declared' % (name,))
    else:
        local_name = name
        # Get the default namespace, or denote an absent namespace
        namespace = GetInScopeNamespaces(node).get(None, None)
    return (namespace, local_name)

def InterpretAttributeQName (node, attribute_ncname, attribute_ns=Namespace.XMLSchema):
    """Provide the namespace and local name for the value of the given
    attribute in the node.

    attribute_ns is the namespace that should be used when locating
    the attribute within the node.  If no matching attribute can be
    found, this function returns None.

    If the attribute is found, its value is normalized per QName's
    whitespace facet (collapse), then QName interpretation per section
    3.15.3 is performed to identify the namespace name and localname
    to which the value refers.  If the resulting namespace is absent,
    the value None used; otherwise, the Namespace instance for the
    namespace name is used.

    The return value is None, or a pair consisting of a Namespace
    instance or None and a local name.
    """

    return InterpretQName(node, NodeAttribute(node, attribute_ncname, attribute_ns))

def AttributeMap (node):
    attribute_map = { }
    for ai in range(node.attributes.length):
        attr = node.attributes.item(ai)
        attribute_map[(attr.namespaceURI, attr.localName)] = attr.value
        print '%s %s = %s' % (attr.namespaceURI, attr.localName, attr.value)
    return attribute_map

class NamespaceDataFromNode (object):

    def defaultNamespace (self):
        return self.__defaultNamespace
    __defaultNamespace = None

    def targetNamespace (self):
        return self.__targetNamespace
    __targetNamespace = None

    def inScopeNamespaces (self):
        return self.__inScopeNamespaces
    __inScopeNamespaces = None

    def attributeMap (self):
        return self.__attributeMap
    __attributeMap = None

    def __init__ (self, node, attributes=None):

        if attributes is None:
            attributes = AttributeMap(node)

        self.__attributeMap = { }
        self.__defaultNamespace = None
        self.__inScopeNamespaces = { }
        for (( ns_uri, attr_ln), attr_value) in attributes.items():
            if Namespace.XMLNamespaces.uri() == ns_uri:
                if 'xmlns' == attr_ln:
                    self.__defaultNamespace = Namespace.NamespaceForURI(attr_value, create_if_missing=True)
                    self.__inScopeNamespaces[None] = self.__defaultNamespace
                else:
                    self.__inScopeNamespaces[attr_ln] = Namespace.NamespaceForURI(attr_value, create_if_missing=True)
            else:
                # @todo probably should include namespace in this
                self.__attributeMap[attr_ln] = attr_value
        
        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        SetInScopeNamespaces(node, self.inScopeNamespaces())

        tns_uri = self.attributeMap().get('targetNamespace', None)
        if tns_uri is None:
            self.__targetNamespace = Namespace.CreateAbsentNamespace()
        else:
            self.__targetNamespace = Namespace.NamespaceForURI(tns_uri, create_if_missing=True)

