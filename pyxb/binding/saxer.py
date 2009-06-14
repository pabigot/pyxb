import xml.sax
import xml.sax.handler
import pyxb.namespace

class _SAXElementState (object):
    __parentState = None
    namespaceContext = None
    bindingObject = None
    elementUse = None
    enclosingCTD = None
    __content = None

    def __init__ (self, namespace_context, parent_state):
        self.namespaceContext = namespace_context
        self.__parentState = parent_state
        self.bindingObject = None
        self.elementUse = None
        if isinstance(self.__parentState, _SAXElementState):
            self.enclosingCTD = self.__parentState.enclosingCTD
        else:
            self.enclosingCTD = None
        self.__content = []

    def content (self):
        return ''.join(self.__content)

    def __constructElement (self, new_object_factory, attrs, content=None):
        if content is not None:
            self.bindingObject = new_object_factory(content)
        else:
            self.bindingObject = new_object_factory()
        if isinstance(self.bindingObject, pyxb.binding.basis.complexTypeDefinition):
            # @todo: set attributes
            pass
        if self.__elementUse is not None:
            assert self.__parentState is not None
            assert self.__parentState.bindingObject is not None
            self.__elementUse.setOrAppend(self.__parentState.bindingObject, self.bindingObject)
        return self.bindingObject

    def startElement (self, type_class, new_object_factory, element_use, attrs):
        self.__delayedConstructor = None
        self.__elementUse = element_use
        self.__attributes = None
        if type_class._IsSimpleTypeContent():
            self.__delayedConstructor = new_object_factory
            self.__attributes = attrs
        else:
            self.__constructElement(new_object_factory, attrs)
        return self.bindingObject

    def addContent (self, content):
        self.__content.append(content)

    def endElement (self):
        if self.__delayedConstructor is not None:
            self.__constructElement(self.__delayedConstructor, self.__attributes, self.content())
        return self.bindingObject

class PyXBSAXHandler (xml.sax.handler.ContentHandler):
    __XSITypeTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('type').uriTuple()

    __nextNamespaceContext = None
    __namespaceContext = None

    __locator = None
    __elementState = None
    __elementStateStack = []

    def rootObject (self):
        return self.__rootObject
    __rootObject = None

    def reset (self):
        self.__namespaceContext = pyxb.namespace.NamespaceContext()
        self.__nextNamespaceContext = None
        self.__locator = None
        self.__elementState = _SAXElementState(self.__namespaceContext, None)
        self.__elementStateStack = []
        self.__rootObject = None

    def __init__ (self):
        self.reset()

    def startDocument (self):
        self.reset()

    def setDocumentLocator (self, locator):
        self.__locator = locator

    def namespaceContext (self):
        return self.__namespaceContext
    
    def _updateNamespaceContext (self):
        if self.__nextNamespaceContext is not None:
            self.__namespaceContext = self.__nextNamespaceContext
            self.__nextNamespaceContext = None
        return self.__namespaceContext

    def startPrefixMapping (self, prefix, uri):
        self._updateNamespaceContext().processXMLNS(prefix, uri)

    def endPrefixMapping (self, prefix):
        #
        pass

    def startElementNS (self, name, qname, attrs):
        name_en = pyxb.namespace.ExpandedName(name)
        ns_ctx = self._updateNamespaceContext()
        self.__nextNamespaceContext = pyxb.namespace.NamespaceContext(parent_context=ns_ctx)

        # Save the state of the enclosing element, and create a new
        # state for this element.
        parent_state = self.__elementState
        self.__elementStateStack.append(self.__elementState)
        self.__elementState = this_state = _SAXElementState(ns_ctx, parent_state)

        type_class = element_use = element_binding = None

        if attrs.has_key(self.__XSITypeTuple):
            xsi_type = attrs.getValue(self.__XSITypeTuple)
            type_class = ns_ctx.interpretQName(xsi_type).typeBinding()

        # @todo: handle substitution groups
        if parent_state.enclosingCTD is not None:
            element_use = parent_state.enclosingCTD._UseForTag(name_en)
        else:
            element_binding = name_en.elementBinding()

        if element_use is not None:
            assert self.__rootObject is not None
            element_binding = element_use.elementBinding()
            assert element_binding is not None

        if type_class is not None:
            # @todo: validate xsi:type against abstract
            new_object_factory = type_class.Factory
        else:
            assert element_binding is not None
            new_object_factory = element_binding
            type_class = element_binding.typeDefinition()

        assert type_class is not None
        if issubclass(type_class, pyxb.binding.basis.complexTypeDefinition):
            this_state.enclosingCTD = type_class
        else:
            this_state.enclosingCTD = parent_state.enclosingCTD

        binding_object = this_state.startElement(type_class, new_object_factory, element_use, attrs)
        if self.__rootObject is None:
            self.__rootObject = binding_object

    def endElementNS (self, name, qname):
        this_state = self.__elementState
        parent_state = self.__elementState = self.__elementStateStack.pop()

        binding_object = this_state.endElement()
        assert binding_object is not None

        if self.__rootObject is None:
            self.__rootObject = binding_object

    def characters (self, content):
        self.__elementState.addContent(content)

    def ignorableWhitespace (self, whitespace):
        self.__elementState.addContent(whitespace)

def make_parser (*args, **kw):
    parser = xml.sax.make_parser(*args, **kw)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, False)
    parser.setContentHandler(PyXBSAXHandler())
    return parser
