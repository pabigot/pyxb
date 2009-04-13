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
    __realContent = None

    # Reference to the instance of the underlying type
    __content = None
    
    # Assign to the content field.  This may manipulate the assigned
    # value if doing so results in a cleaner interface for the user.
    def __setContent (self, content):
        self.__realContent = content
        self.__content = self.__realContent
        if content is not None:
            if issubclass(self._TypeDefinition, PyWXSB_CTD_simple):
                self.__content = self.__realContent.content()
        return self

    def __init__ (self, *args, **kw):
        """Create a new element.

        This sets the content to be an instance created by invoking
        the Factory method of the element type definition.
        
        If the element is a complex type with simple content, the
        value of the content() is dereferenced once, as a convenience.
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
        return self.__realContent.toDOM(self._XsdName)

class AttributeUse (object):
    """A helper class that encapsulates everything we need to know about an attribute."""
    __tag = None       # Unicode XML tag @todo not including namespace
    __valueAttributeName = None # Private attribute used in instances to hold the attribute value
    __dataType = None  # PST datatype
    __defaultValue = None       # Unicode default value, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, tag, value_attribute_name, data_type, default_value=None, fixed=False, required=False, prohibited=False):
        self.__tag = tag
        self.__valueAttributeName = value_attribute_name
        self.__dataType = data_type
        self.__defaultValue = default_value
        self.__fixed = fixed
        self.__required = required
        self.__prohibited = prohibited

    def __getValue (self, cdt_instance):
        return getattr(cdt_instance, self.__valueAttributeName, (False, None))

    def __getProvided (self, cdt_instance):
        return self.__getValue(cdt_instance)[0]

    def value (self, cdt_instance):
        """Get the value of the attribute."""
        return self.__getValue(cdt_instance)[1]

    def __setValue (self, cdt_instance, new_value, provided):
        return setattr(cdt_instance, self.__valueAttributeName, (provided, new_value))

    def setFromDOM (self, cdt_instance, node):
        unicode_value = self.__defaultValue
        provided = False
        if isinstance(node, dom.Node):
            if node.hasAttribute(self.__tag):
                if self.__prohibited:
                    raise ProhibitedAttributeError('Prohibited attribute %s found' % (self.__tag,))
                unicode_value = node.getAttribute(self.__tag)
                provided = True
            else:
                if self.__required:
                    raise MissingAttributeError('Required attribute %s not found' % (self.__tag,))
        if unicode_value is None:
            # Must be optional and absent
            self.__setValue(cdt_instance, None, False)
        else:
            if self.__fixed and (unicode_value != self.__defaultValue):
                raise AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__tag,))
            # NB: Do not set provided here; this may be the default
            self.__setValue(cdt_instance, self.__dataType(unicode_value), provided)
        return self

    def addDOMAttribute (self, cdt_instance, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        ( provided, value ) = self.__getValue(cdt_instance)
        if provided:
            assert value is not None
            element.setAttribute(self.__tag, value.xsdLiteral())
        return self

    def setValue (self, cdt_instance, new_value):
        """Set the value of the attribute.

        This validates the value against the data type."""
        assert new_value is not None
        if not isinstance(new_value, self.__dataType):
            new_value = self.__dataType(new_value)
        self.__setValue(cdt_instance, new_value, True)
        return new_value

class PyWXSB_enumeration_mixin (object):
    """Marker in case we need to know that a PST has an enumeration constraint facet."""
    pass

class PyWXSB_complexTypeDefinition (object):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType.
    """
    def _setAttributesFromDOM (self, node):
        for au in self._AttributeUses:
            au.setFromDOM(self, node)
        return self

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeUses:
            au.addDOMAttribute(self, element)
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

    def toDOM (self, element_tag):
        """Create a DOM element with the given tag holding the content of this instance."""
        doc = minidom.getDOMImplementation().createDocument(None, element_tag, None)
        doc.documentElement.appendChild(doc.createTextNode(self.content().xsdLiteral()))
        return self._setDOMFromAttributes(doc.documentElement)

class PyWXSB_CTD_mixed (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with mixed content."""
    pass

class Particle (object):
    """Record defining the structure and number of an XML object.
    This is a min and max count associated with a
    ModelGroup, ElementDeclaration, or Wildcard."""
    # The minimum number of times the term may appear.
    __minOccurs = 1
    def minOccurs (self):
        """The minimum number of times the term may appear.

        Defaults to 1."""
        return self.__minOccurs

    # Upper limit on number of times the term may appear.
    __maxOccurs = 1
    def maxOccurs (self):
        """Upper limit on number of times the term may appear.

        If None, the term may appear any number of times; otherwise,
        this is an integral value indicating the maximum number of times
        the term may appear.  The default value is 1; the value, unless
        None, must always be at least minOccurs().
        """
        return self.__maxOccurs

    # A reference to a ModelGroup, WildCard, or ElementDeclaration
    __term = None
    def term (self):
        """A reference to a ModelGroup, Wildcard, or ElementDeclaration."""
        return self.__term

    def isPlural (self):
        """Return true iff the term might appear multiple times."""
        if (self.maxOccurs() is None) or 1 < self.maxOccurs():
            return True
        return self.term().isPlural()

    def __init__ (self, min_occurs, max_occurs, term):
        self.__minOccurs = min_occurs
        self.__maxOccurs = max_occurs
        self.__term = term

class PyWXSB_CTD_element (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with element-only content."""

    # The Particle instance used to represent data for this type
    __content = None

    pass
