from PyWXSB.exceptions_ import *
import XMLSchema as xs
import xml.dom as dom
from xml.dom import minidom
import domutils
import utility
import types

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

    def content (self):
        """Return the element content, which is an instance of the
        _TypeDefinition for this class.  Or, in the case that
        _TypeDefinition is a complex type with simple content, the
        dereferenced simple content is returned."""
        return self.__content
    
    @classmethod
    def CreateFromDOM (cls, node):
        """Create an instance of this element from the given DOM node.

        Raises LogicError if the name of the node is not consistent
        with the _XsdName of this class."""
        node_name = node.nodeName
        if 0 < node_name.find(':'):
            node_name = node_name.split(':')[1]
        if cls._XsdName != node_name:
            raise LogicError('Attempting to create element %s from DOM node named %s' % (cls._XsdName, node_name))
        rv = cls()
        rv.__setContent(cls._TypeDefinition.CreateFromDOM(node))
        return rv

    def toDOM (self, document=None, parent=None):
        (document, element) = domutils.ToDOM_startup(document, parent, self._XsdName)
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

    def _setDataTypes (self, data_types):
        self.__dataTypes = data_types

    def tag (self):
        return self.__tag
    
    def pythonTag (self):
        return self.__pythonTag

    def isPlural (self):
        return self.__isPlural

    def validElements (self):
        return self.__dataTypes

    def defaultValue (self):
        if self.isPlural():
            return []
        return None

    def clearGenerationMarkers (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                return
            value = [ value ]
        for v in value:
            assert v is not None
            v.__generated = False

    def nextValueToGenerate (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                raise DOMGenerationError('Optional %s value is not available' % (self.pythonTag(),))
            value = [ value ]
        for v in value:
            if not v.__generated:
                print 'Marked value in %s as generated' % (self.pythonTag(),)
                v.__generated = True
                return v
        raise DOMGenerationError('No %s values remain to be generated' % (self.pythonTag(),))

    def hasUngeneratedValues (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                return False
            value = [ value ]
        for v in value:
            if not v.__generated:
                return True
        return False

    def value (self, ctd_instance):
        return getattr(ctd_instance, self.__valueElementName, self.defaultValue())

    def reset (self, ctd_instance):
        setattr(ctd_instance, self.__valueElementName, self.defaultValue())
        return self

    def __setValue (self, ctd_instance, value):
        if self.isPlural():
            values = self.value(ctd_instance)
            values.append(value)
            return values
        return setattr(ctd_instance, self.__valueElementName, value)

    # @todo Distinguish based on plurality
    def setValue (self, ctd_instance, value):
        """Set the value of this element in the given instance."""
        if value is None:
            return self.reset(ctd_instance)
        assert self.__dataTypes is not None
        for dt in self.__dataTypes:
            if isinstance(value, dt):
                self.__setValue(ctd_instance, value)
                ctd_instance._addContent(value)
                return self
        for dt in self.__dataTypes:
            try:
                iv = dt(value)
                self.__setValue(ctd_instance, iv)
                ctd_instance._addContent(iv)
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

    def extendDOMFromContent (self, document, element, ctd_instance):
        rep = 0
        assert isinstance(ctd_instance, PyWXSB_complexTypeDefinition)
        while ((self.maxOccurs() is None) or (rep < self.maxOccurs())):
            try:
                if isinstance(self.term(), ModelGroup):
                    self.term().extendDOMFromContent(document, element, ctd_instance)
                elif issubclass(self.term(), PyWXSB_element):
                    eu = ctd_instance._UseForElement(self.term())
                    assert eu is not None
                    value = eu.nextValueToGenerate(ctd_instance)
                    value.toDOM(document, element)
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except IncompleteImplementationError, e:
                raise
            except DOMGenerationError, e:
                break
            except Exception, e:
                print 'Caught extending DOM from term %s: %s' % (self.term(), e)
                raise
            rep += 1
        if rep < self.minOccurs():
            raise DOMGenerationError('Expected at least %d instances of %s, got only %d' % (self.minOccurs(), self.term(), rep))

    def extendFromDOM (self, ctd_instance, node_list):
        """Extend the content of the given ctd_instance from the DOM
        nodes in the list.

        Nodes are removed from the front of the list as their content
        is extracted and saved.  The unconsumed portion of the list is
        returned."""
        rep = 0
        assert isinstance(ctd_instance, PyWXSB_complexTypeDefinition)
        while (0 < len(node_list)) and ((self.maxOccurs() is None) or (rep < self.maxOccurs())):
            try:
                if isinstance(self.term(), ModelGroup):
                    node_list = self.term().extendFromDOM(ctd_instance, node_list)
                elif issubclass(self.term(), PyWXSB_element):
                    if 0 == len(node_list):
                        raise MissingContentError('Expected element %s' % (self.term()._XsdName,))
                    element = self.term().CreateFromDOM(node_list[0])
                    node_list.pop(0)
                    ctd_instance._addElement(element)
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except IncompleteImplementationError, e:
                raise
            except Exception, e:
                print 'Caught creating term from DOM %s: %s' % (node_list[0], e)
                raise
            rep += 1
        if rep < self.minOccurs():
            raise MissingContentError('Expected at least %d instances of %s, got only %d' % (self.minOccurs(), self.term(), rep))
        return node_list

class ModelGroup (object):
    """Record the structure of a model group.

    This is used when interpreting a DOM document fragment, to be sure
    the correct binding structure is used to extract the contents of
    each element.  It almost does something like validation, as a side
    effect."""

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

    def __extendDOMFromChoice (self, document, element, ctd_instance, candidate_particles):
        for particle in candidate_particles:
            try:
                particle.extendDOMFromContent(document, element, ctd_instance)
                return particle
            except DOMGenerationError, e:
                pass
            except Exception, e:
                print 'GEN CHOICE failed: %s' % (e,)
                raise
        return None

    def extendDOMFromContent (self, document, element, ctd_instance):
        assert isinstance(ctd_instance, PyWXSB_complexTypeDefinition)
        if self.C_SEQUENCE == self.compositor():
            for particle in self.particles():
                particle.extendDOMFromContent(document, element, ctd_instance)
        elif self.C_ALL == self.compositor():
            mutable_particles = self.particles().copy()
            while 0 < len(mutable_particles):
                try:
                    choice = self.__extendDOMFromChoice(document, element, ctd_instance, mutable_particles)
                    mutable_particles.remove(choice)
                except Exception, e:
                    print 'ALL failed: %s' % (e,)
                    break
            for particle in mutable_particles:
                if 0 < particle.minOccurs():
                    raise DOMGenerationError('ALL: Could not generate instance of required %s' % (particle.term(),))
        elif self.C_CHOICE == self.compositor():
            choice = self.__extendDOMFromChoice(document, element, ctd_instance, self.particles())
            if choice is None:
                raise DOMGenerationError('CHOICE: No candidates found')
        else:
            assert False
        
    def __extendContentFromChoice (self, ctd_instance, node_list, candidate_particles):
        for particle in candidate_particles:
            assert particle.minOccurs() in (0, 1)
            assert 1 == particle.maxOccurs()
            try:
                node_list = particle.extendFromDOM(ctd_instance, node_list)
                return (particle, node_list)
            except Exception, e:
                print 'CHOICE failed: %s' % (e,)
        raise UnrecognizedContentError(node_list[0])

    def extendFromDOM (self, ctd_instance, node_list):
        assert isinstance(ctd_instance, PyWXSB_complexTypeDefinition)
        mutable_node_list = node_list[:]
        if self.C_SEQUENCE == self.compositor():
            for particle in self.particles():
                try:
                    mutable_node_list = particle.extendFromDOM(ctd_instance, mutable_node_list)
                except Exception, e:
                    print 'SEQUENCE failed: %s' % (e,)
                    raise
            return mutable_node_list
        elif self.C_ALL == self.compositor():
            mutable_particles = self.particles().copy()
            while 0 < len(mutable_particles):
                try:
                    (choice, new_list) = self.__extendContentFromChoice(ctd_instance, mutable_node_list, mutable_particles)
                    mutable_particles.remove(choice)
                    mutable_node_list = new_list
                except Exception, e:
                    print 'ALL failed: %s' % (e,)
                    break
            for particle in mutable_particles:
                if 0 < particle.minOccurs():
                    raise MissingContentError('ALL: Expected an instance of %s' % (particle.term(),))
            print 'Ignored unused %s' % (mutable_particles,)
            return mutable_node_list
        elif self.C_CHOICE == self.compositor():
            (choice, new_list) = self.__extendContentFromChoice(ctd_instance, mutable_node_list, self.particles())
            return new_list
        else:
            assert False

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
        """Create an instance from parameters and keywords."""
        rv = cls(*args, **kw)
        return rv

    @classmethod
    def CreateFromDOM (cls, node):
        """Create an instance from a DOM node.

        Note that only the node attributes and content are used; the
        node name must have been validated against an owning
        element."""
        rv = cls()
        rv._setAttributesFromDOM(node)
        rv._setContentFromDOM(node)
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

    @classmethod
    def _UseForElement (cls, element):
        for eu in cls._ElementMap.values():
            if element in eu.validElements():
                return eu
        return None

    def _setAttributesFromDOM (self, node):
        """Initialize the attributes of this element from those of the DOM node."""
        for au in self._AttributeMap.values():
            au.setFromDOM(self, node)
        return self

    def _setContentFromDOM_vx (self, node):
        """Override this in subclasses that expect to process content."""
        raise LogicError('%s did not implement _setContentFromDOM_vx' % (self.__class__.__name__,))

    def _setContentFromDOM (self, node):
        """Initialize the content of this element from the content of the DOM node."""
        return self._setContentFromDOM_vx(node)

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeMap.values():
            au.addDOMAttribute(self, element)
        return element

    def toDOM (self, document=None, parent=None, tag=None):
        """Create a DOM element with the given tag holding the content of this instance."""
        (document, element) = domutils.ToDOM_startup(document, parent, tag)
        for eu in self._ElementMap.values():
            eu.clearGenerationMarkers(self)
        self._setDOMFromContent(document, element)
        for eu in self._ElementMap.values():
            if eu.hasUngeneratedValues(self):
                raise DOMGenerationError('Values in %s were not converted to DOM' % (eu.pythonTag(),))
        self._setDOMFromAttributes(element)
        return element

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with empty content."""

    def _setContentFromDOM_vx (self, node):
        """CTD with empty content does nothing with node content."""
        # @todo Schema validation check?
        return self

    def _setDOMFromContent (self, document, element):
        return self

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with simple content."""

    __content = None
    def content (self):
        return self.__content

    def __setContent (self, value):
        self.__content = value

    def __init__ (self, *args, **kw):
        assert issubclass(self._TypeDefinition, xs.datatypes._PST_mixin)
        super(PyWXSB_CTD_simple, self).__init__(**kw)
        self.__setContent(self._TypeDefinition.Factory(*args, **kw))

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    def _setContentFromDOM_vx (self, node):
        """CTD with simple content type creates a PST instance from the node body."""
        self.__setContent(self._TypeDefinition.CreateFromDOM(node))

    def _setDOMFromContent (self, document, element):
        """Create a DOM element with the given tag holding the content of this instance."""
        return element.appendChild(document.createTextNode(self.content().xsdLiteral()))

class _CTD_content_mixin (object):
    """Retain information about element and mixed content in a complex type instance.

    This is used to generate the XML from the binding in the same
    order as it was read in, with mixed content in the right position.
    It can also be used if order is critical to the interpretation of
    interleaved elements.

    Subclasses must define a class variable _Content with a
    bindings.Particle instance as its value.

    Subclasses should define a class-level _ElementMap variable which
    maps from unicode element tags (not including namespace
    qualifiers) to the corresponding ElementUse information
    """

    # A list containing just the content
    __content = None

    def __init__ (self, *args, **kw):
        self._resetContent()
        super(_CTD_content_mixin, self).__init__(*args, **kw)

    def content (self):
        return [ _x for _x in self.__content if isinstance(_x, types.StringTypes) ]

    def _resetContent (self):
        self.__content = []

    def _addElement (self, element):
        eu = self._ElementMap.get(element._XsdName, None)
        if eu is None:
            raise LogicError('Element %s is not registered within %s' % (element._XsdName, self._XsdName))
        eu.setValue(self, element)

    def _addContent (self, child):
        assert isinstance(child, PyWXSB_element) or isinstance(child, types.StringTypes)
        self.__content.append(child)

    def _setMixableContentFromDOM (self, node, is_mixed):
        """Set the content of this instance from the content of the given node."""
        assert isinstance(self._Content, Particle)
        node_list = []
        for cn in node.childNodes:
            if cn.nodeType in (dom.Node.TEXT_NODE, dom.Node.CDATA_SECTION_NODE):
                if is_mixed:
                    if 0 < len(node_list):
                        node_list = self._Content.extendFromDOM(self, node_list)
                    self._addContent(cn.data)
                else:
                    # Text outside of mixed mode is ignored.  @todo
                    # verify is only whitespace?
                    print 'Ignoring mixed content in %s: %s' % (node.nodeName, domutils.ExtractTextContent(cn),)
                    pass
            else:
                node_list.append(cn)
        if 0 < len(node_list):
            node_list = self._Content.extendFromDOM(self, node_list)
        if 0 < len(node_list):
            raise ExtraContentError('Extra content starting with %s' % (node_list[0],))
        return self

    def _setDOMFromContent (self, document, element):
        self._Content.extendDOMFromContent(document, element, self)
        mixed_content = self.content()
        if 0 < len(mixed_content):
            element.appendChild(document.createTextNode(''.join(mixed_content)))
        return self

class PyWXSB_CTD_mixed (_CTD_content_mixin, PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with mixed content.
    """

    def _setContentFromDOM_vx (self, node):
        """Delegate processing to content mixin, with mixed content enabled."""
        return self._setMixableContentFromDOM(node, is_mixed=True)


class PyWXSB_CTD_element (_CTD_content_mixin, PyWXSB_complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with element-only content.
    """

    def _setContentFromDOM_vx (self, node):
        """Delegate processing to content mixin, with mixed content disabled."""
        return self._setMixableContentFromDOM(node, is_mixed=False)
