# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Functions that support activities related to the Document Object Model."""

import pyxb
import pyxb.namespace
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

def NodeAttribute (node, attribute_ncname, attribute_ns=None):
    """Namespace-aware search for an optional attribute in a node.

    @param attribute_ncname: The local name of the attribute.
    @type attribute_ncname: C{str} or C{unicode}

    @param attribute_ns: The namespace of the attribute.  Defaults to None
    since most attributes are not in a namespace.  Can be provided as either a
    L{pyxb.namespace.Namespace} instance, or a string URI.
    @type attribute_ns: C{None} or C{str} or C{unicode} or L{pyxb.namespace.Namespace}

    @return: The value of the attribute, or C{None} if the attribute is not
    present.  (Unless C{None}, the value will always be a (unicode) string.)
    """

    ns_uri = attribute_ns
    if isinstance(attribute_ns, pyxb.namespace.Namespace):
        ns_uri = attribute_ns.uri()
    attr = node.getAttributeNodeNS(ns_uri, attribute_ncname)
    if attr is None:
        return None
    return attr.value

def LocateUniqueChild (node, tag, absent_ok=True, namespace=pyxb.namespace.XMLSchema):
    """Locate a unique child of the DOM node.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  tag is
    the NCName of an element in the namespace, which defaults to the
    XMLSchema namespace.  This function returns the sole child of node
    which is an ELEMENT_NODE instance and has a tag consistent with
    the given tag.  If multiple nodes with a matching tag are found,
    or abesnt_ok is False and no matching tag is found, an exception
    is raised.

    @raise pyxb.SchemaValidationError: multiple elements are identified
    @raise pyxb.SchemaValidationError: C{absent_ok} is C{False} and no element is identified.
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

def LocateMatchingChildren (node, tag, namespace=pyxb.namespace.XMLSchema):
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
            if ignore_annotations and pyxb.namespace.XMLSchema.nodeIsNamed(cn, 'annotation'):
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
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and (not pyxb.namespace.XMLSchema.nodeIsNamed(cn, 'annotation')):
            return True
    return False

def ExtractTextContent (node):
    """Walk all the children, extracting all text content and
    catenating it.

    Returns None if no text content (including whitespace) is found.
    
    This is mainly used to strip comments out of the content of complex
    elements with simple types."""
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
    if 0 == len(text):
        return None
    return ''.join(text)

class BindingDOMSupport (object):
    """This holds DOM-related information used when generating a DOM tree from
    a binding instance."""
    # Namespace declarations required on the top element
    __namespaces = None

    __namespacePrefixCounter = None

    def defaultNamespace (self):
        """The registered default namespace.

        The default namespace can be set in the constructor, or using the
        L{setDefaultNamespace} method.  @rtype: L{pyxb.namespace.Namespace} or
        C{None}
        """
        return self.__defaultNamespace
    __defaultNamespace = None

    def implementation (self):
        """The DOMImplementation object to be used.

        Defaults to L{pyxb.utils.domutils.GetDOMImplementation()}, but can be
        overridden in the constructor call using the C{implementation}
        keyword."""
        return self.__implementation
    __implementation = None

    def document (self):
        """Return the document generated using this instance."""
        return self.__document
    __document = None

    def requireXSIType (self):
        """Indicates whether xsi:type should be added to all elements.

        Certain WSDL styles and encodings seem to require explicit notation of
        the type of each element, even if it was specified in the schema.

        This value can only be set in the constructor."""
        return self.__requireXSIType
    __requireXSIType = None

    def __init__ (self, implementation=None, default_namespace=None, require_xsi_type=False):
        """Create a new instance used for building a single document.

        @keyword implementation: The C{xml.dom} implementation to use.
        Defaults to the one selected by L{GetDOMImplementation}.

        @keyword default_namespace: The namespace to configure as the default
        for the document.  If not provided, there is no default namespace.

        @keyword require_xsi_type: If C{True}, an U{xsi:type
        <http://www.w3.org/TR/xmlschema-1/#xsi_type>} attribute should be
        placed in every element.
        """
        if implementation is None:
            implementation = GetDOMImplementation()
        self.__implementation = implementation
        self.__document = self.implementation().createDocument(None, None, None)
        self.__namespaces = { }
        self.__namespacePrefixCounter = 0
        self.__requireXSIType = require_xsi_type
        self.setDefaultNamespace(default_namespace)

    def setDefaultNamespace (self, default_namespace):
        """Set the default namespace for the generated document.

        Even if invoked post construction, the default namespace will affect
        the entire document, as all namespace declarations are placed in the
        document root.

        @param default_namespace: The namespace to be defined as the default
        namespace in the top-level element of the document.  May be provided
        as a real namespace, or just its URI.

        @type default_namespace: L{pyxb.namespace.Namespace} or C{str} or
        C{unicode}.
        """

        if self.__defaultNamespace is not None:
            del self.__namespaces[self.__defaultNamespace]
        if isinstance(default_namespace, pyxb.namespace.Namespace):
            default_namespace = default_namespace.uri()
        self.__defaultNamespace = default_namespace
        if self.__defaultNamespace is not None:
            self.__namespaces[self.__defaultNamespace] = None

    def declareNamespace (self, namespace, prefix=None):
        """Add the given namespace as one to be used in this document.

        @param namespace: The namespace to be associated with the document.  May be provided
        as a real namespace, or just its URI.

        @type namespace: L{pyxb.namespace.Namespace} or C{str} or
        C{unicode}.

        @param prefix: Optional prefix to be used with this namespace.  If not
        provided, a unique prefix is generated or a standard prefix is used,
        depending on the namespace.

        @todo: ensure multiple namespaces do not share the same prefix
        @todo: provide default prefix in L{pyxb.namespace.Namespace}
        @todo: support multiple prefixes for each namespace
        """
        if isinstance(namespace, pyxb.namespace.Namespace):
            namespace = namespace.uri()
        if prefix is None:
            if (pyxb.namespace.XMLSchema_instance.uri() == namespace) and not ('xsi' in self.__namespaces):
                prefix = 'xsi'
            else:
                self.__namespacePrefixCounter += 1
                prefix = 'ns%d' % (self.__namespacePrefixCounter,)
        self.__namespaces[namespace] = prefix
        return prefix

    def namespacePrefix (self, namespace):
        """Return the prefix to be used for the given namespace.

        This will L{declare <declareNamespace>} the namespace if it has not
        yet been observed.
        """
        
        if isinstance(namespace, pyxb.namespace.Namespace):
            namespace = namespace.uri()
        if namespace is None:
            return None
        if not (namespace in self.__namespaces):
            return self.declareNamespace(namespace)
        return self.__namespaces[namespace]

    def addAttribute (self, element, expanded_name, value):
        """Add an attribute to the given element.

        @param element: The element to which the attribute should be added
        @type element: C{xml.dom.Element}
        @param expanded_name: The name of the attribute.  This may be a local
        name if the attribute is not in a namespace.
        @type expanded_name: L{pyxb.namespace.Namespace} or C{str} or C{unicode}
        @param value: The value of the attribute
        @type value: C{str} or C{unicode}
        """
        name = expanded_name
        namespace = None
        if isinstance(name, pyxb.namespace.ExpandedName):
            name = expanded_name.localName()
            namespace = expanded_name.namespace()
            prefix = self.namespacePrefix(namespace)
            if prefix is not None:
                name = '%s:%s' % (prefix, name)
        element.setAttributeNS(namespace, name, value)

    def finalize (self):
        """Do the final cleanup after generating the tree.  This makes sure
        that the document element includes XML Namespace declarations for all
        namespaces referenced in the tree.

        @return: The document that has been created.
        @rtype: xml.dom.Document"""
        for ( ns_uri, pfx ) in self.__namespaces.items():
            if pfx is None:
                self.document().documentElement.setAttributeNS(pyxb.namespace.XMLNamespaces.uri(), 'xmlns', ns_uri)
            else:
                self.document().documentElement.setAttributeNS(pyxb.namespace.XMLNamespaces.uri(), 'xmlns:%s' % (pfx,), ns_uri)
        return self.document()

    def createChildElement (self, expanded_name, parent=None):
        """Create a new element node in the tree.

        @param expanded_name: The name of the element.  A plain string
        indicates a name in no namespace.
        @type expanded_name: L{pyxb.namespace.ExpandedName} or C{str} or C{unicode}

        @keyword parent: The node in the tree that will serve as the child's
        parent.  If C{None}, the document element is used.  (If there is no
        document element, then this call creates it as a side-effect.)

        @return: A newly created DOM element
        @rtype: C{xml.dom.Element}
        """

        if parent is None:
            parent = self.document().documentElement
        if parent is None:
            parent = self.__document
        ns_uri = xml.dom.EMPTY_NAMESPACE
        if isinstance(expanded_name, pyxb.namespace.ExpandedName):
            name = expanded_name.localName()
            ns_uri = expanded_name.namespaceURI()
        elif isinstance(expanded_name, (str, unicode)):
            name = expanded_name
        else:
            raise pyxb.LogicError('Invalid type %s for expanded name' % (type(expanded_name),))
        if ns_uri is not None:
            if ns_uri in self.__namespaces:
                pfx = self.__namespaces[ns_uri]
            else:
                pfx = self.declareNamespace(ns_uri)
            if pfx is not None:
                name = '%s:%s' % (pfx, name)
        element = self.__document.createElementNS(ns_uri, name)
        return parent.appendChild(element)


## Local Variables:
## fill-column:78
## End:
    
