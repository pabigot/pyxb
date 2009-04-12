"""Classes supporting XMLSchema Part 2: Datatypes.

Each SimpleTypeDefinition component instance is paired with at most
one PythonSimpleType (PST), which is a subclass of a Python type
augmented with facets and other constraining information.  This file
contains the definitions of these types.

We want the simple datatypes to be efficient Python values, but to
also hold specific constraints that don't apply to the Python types.
To do this, we subclass each PST.  Primitive PSTs inherit from the
Python type that represents them, and from a _PST_mixin class which
adds in the constraint infrastructure.  Derived PSTs inherit from the
parent PST.

There is an exception to this when the Python type best suited for a
derived SimpleTypeDefinition differs from the type associated with its
parent STD: for example, xsd:integer has a value range that requires
it be represented by a Python long, but xsd:int allows representation
by a Python int.  In this case, the derived PST class is structured
like a primitive type, but the PST associated with the STD superclass
is recorded in a class variable _XsdBaseType.

Note the strict terminology: "datatype" refers to a class which is a
subclass of a Python type, while "type definition" refers to an
instance of either SimpleTypeDefinition or ComplexTypeDefinition.

"""

from PyWXSB.exceptions_ import *
import structures as xsc
import types
import PyWXSB.Namespace as Namespace
import PyWXSB.domutils as domutils

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

#"""http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType"""
# NB: anyType is a ComplexTypeDefinition instance; haven't figured out
# how to deal with that yet.

class _PST_mixin (object):
    """_PST_mixin is a base mix-in class that is part of the hierarchy
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
    # Note that each descendent of _PST_mixin has its own map.
    __FacetMap = {}

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
            if issubclass(super_class, _PST_mixin):
                fm = super_class._FacetMap()
                break
        if fm is None:
            raise LogicError('%s is not a child of _PST_mixin' % (cls.__name__,))
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

        This method may be overridden in subclasses (like _PST_union)."""
        return cls(*args, **kw)

    @classmethod
    def CreateFromDOM (cls, node):
        """Create a simple type instance from the given DOM Node instance."""
        return cls.Factory(domutils.ExtractTextContent(node))

    # Must override new, because new gets invoked before init, and
    # usually doesn't accept keywords.  In case it does, only remove
    # the ones that are interpreted by this class.  Do the same
    # argument conversion as is done in init.
    def __new__ (cls, *args, **kw):
        kw.pop('validate_constraints', None)
        return super(_PST_mixin, cls).__new__(cls, *cls.__ConvertArgs(args), **kw)

    # Validate the constraints after invoking the parent constructor,
    # unless told not to.
    def __init__ (self, *args, **kw):
        validate_constraints = kw.pop('validate_constraints', True)
        super(_PST_mixin, self).__init__(*self.__ConvertArgs(args), **kw)
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
        attr_name = cls.__STDAttrName()
        if hasattr(cls, attr_name):
            return getattr(cls, attr_name)
        raise IncompleteImplementationError('%s: No STD available' % (cls,))

    @classmethod
    def XsdLiteral (cls, value):
        """Convert from a python value to a quoted string usable in a schema."""
        raise LogicError('%s does not implement XsdLiteral' % (cls,))

    def xsdLiteral (self):
        return self.XsdLiteral(self)

    @classmethod
    def XsdSuperType (cls):
        """Find the nearest parent class in the PST hierarchy.

        The value for anySimpleType is None; for all others, it's a
        primitive or derived PST descendent (including anySimpleType)."""
        for sc in cls.mro():
            if sc == cls:
                continue
            if _PST_mixin == sc:
                # If we hit the PST base, this is a primitive type or
                # otherwise directly descends from a Python type; return
                # the recorded XSD supertype.
                return cls._XsdBaseType
            if issubclass(sc, _PST_mixin):
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
            if not issubclass(sc, _PST_mixin):
                return sc
        raise LogicError('No python type found for %s' % (cls,))

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Pre-extended class method to verify other things before checking constraints."""
        super_fn = getattr(super(_PST_mixin, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
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
    def XsdToString (cls, value):
        """Convert the python native value into a string suitable for use in a schema."""
        return unicode(str(value))

    def xsdToString (cls):
        return self.XsdToString(self)

    @classmethod
    def XsdFromString (cls, string_value):
        return cls(string_value)

    def pythonLiteral (self):
        class_name = self.__class__.__name__
        return '%s(%s)' % (class_name, super(_PST_mixin, self).__str__())

class _PST_union (_PST_mixin):
    """Base class for union datatypes.

    This class descends only from _PST_mixin.  A LogicError is raised
    if an attempt is made to construct an instance of a subclass of
    _PST_union.  Values consistent with the member types are
    constructed using the Factory class method.  Values are validated
    using the ValidateMember class method.

    Subclasses must provide a class variable _MemberTypes which is a
    tuple of legal members of the union."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from _PST_mixin.
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
    def ValidateMember (cls, value):
        """Validate the given value as a potential union member.

        Raises BadTypeValueError if the value is not an instance of a
        member type."""
        if not isinstance(value, cls._MemberTypes):
            raise BadTypeValueError('%s cannot hold a member of type %s' % (cls.__name__, value.__class__.__name__))
        return value

    def __init__ (self, *args, **kw):
        raise LogicError('%s: cannot construct instances of union' % (self.__class__.__name__,))

