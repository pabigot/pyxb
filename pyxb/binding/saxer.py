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

"""This module contains for generating bindings from an XML stream
using a SAX parser."""

import xml.sax
import xml.sax.handler
import pyxb.namespace

class _SAXElementState (object):
    """State corresponding to processing a given element."""

    # Reference to the _SAXElementState of the element enclosing this one
    __parentState = None

    # The pyxb.namespace.NamespaceContext used for this binding
    __namespaceContext = None

    # The binding object being created for this element.  When the
    # element type has simple content, the binding instance cannot be
    # created until the end of the element has been reached and the
    # content of the element has been processed accumulated for use in
    # the instance constructor.  When the element type has complex
    # content, the binding instance must be created at the start of
    # the element, so contained elements can be properly stored.
    __bindingObject = None

    # The nearest enclosing complex type definition
    __enclosingCTD = None

    # An accumulation of non-element content
    __content = None

    # The factory that is called to create a binding instance for this
    # element; None if the binding instance was created at the start
    # of the element.
    __delayedConstructor = None

    # The pyxb.binding.content.ElementUse instance for this element
    # within its parent object.
    __elementUse = None

    # An xml.sax.xmlreader.Attributes instance providing the
    # attributes for the element.
    __attributes = None
    
    def __init__ (self, namespace_context, parent_state):
        self.__namespaceContext = namespace_context
        self.__parentState = parent_state
        self.__bindingObject = None
        if isinstance(self.__parentState, _SAXElementState):
            self.__enclosingCTD = self.__parentState.enclosingCTD()
        else:
            self.__enclosingCTD = None
        self.__content = []

    def enclosingCTD (self):
        """The nearest enclosing complex type definition; None if this
        is a top-level element.

        You need this when resolving local element names."""
        return self.__enclosingCTD
    def setEnclosingCTD (self, enclosing_ctd):
        """Set the enclosing complex type definition for this element."""
        self.__enclosingCTD = enclosing_ctd
        return self

    def content (self):
        """Return a string catenating all non-element content observed
        within this node."""
        return ''.join(self.__content)

    # Create the binding instance for this element.
    def __constructElement (self, new_object_factory, attrs, content=None):
        if content is not None:
            self.__bindingObject = new_object_factory(content)
        else:
            self.__bindingObject = new_object_factory()
        # Set the attributes.
        if isinstance(self.__bindingObject, pyxb.binding.basis.complexTypeDefinition):
            for attr_name in self.__attributes.getNames():
                attr_en = pyxb.namespace.ExpandedName(attr_name)
                au = self.__bindingObject._AttributeMap.get(attr_en)
                if au is not None:
                    au.set(self.__bindingObject, attrs.getValue(attr_name))
        # If this element appears inside an enclosing object, store it
        # within that object.
        if self.__elementUse is not None:
            assert self.__parentState is not None
            assert self.__parentState.__bindingObject is not None
            self.__elementUse.setOrAppend(self.__parentState.__bindingObject, self.__bindingObject)
        # Record the namespace context so users of the binding can
        # interprete QNames within the attributes and content.
        self.__bindingObject._setNamespaceContext(self.__namespaceContext)
        return self.__bindingObject

    def startElement (self, type_class, new_object_factory, element_use, attrs):
        self.__delayedConstructor = None
        self.__elementUse = element_use
        self.__attributes = attrs
        if type_class._IsSimpleTypeContent():
            self.__delayedConstructor = new_object_factory
            self.__attributes = attrs
        else:
            self.__constructElement(new_object_factory, attrs)
        return self.__bindingObject

    def addContent (self, content):
        self.__content.append(content)

    def endElement (self):
        if self.__delayedConstructor is not None:
            self.__constructElement(self.__delayedConstructor, self.__attributes, self.content())
        return self.__bindingObject

