xml_file = 'examples/xsdprimer/ipo.xml'

import sys
import xml.sax
import xml.sax.handler
import pyxb.namespace
import ipo

class PyXBSAXHandler (xml.sax.handler.ContentHandler):
    __nextNamespaceContext = None
    __namespaceContext = None
    __XSITypeTuple = pyxb.namespace.XMLSchema_instance.createExpandedName('type').uriTuple()

    def _updateNamespaceContext (self):
        if self.__nextNamespaceContext is not None:
            self.__namespaceContext = self.__nextNamespaceContext
            self.__nextNamespaceContext = None
        return self.__namespaceContext

    def reset (self):
        self.__nextNamespaceContext = None
        self.__namespaceContext = pyxb.namespace.NamespaceContext()

    def __init__ (self):
        self.reset()

    def startDocument (self):
        self.reset()

    def setDocumentLocator (self, locator):
        print 'setDocumentLocator %s' % (locator,)

    def namespaceContext (self):
        return self.__namespaceContext
    
    def startPrefixMapping (self, prefix, uri):
        print 'Begin prefix %s uri %s' % (prefix, uri)
        self._updateNamespaceContext().processXMLNS(prefix, uri)
    def endPrefixMapping (self, prefix):
        print 'End prefix %s' % (prefix,)

    __rootObject = None
    __contextStack = []

    __bindingObject = None
    __bindingStack = []
    __enclosingCTD = None
    __ctdStack = []
    __elementUseStack = []

    def rootObject (self):
        return self.__rootObject

    def startElementNS (self, name, qname, attrs):
        name_en = pyxb.namespace.ExpandedName(name)
        ns_ctx = self._updateNamespaceContext()
        self.__contextStack.append(ns_ctx)

        self.__nextNamespaceContext = pyxb.namespace.NamespaceContext(parent_context=ns_ctx)

        print " ".join([ '%s=%s' % (_v, _ns.uri()) for (_v, _ns) in self.__namespaceContext.inScopeNamespaces().items() ])
        print 'Start element %s with %d attrs' % (pyxb.namespace.ExpandedName(name), len(attrs))
        for attr_name in attrs.getNames():
            attr_en = pyxb.namespace.ExpandedName(attr_name)
            attr_val = attrs.getValue(attr_name)
            print '  %s %s' % (attr_en, attr_val)
        type_class = element_use = element_binding = None
        if attrs.has_key(self.__XSITypeTuple):
            xsi_type = attrs.getValue(self.__XSITypeTuple)
            type_class = ns_ctx.interpretQName(xsi_type).typeBinding()
        if self.__enclosingCTD is not None:
            element_use = self.__enclosingCTD._UseForTag(name_en)
        else:
            element_binding = name_en.elementBinding()
        if element_use is not None:
            assert self.__rootObject is not None
            element_binding = element_use.elementBinding()

        self.__bindingStack.append(self.__bindingObject)
        self.__elementUseStack.append(element_use)
        if type_class is not None:
            new_object = type_class.Factory(_validate_constraints=False)
        else:
            assert element_binding is not None
            new_object = element_binding(_validate_constraints=False)

        if element_use is None:
            assert self.__rootObject is None
            self.__rootObject = new_object
        else:
            element_use.setOrAppend(self.__bindingObject, new_object)
        self.__bindingObject = new_object

        if isinstance(self.__bindingObject, pyxb.binding.basis.complexTypeDefinition):
            self.__ctdStack.append(self.__enclosingCTD)
            self.__enclosingCTD = self.__bindingObject

    def endElementNS (self, name, qname):
        element_use = self.__elementUseStack.pop()
        if isinstance(self.__bindingObject, pyxb.binding.basis.simpleTypeDefinition):
            # Note: Not doing this for CTDs, takes too long
            self.__bindingObject.validateBinding()

        if self.__enclosingCTD == self.__bindingObject:
            self.__enclosingCTD = self.__ctdStack.pop()
        self.__bindingObject = self.__bindingStack.pop()
        self.__nextNamespaceContext = None
        self.__namespaceContext = self.__contextStack.pop()
        print 'End element %s' % (pyxb.namespace.ExpandedName(name),)

    def characters (self, content):
        print 'Content %s' % (content,)
        if isinstance(self.__bindingObject, pyxb.binding.basis.simpleTypeDefinition):
            pass
        else:
            self.__bindingObject.append(content)

    def ignorableWhitespace (self, whitespace):
        print 'Whitespace %s' % (whitespace,)
        pass

def ShowOrder (order):
    print '%s is sending %s %d thing(s):' % (order.billTo().name(), order.shipTo().name(), len(order.items().item()))
    for item in order.items().item():
        print '  Quantity %d of %s at $%s' % (item.quantity(), item.productName(), item.USPrice())

if False:
    import pyxb.utils.domutils
    xmld = pyxb.utils.domutils.StringToDOM(file(xml_file).read())
    dom_value = ipo.CreateFromDOM(xmld.documentElement)
    ShowOrder(dom_value)

saxer = xml.sax.make_parser()
# Without this, the NS handlers aren't invoked
saxer.setFeature(xml.sax.handler.feature_namespaces, True)
saxer.setFeature(xml.sax.handler.feature_namespace_prefixes, False)

handler = PyXBSAXHandler()
saxer.setContentHandler(handler)
saxer.parse(file(xml_file))
ShowOrder(handler.rootObject())
