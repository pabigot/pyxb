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

"""This module contains support for generating bindings from an XML stream
using a SAX parser."""

import xml.sax
import xml.sax.handler
import pyxb.namespace
import pyxb.utils.saxutils
import basis

class _SAXElementState (pyxb.utils.saxutils.SAXElementState):
    """State corresponding to processing a given element."""

    # An expanded name corresponding to xsi:nil
    __XSINilTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('nil').uriTuple()

    # The binding object being created for this element.  When the
    # element type has simple content, the binding instance cannot be
    # created until the end of the element has been reached and the
    # content of the element has been processed accumulated for use in
    # the instance constructor.  When the element type has complex
    # content, the binding instance must be created at the start of
    # the element, so contained elements can be properly stored.
    __bindingObject = None

    # The nearest enclosing complex type definition
    def enclosingCTD (self):
        """The nearest enclosing complex type definition, as used for
        resolving local element/attribute names.

        @return: An instance of L{basis.complexTypeDefinition}, or C{None} if
        the element is top-level
        """
        return self.__enclosingCTD
    __enclosingCTD = None

    # The factory that is called to create a binding instance for this
    # element; None if the binding instance was created at the start
    # of the element.
    __delayedConstructor = None

    # An xml.sax.xmlreader.Attributes instance providing the
    # attributes for the element.
    __attributes = None
    
    def __init__ (self, **kw):
        super(_SAXElementState, self).__init__(**kw)
        self.__bindingObject = None
        parent_state = self.parentState()
        if isinstance(parent_state, _SAXElementState):
            self.__enclosingCTD = parent_state.enclosingCTD()

    def setEnclosingCTD (self, enclosing_ctd):
        """Set the enclosing complex type definition for this element.

        @param enclosing_ctd: The scope for a local element.
        @type enclosing_ctd: L{basis.complexTypeDefinition}
        @return: C{self}
        """
        self.__enclosingCTD = enclosing_ctd

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
            # NB: attrs implements the SAX AttributesNS interface, meaning
            # that names are pairs of (namespaceURI, localName), just like we
            # want them to be.
            for attr_name in self.__attributes.getNames():
                attr_en = pyxb.namespace.ExpandedName(attr_name)
                au = self.__bindingObject._AttributeMap.get(attr_en)
                if au is not None:
                    au.set(self.__bindingObject, attrs.getValue(attr_name))
            self.__bindingObject._validateAttributes()
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

    def endElement (self):
        """Perform any end-of-element processing.

        For simple type instances, this creates the binding instance.
        @return: The generated binding instance
        """
        if self.__delayedConstructor is not None:
            args = []
            for (content, element_use, maybe_element) in self.__content:
                assert not maybe_element
                assert element_use is None
                assert isinstance(content, basestring)
                args.append(content)
            assert 1 >= len(args), 'Unexpected STD content %s' % (args,)
            self.__constructElement(self.__delayedConstructor, self.__attributes, args)
        else:
            #print 'Extending %s by content %s' % (self.__bindingObject, self.__content,)
            for (content, element_use, maybe_element) in self.__content:
                self.__bindingObject.append(content, element_use, maybe_element)
        parent_state = self.parentState()
        if parent_state is not None:
            parent_state.addElementContent(self.__bindingObject, self.__elementUse)
        return self.__bindingObject

class PyXBSAXHandler (pyxb.utils.saxutils.BaseSAXHandler):
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

    # An expanded name corresponding to xsi:type
    __XSITypeTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('type').uriTuple()

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
        super(PyXBSAXHandler, self).reset()
        self.__rootObject = None
        return self

    def __init__ (self, **kw):
        kw.setdefault('element_state_constructor', _SAXElementState)
        super(PyXBSAXHandler, self).__init__(**kw)
        self.reset()

    def startElementNS (self, name, qname, attrs):
        (this_state, parent_state, ns_ctx, name_en) = super(PyXBSAXHandler, self).startElementNS(name, qname, attrs)

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
        # extract the binding.  (Keep any current binding, since it may be a
        # member of a substitution group.)
        if (element_use is not None) and (element_binding is None):
            assert self.__rootObject is not None
            element_binding = element_use.elementBinding()
            assert element_binding is not None

        # Get the factory method for the binding type for the element instance
        if type_class is not None:
            # @todo: validate xsi:type against abstract
            new_object_factory = type_class.Factory
        elif element_binding is None:
            raise pyxb.UnrecognizedElementError('Unable to locate element %s' % (name_en,))
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
        this_state = super(PyXBSAXHandler, self).endElementNS(name, qname)

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

    @keyword location_base: An object to be recorded as the location from
    which XML was consumed.
    """
    kw.setdefault('content_handler_constructor', PyXBSAXHandler)
    return pyxb.utils.saxutils.make_parser(*args, **kw)

## Local Variables:
## fill-column:78
## End:
    