class _PST_list (_PST_mixin, types.ListType):
    """Base class for collection datatypes.

    This class descends from the Python list type, and incorporates
    _PST_mixin.  Subclasses must define a class variable _ItemType
    which is a reference to the class of which members must be
    instances."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from _PST_mixin.
    __FacetMap = {}

    @classmethod
    def ValidateItem (cls, value):
        """Verify that the given value is permitted as an item of this list."""
        if issubclass(cls._ItemType, _PST_union):
            cls._ItemType.ValidateMember(value)
        else:
            if not isinstance(value, cls._ItemType):
                raise BadTypeValueError('Type %s has member of type %s, must be %s' % (cls.__name__, type(value).__name__, cls._ItemType.__name__))
        return value

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Verify that the items in the list are acceptable members."""
        for v in value:
            cls.ValidateItem(v)
        super_fn = getattr(super(_PST_list, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)

    @classmethod
    def _XsdValueLength_vx (cls, value):
        return len(value)

# We use unicode as the Python type for anything that isn't a normal
# primitive type.  Presumably, only enumeration and pattern facets
# will be applied.
class anySimpleType (_PST_mixin, unicode):
    """http://www.w3.org/TR/xmlschema-2/#dt-anySimpleType"""
    _XsdBaseType = None
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return value
# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).
    
class string (_PST_mixin, unicode):
    """string.
    
    http://www.w3.org/TR/xmlschema-2/#string"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        assert isinstance(value, cls)
        return value

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

_PrimitiveDatatypes.append(string)

# It is illegal to subclass the bool type in Python, so we subclass
# int instead.
class boolean (_PST_mixin, int):
    """boolean.

    http://www.w3.org/TR/xmlschema-2/#boolean"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    
    @classmethod
    def XsdLiteral (cls, value):
        if value:
            return 'True'
        return 'False'

    def __str__ (self):
        if self:
            return 'true'
        return 'false'

    def __new__ (cls, value, *args, **kw):
        # Strictly speaking, only 'true' and 'false' should be
        # recognized; however, since the base type is a built-in,
        # @todo ensure pickle value is str(self)
        if value in (1, 0, '1', '0', 'true', 'false'):
            if value in (1, '1', 'true'):
                iv = True
            else:
                iv = False
            return super(boolean, cls).__new__(cls, iv, *args, **kw)
        raise ValueError('[xsd:boolean] Initializer "%s" not valid for type' % (value,))


_PrimitiveDatatypes.append(boolean)

class decimal (_PST_mixin, types.FloatType):
    """decimal.
    
    http://www.w3.org/TR/xmlschema-2/#decimal

    @todo The Python base type for this is wrong. Consider
    http://code.google.com/p/mpmath/.

    """
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(decimal)

class float (_PST_mixin, types.FloatType):
    """float.

    http://www.w3.org/TR/xmlschema-2/#float"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(float)

class double (_PST_mixin, types.FloatType):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(double)

class duration (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(duration)

class dateTime (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(dateTime)

class time (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(time)

class date (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(date)

class gYearMonth (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gYearMonth)

class gYear (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gYear)

class gMonthDay (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gMonthDay)

class gDay (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gDay)

class gMonth (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gMonth)

class hexBinary (_PST_mixin, types.LongType):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    def __new__ (cls, value, *args, **kw):
        if isinstance(value, types.StringTypes):
            return super(hexBinary, cls).__new__(cls, '0x%s' % (value,), 16, *args, **kw)
        return super(hexBinary, cls).__new__(cls, value, *args, **kw)

    @classmethod
    def XsdLiteral (self, value):
        return '0x%x' % (value,)

    @classmethod
    def XsdValueLength (cls, value):
        raise NotImplementedError('No length calculation for hexBinary')

_PrimitiveDatatypes.append(hexBinary)

class base64Binary (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdValueLength (cls, value):
        raise NotImplementedError('No length calculation for base64Binary')

_PrimitiveDatatypes.append(base64Binary)

class anyURI (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

_PrimitiveDatatypes.append(anyURI)

class QName (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdValueLength (cls, value):
        """Section 4.3.1.3: Legacy length return None to indicate no check"""
        return None

_PrimitiveDatatypes.append(QName)

class NOTATION (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdValueLength (cls, value):
        """Section 4.3.1.3: Legacy length return None to indicate no check"""
        return None

_PrimitiveDatatypes.append(NOTATION)

class normalizedString (string):
    pass
_DerivedDatatypes.append(normalizedString)
assert normalizedString.XsdSuperType() == string

class token (normalizedString):
    pass
_DerivedDatatypes.append(token)

class language (token):
    pass
_DerivedDatatypes.append(language)

class NMTOKEN (token):
    pass
_DerivedDatatypes.append(NMTOKEN)

class NMTOKENS (_PST_list):
    _ItemType = NMTOKEN
_ListDatatypes.append(NMTOKENS)

class Name (token):
    pass
_DerivedDatatypes.append(Name)

class NCName (Name):
    pass
_DerivedDatatypes.append(NCName)

class ID (NCName):
    pass
_DerivedDatatypes.append(ID)

class IDREF (NCName):
    pass
_DerivedDatatypes.append(IDREF)

class IDREFS (_PST_list):
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    pass
_DerivedDatatypes.append(ENTITY)

class ENTITIES (_PST_list):
    _ItemType = ENTITY
_ListDatatypes.append(ENTITIES)

class integer (_PST_mixin, long):
    """integer.

    http://www.w3.org/TR/xmlschema-2/#integer"""
    _XsdBaseType = decimal
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdLiteral (cls, value):
        return 'long(%s)' % (value,)

_DerivedDatatypes.append(integer)

class nonPositiveInteger (integer):
    MinimumValue = 1
_DerivedDatatypes.append(nonPositiveInteger)

class negativeInteger (nonPositiveInteger):
    MaximumValue = -1
_DerivedDatatypes.append(negativeInteger)

class long (integer):
    MinimumValue = -9223372036854775808
    MaximumValue = 9223372036854775807
_DerivedDatatypes.append(long)

class int (_PST_mixin, types.IntType):
    _XsdBaseType = long
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

    MinimumValue = -2147483648
    MaximumValue = 2147483647
_DerivedDatatypes.append(int)

class short (int):
    MinimumValue = -32768
    MaximumValue = 32767
_DerivedDatatypes.append(short)

class byte (short):
    MinimumValue = -128
    MaximumValue = 127
    pass
_DerivedDatatypes.append(byte)

class nonNegativeInteger (integer):
    MinimumValue = 0
_DerivedDatatypes.append(nonNegativeInteger)

class unsignedLong (nonNegativeInteger):
    pass
_DerivedDatatypes.append(unsignedLong)

class unsignedInt (unsignedLong):
    pass
_DerivedDatatypes.append(unsignedInt)

class unsignedShort (unsignedInt):
    pass
_DerivedDatatypes.append(unsignedShort)

class unsignedByte (unsignedShort):
    pass
_DerivedDatatypes.append(unsignedByte)

class positiveInteger (nonNegativeInteger):
    pass
_DerivedDatatypes.append(positiveInteger)

try:
    import datatypes_facets
except ImportError, e:
    pass

def _AddSimpleTypes (schema):
    """Add to the schema the definitions of the built-in types of
    XMLSchema."""
    # Add the ur type
    td = schema._addNamedComponent(xsc.ComplexTypeDefinition.UrTypeDefinition(in_builtin_definition=True))
    assert td.isResolved()
    # Add the simple ur type
    td = schema._addNamedComponent(xsc.SimpleTypeDefinition.SimpleUrTypeDefinition(in_builtin_definition=True))
    assert td.isResolved()
    # Add definitions for all primitive and derived simple types
    pts_std_map = {}
    for dtc in _PrimitiveDatatypes:
        name = dtc.__name__.rstrip('_')
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreatePrimitiveInstance(name, schema, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in _DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.XsdSuperType()]
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateDerivedInstance(name, schema, parent_std, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in _ListDatatypes:
        list_name = dtc.__name__.rstrip('_')
        element_name = dtc._ItemType.__name__.rstrip('_')
        element_std = schema._lookupTypeDefinition(element_name)
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateListInstance(list_name, schema, element_std, dtc))
        assert td.isResolved()
    return schema

