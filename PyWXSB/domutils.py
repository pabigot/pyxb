import PyWXSB.Namespace as Namespace
from PyWXSB.exceptions_ import *
from xml.dom import Node
from xml.dom import minidom
import xml.dom as dom

def NodeAttribute (node, schema, attribute_ncname, attribute_ns=Namespace.XMLSchema):
    """Look up an attribute in a node.

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
    assert node.namespaceURI is not None
    container_ns = schema.namespaceForURI(node.namespaceURI)
    assert container_ns is not None
    assert attribute_ns is not None
    candidate_names = schema.qualifiedNames(attribute_ncname, attribute_ns)
    if (attribute_ns == container_ns) and not (attribute_ncname in candidate_names):
        candidate_names = candidate_names + (attribute_ncname,)
    attr_value = None
    match_name = None
    for attr_name in candidate_names:
        if node.hasAttribute(attr_name):
            if attr_value is not None:
                raise SchemaValidationError('Multiple instances of attribute %s from %s' % (attribute_ncname, attribute_ns.uri()))
            attr_value = node.getAttribute(attr_name)
    return attr_value

def LocateUniqueChild (node, schema, tag, absent_ok=True, namespace=Namespace.XMLSchema):
    """Locate a unique child of the DOM node.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  The
    schema from which the node derives is also provided.  tag is the
    NCName of an XMLSchema element.  This function returns the sole
    child of node which is an ELEMENT_NODE instance and has a tag
    consistent with the given tag.  If multiple nodes with a matching
    tag are found, or abesnt_ok is False and no matching tag is found,
    an exception is raised.

    @throw SchemaValidationError if multiple elements are identified
    @throw SchemaValidationError if absent_ok is False and no element is identified.
    """
    candidate = None
    # @todo identify QName children as well as NCName
    names = schema.qualifiedNames(tag, namespace)
    for cn in node.childNodes:
        if (Node.ELEMENT_NODE == cn.nodeType) and (cn.nodeName in names):
            if candidate:
                raise SchemaValidationError('Multiple %s elements nested in %s' % (name, node.nodeName))
            candidate = cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('Expected %s elements nested in %s' % (name, node.nodeName))
    return candidate

def LocateMatchingChildren (node, schema, tag, namespace=Namespace.XMLSchema):
    """Locate all children of the DOM node that have a particular tag.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  The
    schema from which the node derives is also provided.  tag is the
    NCName of an XMLSchema element.  This function returns a list of
    children of node which are an ELEMENT_NODE instances and have a tag
    consistent with the given tag.
    """
    matches = []
    names = schema.qualifiedNames(tag, namespace)
    for cn in node.childNodes:
        if (Node.ELEMENT_NODE == cn.nodeType) and (cn.nodeName in names):
            matches.append(cn)
    return matches

def LocateFirstChildElement (node, absent_ok=True, require_unique=False):
    """Locate the first element child of the node.

    If absent_ok is True, and there are no ELEMENT_NODE children, None
    is returned.  If require_unique is True and there is more than one
    ELEMENT_NODE child, an exception is rasied.
    """
    
    candidate = None
    for cn in node.childNodes:
        if Node.ELEMENT_NODE == cn.nodeType:
            if require_unique:
                if candidate:
                    raise SchemaValidationError('Multiple elements nested in %s' % (node.nodeName,))
                candidate = cn
            else:
                return cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('No elements nested in %s' % (node.nodeName,))
    return candidate

def HasNonAnnotationChild (wxs, node):
    """Return True iff node has an ELEMENT_NODE child that is not an
    XMLSchema annotation node."""
    xs_annotation = wxs.xsQualifiedNames('annotation')
    for cn in node.childNodes:
        if Node.ELEMENT_NODE != cn.nodeType:
            continue
        if cn.nodeName not in xs_annotation:
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
