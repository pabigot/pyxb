from PyWXSB.exceptions_ import *
import XMLSchema as xs
import xml.dom as dom
from xml.dom import minidom
import domutils

class PyWXSB_element (object):
    """Base class for any Python class that serves as the binding to an XMLSchema element.

    The subclass must define a class variable _TypeDefinition which is
    a reference to the _PST_mixin or PyWXSB_complexTypeDefinition
    subclass that serves as the information holder for the element.

    Most actions on instances of these clases are delegated to the
    underlying content object.
    """

    # Reference to the instance of the underlying type
    __content = None
    
    # Assign to the content field.  This may manipulate the assigned
    # value if doing so results in a cleaner interface for the user.
    def __setContent (self, content):
        self.__content = content
        if content is not None:
            if issubclass(self._TypeDefinition, PyWXSB_CTD_simple):
                self.__content = self.content().content()
        return self

    def __init__ (self, *args, **kw):
        """Create a new element.

        This sets the content to be an instance created by invoking
        the Factory method of the element type definition.
        
        If the element is a complex type with simple content, the
        value of the content is dereferenced once.
        """
        self.__setContent(self._TypeDefinition.Factory(*args, **kw))
        
    # Delegate unrecognized attribute accesses to the content.
    def __getattr__ (self, name):
        return getattr(self.__content, name)

    # @todo What if we need to deconflict "content" from something
    # that's in the underlying type?
    def content (self): return self.__content
    
    @classmethod
    def CreateFromDOM (cls, node):
        rv = cls()
        rv.__setContent(cls._TypeDefinition.CreateFromDOM(node))
        return rv

    def toDOM (self):
        return self.content().toDOM(self._XsdName)

class AttributeUse (object):
    """A helper class that encapsulates everything we need to know about an attribute."""
    __tag = None       # Unicode XML tag @todo not including namespace
    __dataType = None  # PST datatype
    __value = None     # THe current value of the attribute
    __defaultValue = None       # Unicode default value, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear
    __provided = False          # If True, attribute was set from DOM or user

    def __init__ (self, tag, data_type, default_value=None, fixed=False, required=False, prohibited=False):
        self.__tag = tag
        self.__dataType = data_type
        self.__defaultValue = default_value
        self.__fixed = fixed
        self.__required = required
        self.__prohibited = prohibited

    def setFromDOM (self, node):
        unicode_value = self.__defaultValue
        if isinstance(node, dom.Node):
            if node.hasAttribute(self.__tag):
                if self.__prohibited:
                    raise ProhibitedAttributeError('Prohibited attribute %s found' % (self.__tag,))
                unicode_value = node.getAttribute(self.__tag)
            else:
                if self.__required:
                    raise MissingAttributeError('Required attribute %s not found' % (self.__tag,))
        if unicode_value is None:
            # Must be optional and absent
            self.__value = None
        else:
            if self.__fixed and (unicode_value != self.__defaultValue):
                raise AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__tag,))
            self.__value = self.__dataType(unicode_value)
        return self

    def addDOMAttribute (self, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        if self.__provided:
            element.setAttribute(self.__tag, self.__value.xsdLiteral())
        return self

    def value (self):
        """Get the value of the attribute."""
        return self.__value

    def setValue (self, new_value):
        """Set the value of the attribute.

        This validates the value against the data type."""
        if not isinstance(new_value, self.__dataType):
            new_value = self.__dataType(new_value)
        self.__value = new_value
        self.__provided = True
        return self.__value

class PyWXSB_enumeration_mixin (object):
    """Marker in case we need to know that a PST has an enumeration constraint facet."""
    pass

class PyWXSB_complexTypeDefinition (object):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType.
    """
    def _setAttributesFromDOM (self, node):
        for au in self._AttributeUses:
            au.setFromDOM(node)
        return self

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeUses:
            au.addDOMAttribute(element)
        return element

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with empty content."""

    @classmethod
    def Factory (cls, *args, **kw):
        return cls(*args, **kw)._setAttributesFromDOM(None)

    @classmethod
    def CreateFromDOM (cls, node):
        """Create a raw instance, and set attributes from the DOM node."""
        return cls()._setAttributesFromDOM(node)

    def toDOM (self, element_tag):
        """Create a DOM element with the given tag holding the content of this instance."""
        doc = minidom.getDOMImplementation().createDocument(None, element_tag, None)
        return self._setDOMFromAttributes(doc.documentElement)

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with simple content."""

    __content = None
    def content (self):
        return self.__content

    def __init__ (self, *args, **kw):
        self.__content = self._TypeDefinition.Factory(*args, **kw)

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    @classmethod
    def CreateFromDOM (cls, node):
        """Create an instance from the node content, and set the attributes."""
        return cls(domutils.ExtractTextContent(node))._setAttributesFromDOM(node)

class PyWXSB_CTD_mixed (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with mixed content."""
    pass

class PyWXSB_CTD_element (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with element-only content."""
    pass
