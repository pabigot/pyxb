"""This file contains support classes from which schema-specific
bindings inherit, and that describe the content models of those
schema."""

from pywxsb.exceptions_ import *
import xml.dom as dom
from xml.dom import minidom
import pywxsb.utils.domutils as domutils
import pywxsb.utils.utility as utility
import types

class PyWXSB_simpleTypeDefinition (utility._DeconflictSymbols_mixin, object):
    """PyWXSB_simpleTypeDefinition is a base mix-in class that is part of the hierarchy
    of any class that represents the Python datatype for a
    SimpleTypeDefinition.

    Note: This class, or a descendent of it, must be the first class
    in the method resolution order when a subclass has multiple
    parents.  Otherwise, constructor keyword arguments may not be
    removed before passing them on to Python classes that do not
    accept them.
    """

    # A map from leaf classes in the facets module to instance of
    # those classes that constrain or otherwise affect the datatype.
    # Note that each descendent of PyWXSB_simpleTypeDefinition has its own map.
    __FacetMap = {}

    # Symbols that remain the responsibility of this class.  Any
    # public symbols in generated binding subclasses are deconflicted
    # by providing an alternative name in the subclass.  (There
    # currently are no public symbols in generated SimpleTypeDefinion
    # bindings.)
    _ReservedSymbols = set([ 'Factory', 'CreateFromDOM', 'XsdLiteral', 'xsdLiteral',
                            'XsdSuperType', 'XsdPythonType', 'XsdConstraintsOK',
                            'xsdConstraintsOK', 'XsdValueLength', 'xsdValueLength',
                            'PythonLiteral', 'pythonLiteral', 'toDOM' ])

    # Determine the name of the class-private facet map.  This
    # algorithm should match the one used by Python, so the base class
    # value can be read.
    @classmethod
    def __FacetMapAttributeName (cls):
        return '_%s__FacetMap' % (cls.__name__.strip('_'),)

    @classmethod
    def _FacetMap (cls):
        """Return a reference to the facet map for this datatype.

        The facet map is a map from leaf facet classes to instances of
        those classes that constrain or otherwise apply to the lexical
        or value space of the datatype.

        Raises AttributeError if the facet map has not been defined."""
        return getattr(cls, cls.__FacetMapAttributeName())
    
    @classmethod
    def _InitializeFacetMap (cls, *args):
        """Initialize the facet map for this datatype.

        This must be called exactly once, after all facets belonging
        to the datatype have been created.

        Raises LogicError if called multiple times, or if called when
        a parent class facet map has not been initialized."""
        fm = None
        try:
            fm = cls._FacetMap()
        except AttributeError:
            pass
        if fm is not None:
            raise LogicError('%s facet map initialized multiple times' % (cls.__name__,))
        for super_class in cls.mro()[1:]:
            if issubclass(super_class, PyWXSB_simpleTypeDefinition):
                fm = super_class._FacetMap()
                break
        if fm is None:
            raise LogicError('%s is not a child of PyWXSB_simpleTypeDefinition' % (cls.__name__,))
        fm = fm.copy()
        for facet in args:
            fm[type(facet)] = facet
        setattr(cls, cls.__FacetMapAttributeName(), fm)
        return fm

    @classmethod
    def __ConvertArgs (cls, args):
        """If the first argument is a string, and this class has a
        whitespace facet, replace the first argument with the results
        of applying whitespace normalization.

        We need to do this for both __new__ and __init__, because in
        some cases (e.g., str/unicode) the value is assigned during
        __new__ not __init__."""
        if (0 < len(args)) and isinstance(args[0], types.StringTypes):
            cf_whitespace = getattr(cls, '_CF_whiteSpace', None)
            if cf_whitespace is not None:
                norm_str = unicode(cf_whitespace.normalizeString(args[0]))
                args = (norm_str,) + args[1:]
        return args

    @classmethod
    def Factory (cls, *args, **kw):
        """Provide a common mechanism to create new instances of this type.

        The class constructor won't do, because you can't create
        instances of union types.

        This method may be overridden in subclasses (like PyWXSB_STD_union)."""
        return cls(*args, **kw)

    @classmethod
    def CreateFromDOM (cls, node):
        """Create a simple type instance from the given DOM Node instance."""
        # @todo error if non-text content?
        return cls.Factory(domutils.ExtractTextContent(node))

    # Must override new, because new gets invoked before init, and
    # usually doesn't accept keywords.  In case it does, only remove
    # the ones that are interpreted by this class.  Do the same
    # argument conversion as is done in init.
    def __new__ (cls, *args, **kw):
        kw.pop('validate_constraints', None)
        return super(PyWXSB_simpleTypeDefinition, cls).__new__(cls, *cls.__ConvertArgs(args), **kw)

    # Validate the constraints after invoking the parent constructor,
    # unless told not to.
    def __init__ (self, *args, **kw):
        validate_constraints = kw.pop('validate_constraints', True)
        super(PyWXSB_simpleTypeDefinition, self).__init__(*self.__ConvertArgs(args), **kw)
        if validate_constraints:
            self.xsdConstraintsOK()

    # This is a placeholder for a class method that will retrieve the
    # set of facets associated with the class.  We can't define it
    # here because the facets module has a dependency on this module.
    _GetConstrainingFacets = None

    # The class attribute name used to store the reference to the STD
    # instance must be unique to the class, not to this base class.
    # Otherwise we mistakenly believe we've already associated a STD
    # instance with a class (e.g., xsd:normalizedString) when in fact it's
    # associated with the superclass (e.g., xsd:string)
    @classmethod
    def __STDAttrName (cls):
        return '_%s__SimpleTypeDefinition' % (cls.__name__,)

    @classmethod
    def _SimpleTypeDefinition (cls, std):
        attr_name = cls.__STDAttrName()
        if hasattr(cls, attr_name):
            old_value = getattr(cls, attr_name)
            if old_value != std:
                raise LogicError('%s: Attempt to override existing STD %s with %s' % (cls, old_value.name(), std.name()))
        setattr(cls, attr_name, std)

    @classmethod
    def SimpleTypeDefinition (cls):
        """Return the SimpleTypeDefinition instance for the given
        class.  This should only be invoked when generating bindings.
        Raise IncompleteImplementationError if no STD instance has
        been associated with the class."""
        attr_name = cls.__STDAttrName()
        if hasattr(cls, attr_name):
            return getattr(cls, attr_name)
        raise IncompleteImplementationError('%s: No STD available' % (cls,))

    @classmethod
    def XsdLiteral (cls, value):
        """Convert from a python value to a string usable in an XML
        document."""
        raise LogicError('%s does not implement XsdLiteral' % (cls,))

    def xsdLiteral (self):
        """Return text suitable for representing the value of this
        instance in an XML document."""
        return self.XsdLiteral(self)

    @classmethod
    def XsdSuperType (cls):
        """Find the nearest parent class in the PST hierarchy.

        The value for anySimpleType is None; for all others, it's a
        primitive or derived PST descendent (including anySimpleType)."""
        for sc in cls.mro():
            if sc == cls:
                continue
            if PyWXSB_simpleTypeDefinition == sc:
                # If we hit the PST base, this is a primitive type or
                # otherwise directly descends from a Python type; return
                # the recorded XSD supertype.
                return cls._XsdBaseType
            if issubclass(sc, PyWXSB_simpleTypeDefinition):
                return sc
        raise LogicError('No supertype found for %s' % (cls,))

    @classmethod
    def XsdPythonType (cls):
        """Find the first parent class that isn't part of the
        PST_mixin hierarchy.  This is expected to be the Python value
        class."""
        for sc in cls.mro():
            if sc == object:
                continue
            if not issubclass(sc, PyWXSB_simpleTypeDefinition):
                return sc
        raise LogicError('No python type found for %s' % (cls,))

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Pre-extended class method to verify other things before checking constraints."""
        super_fn = getattr(super(PyWXSB_simpleTypeDefinition, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)

    @classmethod
    def XsdConstraintsOK (cls, value):
        """Validate the given value against the constraints on this class.

        Throws BadTypeValueError if any constraint is violated.
        """

        cls._XsdConstraintsPreCheck_vb(value)

        facet_values = None

        # When setting up the datatypes, if we attempt to validate
        # something before the facets have been initialized (e.g., a
        # nonNegativeInteger used as a length facet for the parent
        # integer datatype), just ignore that.
        try:
            facet_values = cls._FacetMap().values()
        except AttributeError:
            return value
        for f in facet_values:
            if not f.validateConstraint(value):
                raise BadTypeValueError('%s violation for %s in %s' % (f.Name(), value, cls.__name__))
            #print '%s ok for %s' % (f.Name(), value)
        return value

    def xsdConstraintsOK (self):
        """Validate the value of this instance against its constraints."""
        return self.XsdConstraintsOK(self)

    @classmethod
    def XsdValueLength (cls, value):
        """Return the length of the given value.

        The length is calculated by a subclass implementation of
        _XsdValueLength_vx in accordance with
        http://www.w3.org/TR/xmlschema-2/#rf-length.

        The return value is a non-negative integer, or None if length
        constraints should be considered trivially satisfied (as with
        QName and NOTATION).

        Raise LogicError if the provided value is not an instance of cls.

        Raise LogicError if an attempt is made to calculate a length
        for an instance of a type that does not support length
        calculations.
        """
        assert isinstance(value, cls)
        if not hasattr(cls, '_XsdValueLength_vx'):
            raise LogicError('Class %s does not support length validation' % (cls.__name__,))
        return cls._XsdValueLength_vx(value)

    def xsdValueLength (self):
        """Return the length of this instance within its value space.
        See XsdValueLength."""
        return self.XsdValueLength(self)

    @classmethod
    def PythonLiteral (cls, value):
        """Return a string which can be embedded into Python source to
        represent the given value as an instance of this class."""
        class_name = cls.__name__
        return '%s(%s)' % (class_name, repr(value))

    def pythonLiteral (self):
        """Return a string which can be embedded into Python source to
        represent the value of this instance."""
        return self.PythonLiteral(self)

    def toDOM (self, tag=None, document=None, parent=None):
        (document, element) = domutils.ToDOM_startup(document, parent)
        return element.appendChild(document.createTextNode(self.xsdLiteral()))


class PyWXSB_STD_union (PyWXSB_simpleTypeDefinition):
    """Base class for union datatypes.

    This class descends only from PyWXSB_simpleTypeDefinition.  A LogicError is raised
    if an attempt is made to construct an instance of a subclass of
    PyWXSB_STD_union.  Values consistent with the member types are
    constructed using the Factory class method.  Values are validated
    using the _ValidateMember class method.

    Subclasses must provide a class variable _MemberTypes which is a
    tuple of legal members of the union."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from PyWXSB_simpleTypeDefinition.
    # @todo Ensure that pattern and enumeration are valid constraints
    __FacetMap = {}

    @classmethod
    def Factory (cls, *args, **kw):
        """Given a value, attempt to create an instance of some member
        of this union.

        The first instance which can be legally created is returned.
        If no member type instance can be created from the given
        value, a BadTypeValueError is raised.

        The value generated from the member types is further validated
        against any constraints that apply to the union."""
        rv = None
        validate_constraints = kw.get('validate_constraints', True)
        for mt in cls._MemberTypes:
            try:
                rv = mt(*args, **kw)
                break
            except BadTypeValueError:
                pass
            except ValueError:
                pass
            except:
                pass
        if rv is not None:
            if validate_constraints:
                cls.XsdConstraintsOK(rv)
            return rv
        raise BadTypeValueError('%s cannot construct union member from args %s' % (cls.__name__, args))

    @classmethod
    def _ValidateMember (cls, value):
        """Validate the given value as a potential union member.

        Raises BadTypeValueError if the value is not an instance of a
        member type."""
        if not isinstance(value, cls._MemberTypes):
            raise BadTypeValueError('%s cannot hold a member of type %s' % (cls.__name__, value.__class__.__name__))
        return value

    def __init__ (self, *args, **kw):
        raise LogicError('%s: cannot construct instances of union' % (self.__class__.__name__,))

