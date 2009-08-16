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

"""This module contains support for processing XML using a SAX parser.

In particular, it provides a base content handler class that maintains
namespace context and element state in a stack; and a base element
state class which records the location of the element in the stream.
These classes are extended for specific parsing needs (e.g.,
L{pyxb.binding.saxer}).
"""

import xml.sax
import xml.sax.handler
import pyxb.namespace

class TracingSAXHandler (xml.sax.handler.ContentHandler):
    """A SAX handler class which prints each method invocation.
    """

    # Whether invocation of handler methods should be traced
    __trace = False

    def setDocumentLocator (self, locator):
        print 'setDocumentLocator %s' % (locator,)

    def startDocument (self):
        print 'startDocument'

    def startPrefixMapping (self, prefix, uri):
        print 'startPrefixMapping %s %s' % (prefix, uri)

    def endPrefixMapping (self, prefix):
        print 'endPrefixMapping %s' % (prefix,)

    def startElementNS (self, name, qname, attrs):
        print 'startElementNS %s %s' % (name, qname)

    def endElementNS (self, name, qname):
        print 'endElementNS %s %s' % (name, qname)

    def characters (self, content):
        print 'characters %s' % (content,)

    def ignorableWhitespace (self, whitespace):
        print 'ignorableWhitespace len %d' % (len(whitespace),)

    def processingInstruction (self, data):
        print 'processingInstruction %s' % (data,)

class SAXElementState (object):
    """State corresponding to processing a given element with the SAX
    model."""

    # Reference to the SAXElementState of the element enclosing this one
    def parentState (self):
        return self.__parentState
    __parentState = None

    # The pyxb.namespace.resolution.NamespaceContext used for this binding
    def namespaceContext (self):
        return self.__namespaceContext
    __namespaceContext = None

    # The expanded name of the element
    def expandedName (self):
        return self.__expandedName
    __expandedName = None

    def location (self):
        return self.__location
    __location = None

    # An accumulation of content to be supplied to the content model when the
    # element end is reached.  This is a list, with each member being
    # (content, element_use, maybe_element): content is text or a binding
    # instance; element_use is None or the ElementUse instance used to create
    # the content; and maybe_element is True iff the content is non-content
    # text.
    def content (self):
        return self.__content
    __content = None

    def __init__ (self, **kw):
        self.__expandedName = kw.get('expanded_name', None)
        self.__namespaceContext = kw['namespace_context']
        self.__parentState = kw.get('parent_state', None)
        self.__location = kw.get('location', None)
        self.__content = []

    def addTextContent (self, content):
        """Add the given text as non-element content of the current element.
        @type content: C{unicode} or C{str}
        @return: C{self}
        """
        self.__content.append( (content, None, False) )

    def addElementContent (self, element, element_use):
        self.__content.append( (element, element_use, True) )