class PyXBSAXHandler (xml.sax.handler.ContentHandler):
    # An expanded name corresponding to xsi:type
    __XSITypeTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('type').uriTuple()

    # The namespace context that will be in effect at the start of the
    # next element.  One of these is allocated at the start of each
    # element; it moves to become the current namespace upon receipt
    # of either the next element start or a namespace directive that
    # will apply at that element start.
    __nextNamespaceContext = None

    # The namespace context that is in effect for this element.
    __namespaceContext = None

    # A SAX locator object.  @todo: Figure out how to associate the
    # location information with the binding objects.
    __locator = None

    # The state for the element currently being processed
    __elementState = None

    # The states for all enclosing elements
    __elementStateStack = []

    def rootObject (self):
        """Return the binding object corresponding to the top-most
        element in the document."""
        return self.__rootObject
    __rootObject = None

    def reset (self):
        """Reset the state of the handler in preparation for
        processing a new document."""
        self.__namespaceContext = pyxb.namespace.NamespaceContext()
        self.__nextNamespaceContext = None
        self.__locator = None
        self.__elementState = _SAXElementState(self.__namespaceContext, None)
        self.__elementStateStack = []
        self.__rootObject = None

    def __init__ (self):
        self.reset()

    def namespaceContext (self):
        """Return the current namespace context"""
        return self.__namespaceContext
    
    # If there's a new namespace waiting to be used, make it the
    # current namespace.  Return the current namespace.
    def __updateNamespaceContext (self):
        if self.__nextNamespaceContext is not None:
            self.__namespaceContext = self.__nextNamespaceContext
            self.__nextNamespaceContext = None
        return self.__namespaceContext

    def startDocument (self):
        """Reset this handler for a new document."""
        self.reset()

    def setDocumentLocator (self, locator):
        """Save the locator."""
        self.__locator = locator

    def startPrefixMapping (self, prefix, uri):
        """Record (or remove) the namespace association for the given prefix."""
        self.__updateNamespaceContext().processXMLNS(prefix, uri)

    # The NamespaceContext management does not require any action upon
    # leaving the scope of a namespace directive.
    #def endPrefixMapping (self, prefix):
    #    pass

    def startElementNS (self, name, qname, attrs):
        # Get the element name including namespace information
        name_en = pyxb.namespace.ExpandedName(name)

        # Get the context to be used for this element, and create a
        # new context for the next contained element to be found.
        ns_ctx = self.__updateNamespaceContext()
        self.__nextNamespaceContext = pyxb.namespace.NamespaceContext(parent_context=ns_ctx)

        # Save the state of the enclosing element, and create a new
        # state for this element.
        parent_state = self.__elementState
        self.__elementStateStack.append(self.__elementState)
        self.__elementState = this_state = _SAXElementState(ns_ctx, parent_state)

        # Start knowing nothing
        type_class = element_use = element_binding = None

        # Process an xsi:type attribute, if present
        if attrs.has_key(self.__XSITypeTuple):
            xsi_type = attrs.getValue(self.__XSITypeTuple)
            type_class = ns_ctx.interpretQName(xsi_type).typeBinding()

        # @todo: handle substitution groups

        # Resolve the element within the appropriate context.  Note
        # that global elements have no use, only the binding.
        if parent_state.enclosingCTD() is not None:
            element_use = parent_state.enclosingCTD()._UseForTag(name_en)
        else:
            element_binding = name_en.elementBinding()

        # Non-root elements should have an element use, from which we
        # can extract the binding.
        if element_use is not None:
            assert self.__rootObject is not None
            element_binding = element_use.elementBinding()
            assert element_binding is not None

        # Get the factory method for the binding type for the element instance
        if type_class is not None:
            # @todo: validate xsi:type against abstract
            new_object_factory = type_class.Factory
        else:
            assert element_binding is not None
            new_object_factory = element_binding
            type_class = element_binding.typeDefinition()

        # Update the enclosing complex type definition for this
        # element state.
        assert type_class is not None
        if issubclass(type_class, pyxb.binding.basis.complexTypeDefinition):
            this_state.setEnclosingCTD(type_class)
        else:
            this_state.setEnclosingCTD(parent_state.enclosingCTD())

        # Process the element start.  This may or may not return a
        # binding object.
        binding_object = this_state.startElement(type_class, new_object_factory, element_use, attrs)

        # If the top-level element has complex content, this sets the
        # root object.  If it has simple content, see endElementNS.
        if self.__rootObject is None:
            self.__rootObject = binding_object

    def endElementNS (self, name, qname):
        # Save the state of this element, and restore the state for
        # the parent to which we are returning.
        this_state = self.__elementState
        parent_state = self.__elementState = self.__elementStateStack.pop()

        # Process the element end.  This will return a binding object,
        # either the one created at the start or the one created at
        # the end.
        binding_object = this_state.endElement()
        assert binding_object is not None

        # If we don't have a root object, save it.  No, there is not a
        # problem doing this on the close of the element.  If the
        # top-level element has complex content, the object was
        # created on start, and the root object has been assigned.  If
        # it has simple content, then there are no internal elements
        # that could slip in and set this before we get to it here.
        if self.__rootObject is None:
            self.__rootObject = binding_object

    def characters (self, content):
        """Save the text as content"""
        self.__elementState.addContent(content)

    def ignorableWhitespace (self, whitespace):
        """Save whitespace as content too."""
        self.__elementState.addContent(whitespace)

def make_parser (*args, **kw):
    """Extend xml.sax.make_parser to configure the parser the way we
    need it:

    - C{feature_namespaces} is set to C{True} so we process xmlns
      directives properly
    - C{feature_namespace_prefixes} is set to C{False} so we don't get
      prefixes encoded into our names (probably redundant with the
      above but still...)
    - The content handler is set to a fresh instance of R{PyXBSAXHandler}.
    """
    parser = xml.sax.make_parser(*args, **kw)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, False)
    parser.setContentHandler(PyXBSAXHandler())
    return parser

## Local Variables:
## fill-column:78
## End:
    