class PyWXSB_STD_list (PyWXSB_simpleTypeDefinition, types.ListType):
    """Base class for collection datatypes.

    This class descends from the Python list type, and incorporates
    PyWXSB_simpleTypeDefinition.  Subclasses must define a class variable _ItemType
    which is a reference to the class of which members must be
    instances."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from PyWXSB_simpleTypeDefinition.
    __FacetMap = {}

    @classmethod
    def _ValidateItem (cls, value):
        """Verify that the given value is permitted as an item of this list."""
        if issubclass(cls._ItemType, PyWXSB_STD_union):
            cls._ItemType._ValidateMember(value)
        else:
            if not isinstance(value, cls._ItemType):
                raise BadTypeValueError('Type %s has member of type %s, must be %s' % (cls.__name__, type(value).__name__, cls._ItemType.__name__))
        return value

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Verify that the items in the list are acceptable members."""
        for v in value:
            cls._ValidateItem(v)
        super_fn = getattr(super(PyWXSB_STD_list, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)

    @classmethod
    def _XsdValueLength_vx (cls, value):
        return len(value)

class PyWXSB_element (utility._DeconflictSymbols_mixin, object):
    """Base class for any Python class that serves as the binding to
    an XMLSchema element.

    The subclass must define a class variable _TypeDefinition which is
    a reference to the PyWXSB_simpleTypeDefinition or PyWXSB_complexTypeDefinition
    subclass that serves as the information holder for the element.

    Most actions on instances of these clases are delegated to the
    underlying content object.
    """

    # Reference to the simple or complex type binding that serves as
    # the content of this element.
    # MUST BE SET IN SUBCLASS
    _TypeDefinition = None

    # Reference to the instance of the underlying type
    __realContent = None

    # Reference to the instance of the underlying type, or to that
    # type's content if that is a complex type with simple content.
    __content = None
    
    # Symbols that remain the responsibility of this class.  Any
    # symbols in the type from the content are deconflicted by
    # providing an alternative name in the subclass.  See the
    # _DeconflictSymbols_mixin class.
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
        if isinstance(self.__content, PyWXSB_CTD_mixed):
            return self.__content.content()
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
            raise UnrecognizedContentError('Attempting to create element %s from DOM node named %s' % (cls._XsdName, node_name))
        rv = cls()
        rv.__setContent(cls._TypeDefinition.CreateFromDOM(node))
        return rv

    def toDOM (self, document=None, parent=None):
        """Add a DOM representation of this element as a child of
        parent, which should be a DOM Node instance."""
        (document, element) = domutils.ToDOM_startup(document, parent, self._XsdName)
        self.__realContent.toDOM(tag=None, document=document, parent=element)
        return element

class AttributeUse (object):
    """A helper class that encapsulates everything we need to know
    about the way an attribute is used within a binding class."""
    __tag = None       # Unicode XML tag @todo not including namespace
    __pythonField = None # Identifier used for this attribute within the owning class
    __valueAttributeName = None # Private attribute used in instances to hold the attribute value
    __dataType = None  # PST datatype
    __unicodeDefault = None     # Default value as a unicode string, or None
    __defaultValue = None       # Default value as an instance of datatype, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, tag, python_field, value_attribute_name, data_type, unicode_default=None, fixed=False, required=False, prohibited=False):
        self.__tag = tag
        self.__pythonField = python_field
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
    
    def pythonField (self):
        """Tag used within Python code for the attribute"""
        return self.__pythonField

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
    __pythonField = None
    __valueElementName = None
    __dataTypes = None
    __isPlural = False

    def __init__ (self, tag, python_field, value_element_name, is_plural, default=None, data_types=[]):
        self.__tag = tag
        self.__pythonField = python_field
        self.__valueElementName = value_element_name
        self.__isPlural = is_plural
        self.__dataTypes = data_types

    def _setDataTypes (self, data_types):
        self.__dataTypes = data_types

    def tag (self):
        return self.__tag
    
    def pythonField (self):
        return self.__pythonField

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
                raise DOMGenerationError('Optional %s value is not available' % (self.pythonField(),))
            value = [ value ]
        for v in value:
            if not v.__generated:
                v.__generated = True
                return v
        raise DOMGenerationError('No %s values remain to be generated' % (self.pythonField(),))

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
                elif isinstance(self.term(), type) and issubclass(self.term(), PyWXSB_element):
                    eu = ctd_instance._UseForElement(self.term())
                    assert eu is not None
                    value = eu.nextValueToGenerate(ctd_instance)
                    value.toDOM(document, element)
                elif isinstance(self.term(), Wildcard):
                    #print 'Generation ignoring wildcard'
                    # @todo handle generation of wildcards
                    break
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except IncompleteImplementationError, e:
                raise
            except DOMGenerationError, e:
                break
            except Exception, e:
                #print 'Caught extending DOM from term %s: %s' % (self.term(), e)
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
        while ((self.maxOccurs() is None) or (rep < self.maxOccurs())):
            ctd_instance._stripMixedContent(node_list)
            try:
                if isinstance(self.term(), ModelGroup):
                    self.term().extendFromDOM(ctd_instance, node_list)
                elif isinstance(self.term(), type) and issubclass(self.term(), PyWXSB_element):
                    if 0 == len(node_list):
                        raise MissingContentError('Expected element %s' % (self.term()._XsdName,))
                    element = self.term().CreateFromDOM(node_list[0])
                    node_list.pop(0)
                    ctd_instance._addElement(element)
                elif isinstance(self.term(), Wildcard):
                    if 0 == len(node_list):
                        raise MissingContentError('Expected wildcard')
                    ignored = node_list.pop(0)
                    #print 'Ignoring wildcard match %s' % (ignored,)
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except StructuralBadDocumentError, e:
                #print 'Informational MCE: %s' % (e,)
                break
            except IncompleteImplementationError, e:
                raise
            except Exception, e:
                #print 'Caught creating term from DOM: %s' % (e,)
                raise
            rep += 1
        if rep < self.minOccurs():
            if 0 < len(node_list):
                raise UnrecognizedContentError('Expected at least %d instances of %s, got only %d before %s' % (self.minOccurs(), self.term(), rep, node_list[0].nodeName))
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
    # the keyword parameter "particles".  May be sorted; see
    # _setContent.
    __particles = None
    def particles (self):
        return self.__particles

    def _setContent (self, compositor, particles):
        self.__compositor = compositor
        self.__particles = particles
        # Particle lists that might be involved in a choice are sorted
        # for greedy matching.
        if self.compositor() in (self.C_ALL, self.C_CHOICE):
            self.__particles.sort(lambda _x,_y: -cmp(_x.minOccurs(), _y.minOccurs()))

    def __init__ (self, compositor=C_INVALID, particles=None):
        self._setContent(compositor, particles)

    def __extendDOMFromChoice (self, document, element, ctd_instance, candidate_particles):
        # Correct behavior requires that particles with a minOccurs()
        # of 1 preceed any particle with minOccurs() of zero;
        # otherwise we can incorrectly succeed at matching while not
        # consuming everything that's available.  This sorting was
        # done in _setContent.
        for particle in candidate_particles:
            try:
                particle.extendDOMFromContent(document, element, ctd_instance)
                return particle
            except DOMGenerationError, e:
                pass
            except Exception, e:
                #print 'GEN CHOICE failed: %s' % (e,)
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
                except DOMGenerationError, e:
                    #print 'ALL failed: %s' % (e,)
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
        # @todo Is there a preference to match particles that have a
        # minOccurs of 1?  Probably....
        for particle in candidate_particles:
            assert particle.minOccurs() in (0, 1)
            assert 1 == particle.maxOccurs()
            try:
                particle.extendFromDOM(ctd_instance, node_list)
                return particle
            except BadDocumentError, e:
                #print 'CHOICE failed: %s' % (e,)
                pass
        if 0 < len(node_list):
            raise UnrecognizedContentError(node_list[0])
        raise MissingContentError('No match for required choice')

    def extendFromDOM (self, ctd_instance, node_list):
        assert isinstance(ctd_instance, PyWXSB_complexTypeDefinition)
        if self.C_SEQUENCE == self.compositor():
            for particle in self.particles():
                try:
                    particle.extendFromDOM(ctd_instance, node_list)
                except BadDocumentError, e:
                    #print 'SEQUENCE failed: %s' % (e,)
                    raise
            return
        elif self.C_ALL == self.compositor():
            mutable_particles = self.particles()[:]
            while 0 < len(mutable_particles):
                try:
                    choice = self.__extendContentFromChoice(ctd_instance, node_list, mutable_particles)
                    mutable_particles.remove(choice)
                except BadDocumentError, e:
                    #print 'ALL failed: %s' % (e,)
                    break
            for particle in mutable_particles:
                if 0 < particle.minOccurs():
                    raise MissingContentError('ALL: Expected an instance of %s' % (particle.term(),))
            #print 'Ignored unused %s' % (mutable_particles,)
            return
        elif self.C_CHOICE == self.compositor():
            choice = self.__extendContentFromChoice(ctd_instance, node_list, self.particles())
            return
        else:
            assert False

class Wildcard (object):
    """Placeholder for wildcard objects."""
    pass

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
            iv = kw.get(fu.pythonField(), iv)
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
            python_map[eu.pythonField()] = eu
        for au in cls._AttributeMap.values():
            python_map[au.pythonField()] = au
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
                raise DOMGenerationError('Values in %s were not converted to DOM' % (eu.pythonField(),))
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
        assert issubclass(self._TypeDefinition, PyWXSB_simpleTypeDefinition)
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
        return ''.join([ _x for _x in self.__content if isinstance(_x, types.StringTypes) ])

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

    __isMixed = False
    def _stripMixedContent (self, node_list):
        while 0 < len(node_list):
            if not (node_list[0].nodeType in (dom.Node.TEXT_NODE, dom.Node.CDATA_SECTION_NODE)):
                break
            cn = node_list.pop(0)
            if self.__isMixed:
                #print 'Adding mixed content'
                self._addContent(cn.data)
            else:
                #print 'Ignoring mixed content'
                pass
        return node_list

    def _setMixableContentFromDOM (self, node, is_mixed):
        """Set the content of this instance from the content of the given node."""
        assert isinstance(self._Content, Particle)
        # The child nodes may include text which should be saved as
        # mixed content.  Use _stripMixedContent prior to extracting
        # element data to save them in the correct relative position,
        # while not losing track of where we are in the content model.
        self.__isMixed = is_mixed
        node_list = node.childNodes[:]
        self._Content.extendFromDOM(self, node_list)
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
