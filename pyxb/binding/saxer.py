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

    # An expanded name corresponding to xsi:nil
    __XSINilTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('nil').uriTuple()

    # Reference to the _SAXElementState of the element enclosing this one
    __parentState = None

    # The pyxb.namespace.resolution.NamespaceContext used for this binding
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
        """The nearest enclosing complex type definition, as used for
        resolving local element/attribute names.

        @return: An instance of L{basis.complexTypeDefinition}, or C{None} if
        the element is top-level
        """
        return self.__enclosingCTD
    def setEnclosingCTD (self, enclosing_ctd):
        """Set the enclosing complex type definition for this element.

        @param enclosing_ctd: The scope for a local element.
        @type enclosing_ctd: L{basis.complexTypeDefinition}
        @return: C{self}
        """
        self.__enclosingCTD = enclosing_ctd
        return self

    # Create the binding instance for this element.
    def __constructElement (self, new_object_factory, attrs, content=None):
        kw = {}

        # Note whether the node is marked nil
        if attrs.has_key(self.__XSINilTuple):
            kw['_nil'] = pyxb.binding.datatypes.boolean(attrs.getValue(self.__XSINilTuple))

        if content is None:
            content = []
        self.__bindingObject = new_object_factory(*content, **kw)

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
            #self.__elementUse.setOrAppend(self.__parentState.__bindingObject, self.__bindingObject)
        # Record the namespace context so users of the binding can
        # interprete QNames within the attributes and content.
        self.__bindingObject._setNamespaceContext(self.__namespaceContext)
        return self.__bindingObject

    def startElement (self, type_class, new_object_factory, element_use, attrs):
        """Actions upon entering an element.

        Th element use is recorded.  If the type is a subclass of
        L{basis.simpleTypeDefinition}, a delayed constructor is recorded so
        the binding instance can be created upon completion of the element;
        otherwise, a binding instance is created and stored.  The attributes
        are used to initialize the binding instance (now, or upon element
        end).

        @param type_class: The Python type of the binding instance
        @type type_class: subclass of L{basis._TypeBinding_mixin}
        @param new_object_factory: A callable object that creates an instance of the C{type_class}
        @param element_use: The element use with which the binding instance is associated.  Will be C{None} for top-level elements
        @type element_use: L{basis.element}
        @param attrs: The XML attributes associated with the element
        @type attrs: C{xml.sax.xmlreader.Attributes}
        @return: The generated binding instance, or C{None} if creation is delayed
        """
        self.__delayedConstructor = None
        self.__elementUse = element_use
        self.__attributes = attrs
        if type_class._IsSimpleTypeContent():
            self.__delayedConstructor = new_object_factory
            self.__attributes = attrs
        else:
            self.__constructElement(new_object_factory, attrs)
        return self.__bindingObject

    __NonElementContent = 1
    __ElementContent = 2

    def addContent (self, content):
        """Add the given text as non-element content of the current element.
        @type content: C{unicode} or C{str}
        @return: C{self}
        """
        self.__content.append( (content, None, False) )
        return self

    def endElement (self):
        """Perform any end-of-element processing.

        For simple type instances, this creates the binding instance.
        @return: The generated binding instance
        """
        if self.__delayedConstructor is not None:
            self.__constructElement(self.__delayedConstructor, self.__attributes, [ _c[0] for _c in self.__content ])
        else:
            #print 'Extending %s by content %s' % (self.__bindingObject, self.__content,)
            [ self.__bindingObject.append(*_c) for _c in self.__content ]
        if self.__parentState is not None:
            self.__parentState.__content.append( (self.__bindingObject, self.__elementUse) )
        return self.__bindingObject

