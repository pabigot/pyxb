from PyWXSB.exceptions_ import *
import XMLSchema as xs
import xml.dom as dom
from xml.dom import minidom
import domutils
import utility

class PyWXSB_element (utility._DeconflictSymbols_mixin, object):
    """Base class for any Python class that serves as the binding to an XMLSchema element.

    The subclass must define a class variable _TypeDefinition which is
    a reference to the _PST_mixin or PyWXSB_complexTypeDefinition
    subclass that serves as the information holder for the element.

    Most actions on instances of these clases are delegated to the
    underlying content object.
    """

    # Reference to the instance of the underlying type
    __realContent = None

    # Reference to the instance of the underlying type, or to that
    # type's content if that is a complex type with simple content.
    __content = None
    
    # Symbols that remain the responsibility of this class.  Any
    # symbols in the type from the content are deconflicted by
    # providing an alternative name in the subclass.
    _ReservedSymbols = set([ 'content', 'CreateFromDOM', 'toDOM' ])

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

    def toDOM (self, document=None, parent=None):
        if document is None:
            assert parent is None
            document = minidom.getDOMImplementation().createDocument(None, self._XsdName, None)
            element = document.documentElement
        else:
            assert parent is not None
            element = parent.appendChild(document.createElement(self._XsdName))
        self.__realContent.toDOM(tag=None, document=document, parent=element)
        return element

