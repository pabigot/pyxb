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

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

#"""http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType"""
# NB: anyType is a ComplexTypeDefinition instance; haven't figured out
# how to deal with that yet.

class _PST_mixin (object):
    _Facets = []

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
        raise LogicError('%s does not implement XsdLiteral' % (cls,))

    def xsdLiteral (self):
        return self.__class__.XsdLiteral(self)

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
        for sc in cls.mro():
            if sc == object:
                continue
            if not issubclass(sc, _PST_mixin):
                return sc
        raise LogicError('No python type found for %s' % (cls,))

    @classmethod
    def XsdLength (cls, value):
        return len(cls.XsdToString(value))

    def xsdLength (self):
        return self.__class__.XsdLength(self)

    @classmethod
    def XsdConstraintsOK (self, string_value, value):
        # @todo implement this
        pass

    @classmethod
    def XsdToString (cls, value):
        return str(value)

    def xsdToString (cls):
        return self.__class__.XsdToString(self)

    @classmethod
    def XsdFromString (cls, string_value):
        return cls(string_value)

    def pythonLiteral (self):
        class_name = self.__class__.__name__
        return '%s(%s)' % (class_name, super(_PST_mixin, self).__str__())

class _List_mixin (_PST_mixin):
    """Marker to indicate that the datatype is a collection."""
    pass

# We use unicode as the Python type for anything that isn't a normal
# primitive type.  Presumably, only enumeration and pattern facets
# will be applied.
class anySimpleType (unicode, _PST_mixin):
    """http://www.w3.org/TR/xmlschema-2/#dt-anySimpleType"""
    _XsdBaseType = None
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return "u'%s'" % (value,)
# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).
    
class string (unicode, _PST_mixin):
    """string.
    
    http://www.w3.org/TR/xmlschema-2/#string"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return "'%s'" % (value,)

_PrimitiveDatatypes.append(string)

# It is illegal to subclass the bool type in Python, so we subclass
# int instead.
class boolean (int, _PST_mixin):
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

class decimal (types.FloatType, _PST_mixin):
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

class float (types.FloatType, _PST_mixin):
    """float.

    http://www.w3.org/TR/xmlschema-2/#float"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(float)

class double (types.FloatType, _PST_mixin):
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

class hexBinary (types.LongType, _PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    def __new__ (cls, value, *args, **kw):
        if isinstance(value, types.StringTypes):
            return super(hexBinary, cls).__new__(cls, '0x%s' % (value,), 16, *args, **kw)
        return super(hexBinary, cls).__new__(cls, value, *args, **kw)

    @classmethod
    def XsdLiteral (self, value):
        return '0x%x' % (value,)

_PrimitiveDatatypes.append(hexBinary)

class base64Binary (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(base64Binary)

class anyURI (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(anyURI)

class QName (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(QName)

class NOTATION (_PST_mixin):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
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

class NMTOKENS (types.ListType, _List_mixin):
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

class IDREFS (types.ListType, _List_mixin):
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    pass
_DerivedDatatypes.append(ENTITY)

class ENTITIES (types.ListType, _List_mixin):
    _ItemType = ENTITY
_ListDatatypes.append(ENTITIES)

class integer (long, _PST_mixin):
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

class int (types.IntType, _PST_mixin):
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
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreatePrimitiveInstance(name, schema.getTargetNamespace(), dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in _DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.XsdSuperType()]
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateDerivedInstance(name, schema.getTargetNamespace(), parent_std, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in _ListDatatypes:
        list_name = dtc.__name__.rstrip('_')
        element_name = dtc._ItemType.__name__.rstrip('_')
        element_std = schema._lookupTypeDefinition(element_name)
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateListInstance(list_name, schema.getTargetNamespace(), element_std, dtc))
        assert td.isResolved()
    return schema

