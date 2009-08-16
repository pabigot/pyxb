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

import xml.dom
import saxutils
import StringIO
import pyxb.namespace

def _DumpDOM (n, depth=0):
    pfx = ' ' * depth
    if (xml.dom.Node.ELEMENT_NODE == n.nodeType):
        print '%sElement %s %s with %d children INS %s' % (pfx, n, pyxb.namespace.ExpandedName(n.name), len(n.childNodes), pyxb.namespace.resolution.NamespaceContext.GetNodeContext(n).inScopeNamespaces())
        for (k, v) in n.attributes.items():
            print '%s %s=%s' % (pfx, pyxb.namespace.ExpandedName(k), v)
        for cn in n.childNodes:
            _DumpDOM(cn, depth+1)
    elif (xml.dom.Node.TEXT_NODE == n.nodeType):
        #print '%sText "%s"' % (pfx, n.value)
        pass
    else:
        print 'UNRECOGNIZED %s' % (n.nodeType,)

class _DOMSAXHandler (saxutils.BaseSAXHandler):
    def document (self):
        return self.__document
    __document = None
    
    def startDocument (self):
        self.__document = Document(namespace_context=self.namespaceContext())

    def endDocument (self):
        content = self.elementState().content()
        if 0 < len(content):
            ( content, element_use, maybe_element ) = content[0]
            self.__document.appendChild(content)
            #_DumpDOM(content)

    def startElementNS (self, name, qname, attrs):
        (this_state, parent_state, ns_ctx, name_en) = super(_DOMSAXHandler, self).startElementNS(name, qname, attrs)
        this_state.__attributes = NamedNodeMap()
        for name in attrs.getQNames():
            attr_en = pyxb.namespace.ExpandedName(name)
            value = attrs.getValueByQName(name)
            this_state.__attributes._addItem(Attr(expanded_name=attr_en, namespace_context=ns_ctx, value=value))

    def endElementNS (self, name, qname):
        this_state = super(_DOMSAXHandler, self).endElementNS(name, qname)
        ns_ctx = this_state.namespaceContext()
        element = Element(namespace_context=ns_ctx, expanded_name=this_state.expandedName(), attributes=this_state.__attributes)
        for ( content, element_use, maybe_element ) in this_state.content():
            if isinstance(content, Node):
                element.appendChild(content)
            else:
                element.appendChild(Text(content, namespace_context=ns_ctx))
        parent_state = this_state.parentState()
        parent_state.addElementContent(element, None)
        #print '%s %s has %d children' % (element.namespaceURI, element.localName, len(element.childNodes))

def parse (stream, **kw):
    kw['content_handler_constructor'] = _DOMSAXHandler
    saxer = saxutils.make_parser(**kw)
    handler = saxer.getContentHandler()
    saxer.parse(stream)
    return handler.document()

def parseString (text, **kw):
    return parse(StringIO.StringIO(text), **kw)

class Node (xml.dom.Node, object):
    def __init__ (self, node_type, **kw):
        self.__nodeType = node_type
        self.__parentNode = None
        self.__childNodes = []
        self.__namespaceContext = kw['namespace_context']
        self.__value = kw.get('value')
        self.__attributes = kw.get('attributes')
        expanded_name = kw.get('expanded_name')
        if expanded_name is not None:
            self.__name = expanded_name.uriTuple()
            self.__namespaceURI = expanded_name.namespaceURI()
            self.__localName = expanded_name.localName()
        self.__namespaceContext.setNodeContext(self)

    __name = None
    name = property(lambda _s: _s.__name)
    def _name (self): return self.__name
    nodeName = name
    __namespaceURI = None
    namespaceURI = property(lambda _s: _s.__namespaceURI)
    __localName = None
    localName = property(lambda _s: _s.__localName)
    __value = None
    value = property(lambda _s: _s.__value)

    def __childIfPresent (self, index):
        if 0 < len(self.__childNodes):
            return self.__childNodes[index]
        return None

    def appendChild (self, new_child):
        new_child._setParentNode(self, len(self.__childNodes))
        self.__childNodes.append(new_child)

    def _setParentNode (self, parent_node, index_in_parent):
        self.__parentNode = parent_node
        self.__indexInParent = index_in_parent

    def _setAttributes (self, attributes):
        assert self.__attributes is None
        self.__attributes = attributes
    __attributes = None

    nodeType = property(lambda _s: _s.__nodeType)
    parentNode = property(lambda _s: _s.__parentNode)
    firstChild = property(lambda _s: _s.__childIfPresent(0))
    childNodes = property(lambda _s: _s.__childNodes)
    attributes = property(lambda _s: _s.__attributes)

    def hasAttributeNS (self, ns_uri, local_name):
        return self.getAttributeNodeNS(ns_uri, local_name) is not None

    def getAttributeNodeNS (self, ns_uri, local_name):
        return self.__attributes._getAttr( (ns_uri, local_name) )

class Document (Node):
    def __init__ (self, **kw):
        super(Document, self).__init__(node_type=xml.dom.Node.DOCUMENT_NODE, **kw)

    documentElement = Node.firstChild

class Attr (Node):
    def __init__ (self, **kw):
        super(Attr, self).__init__(node_type=xml.dom.Node.ATTRIBUTE_NODE, **kw)

class NamedNodeMap (dict):
    __members = None

    def __init__ (self):
        super(NamedNodeMap, self).__init__()
        self.__members = []

    length = property(lambda _s: len(_s.__members))
    def item (self, index):
        return self.__members[index]

    def _addItem (self, attr):
        self[attr.name] = attr.value
        assert pyxb.namespace.resolution.NamespaceContext.GetNodeContext(attr) is not None
        self.__members.append(attr)

    def _getAttr (self, name):
        for attr in self.__members:
            if attr.name == name:
                return attr
        return None

class Element (Node):
    def __init__ (self, **kw):
        super(Element, self).__init__(node_type=xml.dom.Node.ELEMENT_NODE, **kw)
        assert self.attributes is not None

class CharacterData (Node):
    pass

class Text (CharacterData):
    def __init__ (self, text, **kw):
        super(Text, self).__init__(value=text, node_type=xml.dom.Node.TEXT_NODE, **kw)

    data = Node.value

if '__main__' == __name__:
    import sys
    xml_file = '/home/pab/pyxb/dev/examples/tmsxtvd/tmsdatadirect_sample.xml'
    if 1 < len(sys.argv):
        xml_file = sys.argv[1]

    doc = parse(file(xml_file))


## Local Variables:
## fill-column:78
## End:
    