class BaseSAXHandler (xml.sax.handler.ContentHandler, object):
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

    def locationBase (self):
        return self.__locationBase
    __locationBase = None

    __elementStateConstructor = None

    # The namespace to use when processing a document with an absent default
    # namespace.
    __fallbackNamespace = None

    # The namespace context that will be in effect at the start of the
    # next element.  One of these is allocated at the start of each
    # element; it moves to become the current namespace upon receipt
    # of either the next element start or a namespace directive that
    # will apply at that element start.
    __nextNamespaceContext = None

    # The namespace context that is in effect for this element.
    def namespaceContext (self):
        """Return the namespace context used for QName resolution within the
        current element.

        @return: An instance of L{pyxb.namespace.resolution.NamespaceContext}"""
        return self.__namespaceContext
    __namespaceContext = None

    # A SAX locator object.  @todo: Figure out how to associate the
    # location information with the binding objects.
    __locator = None

    # The state for the element currently being processed
    def elementState (self):
        return self.__elementState
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
        self.__elementState = self.__elementStateConstructor(namespace_context=self.__namespaceContext)
        self.__elementStateStack = []
        return self

    def __init__ (self, **kw):
        self.__fallbackNamespace = kw.pop('fallback_namespace', None)
        self.__elementStateConstructor = kw.pop('element_state_constructor', SAXElementState)
        self.__locationBase = kw.pop('location_base', None)
        self.reset()

    # If there's a new namespace waiting to be used, make it the
    # current namespace.  Return the current namespace.
    def __updateNamespaceContext (self):
        if self.__nextNamespaceContext is not None:
            self.__namespaceContext = self.__nextNamespaceContext
            self.__nextNamespaceContext = None
        return self.__namespaceContext

    def setDocumentLocator (self, locator):
        """Save the locator object."""
        self.__locator = locator

    def startDocument (self):
        """Process the start of a document.

        This resets this handler for a new document.
        """
        self.reset()

    def startPrefixMapping (self, prefix, uri):
        """Implement base class method.

        @note: For this to be invoked, the C{feature_namespaces} feature must
        be enabled in the SAX parser."""
        self.__updateNamespaceContext().processXMLNS(prefix, uri)

    # The NamespaceContext management does not require any action upon
    # leaving the scope of a namespace directive.
    #def endPrefixMapping (self, prefix):
    #    pass

    def startElementNS (self, name, qname, attrs):
        self.__flushPendingText()

        # Get the context to be used for this element, and create a
        # new context for the next contained element to be found.
        ns_ctx = self.__updateNamespaceContext()
        self.__nextNamespaceContext = pyxb.namespace.resolution.NamespaceContext(parent_context=ns_ctx)

        # Get the element name including namespace information.
        expanded_name = pyxb.namespace.ExpandedName(name, fallback_namespace=self.__fallbackNamespace)

        # Save the state of the enclosing element, and create a new
        # state for this element.
        parent_state = self.__elementState
        location = None
        if self.__locator is not None:
            location = (self.__locationBase, self.__locator.getLineNumber(), self.__locator.getColumnNumber())
        self.__elementStateStack.append(self.__elementState)
        self.__elementState = this_state = self.__elementStateConstructor(expanded_name=expanded_name,
                                                                          namespace_context=ns_ctx,
                                                                          parent_state=parent_state,
                                                                          location=location)
        return (this_state, parent_state, ns_ctx, expanded_name)

    def endElementNS (self, name, qname):
        self.__flushPendingText()

        # Save the state of this element, and restore the state for
        # the parent to which we are returning.
        this_state = self.__elementState
        parent_state = self.__elementState = self.__elementStateStack.pop()

        return this_state

    __pendingText = None
    def __flushPendingText (self):
        if self.__pendingText:
            self.__elementState.addTextContent(''.join(self.__pendingText))
        self.__pendingText = []

    def characters (self, content):
        """Save the text as content"""
        self.__pendingText.append(content)

    def ignorableWhitespace (self, whitespace):
        """Save whitespace as content too."""
        self.__pendingText.append(content)

    def processingInstruction (self, data):
        self.__flushPendingText()

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

    @keyword content_handler: The content handler instance for the
    parser to use.  If not provided, an instance of L{BaseSAXHandler}
    is created and used.
    @type content_handler: C{xml.sax.handler.ContentHandler}
    """
    content_handler_constructor = kw.pop('content_handler_constructor', BaseSAXHandler)
    content_handler = kw.pop('content_handler', None)
    if content_handler is None:
        content_handler = content_handler_constructor(**kw)
    parser = xml.sax.make_parser(*args)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, False)
    parser.setContentHandler(content_handler)
    return parser

if '__main__' == __name__:
    import xml.dom.pulldom
    import pyxb.utils.domutils as domutils
    import time
    import lxml.sax
    import lxml.etree
    import StringIO
    import sys

    Handler = BaseSAXHandler
    xml_file = '/home/pab/pyxb/dev/examples/tmsxtvd/tmsdatadirect_sample.xml'
    if 1 < len(sys.argv):
        xml_file = sys.argv[1]
    xmls = open(xml_file).read()

    dt1 = time.time()
    dt2 = time.time()
    dom = domutils.StringToDOM(xmls)
    dt3 = time.time()

    st1 = time.time()
    sh = Handler()
    saxer = make_parser(content_handler=sh)
    st2 = time.time()
    saxer.parse(StringIO.StringIO(xmls))
    st3 = time.time()

    pt1 = time.time()
    saxer = make_parser()
    h = saxer.getContentHandler()
    pt2 = time.time()
    saxer.parse(StringIO.StringIO(xmls))
    pt3 = time.time()

    lst1 = time.time()
    tree = lxml.etree.fromstring(xmls)
    lst2 = time.time()
    lsh = Handler()
    lxml.sax.saxify(tree, lsh)
    lst3 = time.time()

    ldt1 = time.time()
    tree = lxml.etree.fromstring(xmls)
    ldt2 = time.time()
    ldh = xml.dom.pulldom.SAX2DOM()
    lxml.sax.saxify(tree, ldh)
    ldt3 = time.time()

    print 'PyXB DOM-based read %f, parse %f, total %f' % (dt2-dt1, dt3-dt2, dt3-dt1)
    print 'SAX-based create %f, parse %f, total %f' % (st2-st1, st3-st2, st3-st1)
    print 'PyXB SAX-based create %f, parse %f, total %f' % (pt2-pt1, pt3-pt2, pt3-pt1)
    print 'LXML-based SAX tree %f, parse %f, total %f' % (lst2-lst1, lst3-lst2, lst3-lst1)
    print 'LXML-based DOM tree %f, parse %f, total %f' % (ldt2-ldt1, ldt3-ldt2, ldt3-ldt1)

## Local Variables:
## fill-column:78
## End:
        
    