class PyXBSAXHandler (xml.sax.handler.ContentHandler):
    """A SAX handler class which generates a binding instance for a document
    through a streaming parser.

    An example of using this to parse the document held in the string C{xmls} is::

      import pyxb.binding.saxer
      import StringIO

      saxer = pyxb.binding.saxer.make_parser()
      handler = saxer.getContentHandler()
      saxer.parse(StringIO.StringIO(xml))
      instance = handler.rootObject()

    """

    # Whether invocation of handler methods should be traced
    __trace = False

    # The namespace to use when processing a document with an absent default
    # namespace.
    __fallbackNamespace = None

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
        element in the document

        @return: An instance of L{basis._TypeBinding_mixin} (most usually a
        L{basis.complexTypeDefinition}."""
        return self.__rootObject
    __rootObject = None

    def reset (self):
        """Reset the state of the handler in preparation for processing a new
        document.

        @return: C{self}
        """
        self.__namespaceContext = pyxb.namespace.resolution.NamespaceContext(default_namespace=self.__fallbackNamespace)
        self.__nextNamespaceContext = None
        self.__locator = None
        self.__elementState = _SAXElementState(self.__namespaceContext, None)
        self.__elementStateStack = []
        self.__rootObject = None
        return self

    def __init__ (self, fallback_namespace=None):
        self.__fallbackNamespace = fallback_namespace
        self.reset()

    def namespaceContext (self):
        """Return the namespace context used for QName resolution within the
        current element.

        @return: An instance of L{pyxb.namespace.resolution.NamespaceContext}"""
        return self.__namespaceContext
    
    # If there's a new namespace waiting to be used, make it the
    # current namespace.  Return the current namespace.
    def __updateNamespaceContext (self):
        if self.__nextNamespaceContext is not None:
            self.__namespaceContext = self.__nextNamespaceContext
            self.__nextNamespaceContext = None
        return self.__namespaceContext

    def startDocument (self):
        """Process the start of a document.

        This resets this handler for a new document.
        """
        if self.__trace:
            print 'startDocument'
        self.reset()

    def setDocumentLocator (self, locator):
        """Save the locator object."""
        self.__locator = locator
        if self.__trace:
            print 'setDocumentlocator'
        return self

    def startPrefixMapping (self, prefix, uri):
        """Implement base class method.

        @note: For this to be invoked, the C{feature_namespaces} feature must
        be enabled in the SAX parser."""
        self.__updateNamespaceContext().processXMLNS(prefix, uri)
        if self.__trace:
            print 'startPrefixMapping %s %s' % (prefix, uri)
        return self

    # The NamespaceContext management does not require any action upon
    # leaving the scope of a namespace directive.
    #def endPrefixMapping (self, prefix):
    #    pass

    def startElementNS (self, name, qname, attrs):
        if self.__trace:
            print 'startElementNS %s %s %s' % (name, qname, attrs)

        # Get the context to be used for this element, and create a
        # new context for the next contained element to be found.
        ns_ctx = self.__updateNamespaceContext()
        self.__nextNamespaceContext = pyxb.namespace.resolution.NamespaceContext(parent_context=ns_ctx)

        # Get the element name including namespace information.
        name_en = pyxb.namespace.ExpandedName(name, fallback_namespace=self.__fallbackNamespace)

        # Save the state of the enclosing element, and create a new
        # state for this element.
        parent_state = self.__elementState
        self.__elementStateStack.append(self.__elementState)
        self.__elementState = this_state = _SAXElementState(ns_ctx, parent_state)

        # Start knowing nothing
        type_class = None

        # Process an xsi:type attribute, if present
        if attrs.has_key(self.__XSITypeTuple):
            xsi_type = attrs.getValue(self.__XSITypeTuple)
            type_class = ns_ctx.interpretQName(xsi_type).typeBinding()

        # Resolve the element within the appropriate context.  Note
        # that global elements have no use, only the binding.
        if parent_state.enclosingCTD() is not None:
            (element_binding, element_use) = parent_state.enclosingCTD()._ElementBindingUseForName(name_en)
        else:
            element_use = None
            element_binding = name_en.elementBinding()

        # Non-root elements should have an element use, from which we can
        # extract the binding.  Don't throw away substitution group bindings.
        if (element_use is not None) and (element_binding is None):
            assert self.__rootObject is not None
            element_binding = element_use.elementBinding()
            assert element_binding is not None

        # Get the factory method for the binding type for the element instance
        if type_class is not None:
            # @todo: validate xsi:type against abstract
            new_object_factory = type_class.Factory
        else:
            # Invoke binding __call__ method not Factory, so can check for
            # abstract elements.
            assert element_binding is not None
            element_binding = element_binding.elementForName(name)
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
        if self.__trace:
            print 'endElementNS %s %s' % (name, qname)

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
        if self.__trace:
            print 'characters "%s"' % (content,)
        self.__elementState.addContent(content)

    def ignorableWhitespace (self, whitespace):
        """Save whitespace as content too."""
        if self.__trace:
            print 'ignorableWhitespace length %d' % (len(whitespace),)
        self.__elementState.addContent(whitespace)

def make_parser (*args, **kw):
    """Extend C{xml.sax.make_parser} to configure the parser the way we
    need it:

      - C{feature_namespaces} is set to C{True} so we process xmlns
        directives properly
      - C{feature_namespace_prefixes} is set to C{False} so we don't get
        prefixes encoded into our names (probably redundant with the above but
        still...)
      - The content handler is set to a fresh instance of L{PyXBSAXHandler}.

    All arguments and keywords not documented here are passed to C{xml.sax.make_parser}.

    @keyword fallback_namespace: The namespace to use for lookups of
    unqualified names in absent namespaces.
    @type fallback_namespace: L{pyxb.namespace.Namespace}
    """
    fallback_namespace = kw.pop('fallback_namespace', None)
    parser = xml.sax.make_parser(*args, **kw)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, False)
    parser.setContentHandler(PyXBSAXHandler(fallback_namespace=fallback_namespace))
    return parser

## Local Variables:
## fill-column:78
## End:
    