class AttributeUse (object):
    """A helper class that encapsulates everything we need to know about an attribute."""
    __tag = None       # Unicode XML tag @todo not including namespace
    __pythonTag = None # Identifier used for this attribute within the owning class
    __valueAttributeName = None # Private attribute used in instances to hold the attribute value
    __dataType = None  # PST datatype
    __unicodeDefault = None     # Default value as a unicode string, or None
    __defaultValue = None       # Default value as an instance of datatype, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, tag, python_tag, value_attribute_name, data_type, unicode_default=None, fixed=False, required=False, prohibited=False):
        self.__tag = tag
        self.__pythonTag = python_tag
        self.__valueAttributeName = value_attribute_name
        self.__dataType = data_type
        self.__unicodeDefault = unicode_default
        if self.__unicodeDefault is not None:
            self.__defaultValue = self.__dataType(self.__unicodeDefault)
        self.__fixed = fixed
        self.__required = required
        self.__prohibited = prohibited

    def tag (self):
        """Unicode tag for the attribute in its element"""
        return self.__tag
    
    def pythonTag (self):
        """Tag used within Python code for the attribute"""
        return self.__pythonTag

    def __getValue (self, ctd_instance):
        return getattr(ctd_instance, self.__valueAttributeName, (False, None))

    def __getProvided (self, ctd_instance):
        return self.__getValue(ctd_instance)[0]

    def value (self, ctd_instance):
        """Get the value of the attribute."""
        return self.__getValue(ctd_instance)[1]

    def __setValue (self, ctd_instance, new_value, provided):
        return setattr(ctd_instance, self.__valueAttributeName, (provided, new_value))

    def reset (self, ctd_instance):
        self.__setValue(ctd_instance, self.__defaultValue, False)

    def setFromDOM (self, ctd_instance, node):
        """Set the value of the attribute in the given instance from
        the corresponding attribute of the DOM Element node.  If node
        is None, or does not have an attribute, the default value is
        assigned.  Raises ProhibitedAttributeError and
        MissingAttributeError in the cases of prohibited and required
        attributes.
        """
        unicode_value = self.__unicodeDefault
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
            self.__setValue(ctd_instance, None, False)
        else:
            if self.__fixed and (unicode_value != self.__defaultValue):
                raise AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__tag,))
            # NB: Do not set provided here; this may be the default
            self.__setValue(ctd_instance, self.__dataType(unicode_value), provided)
        return self

    def addDOMAttribute (self, ctd_instance, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        ( provided, value ) = self.__getValue(ctd_instance)
        if provided:
            assert value is not None
            element.setAttribute(self.__tag, value.xsdLiteral())
        return self

    def setValue (self, ctd_instance, new_value):
        """Set the value of the attribute.

        This validates the value against the data type."""
        assert new_value is not None
        if not isinstance(new_value, self.__dataType):
            new_value = self.__dataType(new_value)
        self.__setValue(ctd_instance, new_value, True)
        return new_value

class ElementUse (object):
    """Aggregate the information relevant to an element of a complex type.

    This includes the original tag name, the spelling of the
    corresponding object in Python, an indicator of whether multiple
    instances might be associated with the field, and a list of types
    for legal values of the field."""

    __tag = None
    __pythonTag = None
    __valueElementName = None
    __dataTypes = None
    __isPlural = False

    def __init__ (self, tag, python_tag, value_element_name, is_plural, default=None, data_types=[]):
        self.__tag = tag
        self.__pythonTag = python_tag
        self.__valueElementName = value_element_name
        self.__isPlural = is_plural
        self.__dataTypes = data_types

    def reset (self, ctd_instance):
        self.__setValue(ctd_instance, self.defaultValue())
        return self

    def _setDataTypes (self, data_types):
        self.__dataTypes = data_types

    def tag (self):
        return self.__tag
    
    def pythonTag (self):
        return self.__pythonTag

    def isPlural (self):
        return self.__isPlural

    def defaultValue (self):
        if self.isPlural():
            return []
        return None

    def value (self, ctd_instance):
        return getattr(ctd_instance, self.__valueElementName, self.defaultValue())

    def __setValue (self, ctd_instance, value):
        return setattr(ctd_instance, self.__valueElementName, value)

    def setValue (self, ctd_instance, value):
        if value is None:
            return self.reset(ctd_instance)
        assert self.__dataTypes is not None
        for dt in self.__dataTypes:
            if isinstance(value, dt):
                self.__setValue(ctd_instance, value)
                ctd_instance._addContent(value, self)
                return self
        for dt in self.__dataTypes:
            try:
                iv = dt(value)
                self.__setValue(ctd_instance, iv)
                ctd_instance._addContent(iv, self)
                return self
            except BadTypeValueError, e:
                pass
        raise BadTypeValueError('Cannot assign value of type %s to field %s: legal types %s' % (type(value), self.tag(), ' '.join([str(_dt) for _dt in self.__dataTypes])))

    def addDOMElement (self, value, document, element):
        """Add the given value of the corresponding element field to the DOM element."""
        if value is not None:
            assert isinstance(value, PyWXSB_element)
            value.toDOM(document, parent=element)
        return self

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

class ModelGroup (object):
    C_INVALID = 0
    C_ALL = 0x01
    C_CHOICE = 0x02
    C_SEQUENCE = 0x03

    # One of the C_* values above.  Set at construction time from the
    # keyword parameter "compositor".
    __compositor = C_INVALID
    def compositor (self):
        return self.__compositor

    # A list of _Particle instances.  Set at construction time from
    # the keyword parameter "particles".
    __particles = None
    def particles (self):
        return self.__particles

    def _setContent (self, compositor, particles):
        self.__compositor = compositor
        self.__particles = particles

class PyWXSB_enumeration_mixin (object):
    """Marker in case we need to know that a PST has an enumeration constraint facet."""
    pass

class PyWXSB_complexTypeDefinition (utility._DeconflictSymbols_mixin, object):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType.

    Subclasses should define a class-level _AttributeMap variable
    which maps from the unicode tag of an attribute to the
    AttributeUse instance that defines it.  Similarly, subclasses
    should define an _ElementMap variable.
    """

    _AttributeMap = { }
    _ElementMap = { }

    def __init__ (self, *args, **kw):
        super(PyWXSB_complexTypeDefinition, self).__init__(*args, **kw)
        that = None
        if (0 < len(args)) and isinstance(args[0], self.__class__):
            that = args[0]
        if isinstance(self, _CTD_content_mixin):
            self._resetContent()
        for fu in self._PythonMap().values():
            fu.reset(self)
            iv = None
            if that is not None:
                iv = fu.value(that)
            iv = kw.get(fu.pythonTag(), iv)
            if iv is not None:
                fu.setValue(self, iv)

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    # Specify the symbols to be reserved for all CTDs.
    _ReservedSymbols = set([ 'Factory', 'CreateFromDOM', 'toDOM' ])

    # Class variable which maps complex type attribute names to the
    # name used within the generated binding.  For example, if
    # somebody's gone and decided that the word Factory would make an
    # awesome attribute for some complex type, the binding will
    # rewrite it so the accessor method is Factory_.  This is only
    # overridden in generated bindings where an attribute name
    # conflicted with a reserved symbol.
    _AttributeDeconflictMap = { }

    # Class variable which maps complex type element names to the name
    # used within the generated binding.  See _AttributeDeconflictMap.
    _ElementDeconflictMap = { }

    @classmethod
    def __PythonMapAttribute (cls):
        return '_%s_PythonMap' % (cls.__name__,)

    @classmethod
    def _PythonMap (cls):
        return getattr(cls, cls.__PythonMapAttribute(), { })

    @classmethod
    def _UpdateElementDatatypes (cls, datatype_map):
        for (k, v) in datatype_map.items():
            cls._ElementMap[k]._setDataTypes(v)
        python_map = { }
        for eu in cls._ElementMap.values():
            python_map[eu.pythonTag()] = eu
        for au in cls._AttributeMap.values():
            python_map[au.pythonTag()] = au
        assert(len(python_map) == (len(cls._ElementMap) + len(cls._AttributeMap)))
        setattr(cls, cls.__PythonMapAttribute(), python_map)

    def _setAttributesFromDOM (self, node):
        for au in self._AttributeMap.values():
            au.setFromDOM(self, node)
        return self

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeMap.values():
            au.addDOMAttribute(self, element)
        return element

    def toDOM (self, tag=None, document=None, parent=None):
        """Create a DOM element with the given tag holding the content of this instance."""
        if document is None:
            assert parent is None
            document = minidom.getDOMImplementation().createDocument(None, tag, None)
            element = document.documentElement
        else:
            if parent is None:
                parent = document.documentElement()
            if tag is None:
                element = parent
            else:
                element = parent.appendChild(document.createElement(tag))
        self._setDOMFromContent(document, element)
        self._setDOMFromAttributes(element)
        return element

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with empty content."""

    @classmethod
    def CreateFromDOM (cls, node):
        """Create a raw instance, and set attributes from the DOM node."""
        return cls()._setAttributesFromDOM(node)

    def _setDOMFromContent (self, document, element):
        return self

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with simple content."""

    __content = None
    def content (self):
        return self.__content

    def __init__ (self, *args, **kw):
        super(PyWXSB_CTD_simple, self).__init__(**kw)
        self.__content = self._TypeDefinition.Factory(*args, **kw)

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    @classmethod
    def CreateFromDOM (cls, node):
        """Create an instance from the node content, and set the attributes."""
        return cls(domutils.ExtractTextContent(node))._setAttributesFromDOM(node)

    def _setDOMFromContent (self, document, element):
        """Create a DOM element with the given tag holding the content of this instance."""
        return element.appendChild(document.createTextNode(self.content().xsdLiteral()))

class _CTD_content_mixin (object):
    __elementContent = None
    __content = None

    def __init__ (self, *args, **kw):
        self._resetContent()
        super(_CTD_content_mixin, self).__init__(*args, **kw)

    def content (self):
        return self.__content

    def _resetContent (self):
        self.__content = []
        self.__elementContent = []

    def _elementContent (self):
        return self.__elementContent()

    def _addContent (self, child, element_use=None):
        self.__elementContent.append( (child, element_use) )
        self.__content.append(child)

    def _setDOMFromContent (self, document, element):
        for (content, element_use) in self.__elementContent:
            element_use.addDOMElement(content, document, element)
        return self

class PyWXSB_CTD_mixed (_CTD_content_mixin, PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with mixed content.
    """
    pass

class PyWXSB_CTD_element (_CTD_content_mixin, PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with element-only content.  Subclasses must
    define a class variable _Content with a bindings.Particle instance
    as its value.

    Subclasses should define a class-level _ElementMap variable which
    maps from unicode element tags (not including namespace
    qualifiers) to the corresponding ElementUse information
    """
    pass

