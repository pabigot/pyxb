"""Classes supporting XMLSchema Part 2: Datatypes.

We want the simple datatypes to be efficient Python values, but to
also hold specific constraints that don't apply to the Python types.
To do this, we subclass each STD.  Primitive STDs inherit from the
Python type that represents them, and from a _PST_mixin class which
adds in the constraint infrastructure.  Derived STDs inherit from the
parent STD.

There is an exception to this when the Python type associated with a
derived STD differs from the type associated with its parent STD: for
example, xsd:integer has a value range that requires it be represented
by a Python long, but xsd:int allows representation by a Python int.
In this case, the derived type is structured like a primitive type,
but the STD superclass is recorded in a class variable _XsdBaseType.

"""

from PyWXSB.exceptions_ import *
import structures as xsc
import types

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

#"""http://www/Documentation/W3C/www.w3.org/TR/2001/REC-xmlschema-1-20010502/index.html#key-urType"""
# NB: anyType is a ComplexTypeDefinition instance; haven't figured out
# how to deal with that yet.

class _PST_mixin (object):
    _Facets = []

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
    def XsdLength (cls, value):
        return len(cls.XsdToString(value))

    def xsdLength (self):
        return self.__class__.XsdLength(self)

    @classmethod
    def XsdConstraintsOK (self, string_value, value):
        pass

    @classmethod
    def XsdToString (cls, value):
        return str(value)

    def xsdToString (cls):
        return self.__class__.XsdToString(self)

# We use unicode as the Python type for anything that isn't a normal
# primitive type.  Presumably, only enumeration and pattern facets
# will be applied.
class anySimpleType (unicode, _PST_mixin):
    """http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#dt-anySimpleType"""
    _XsdBaseType = None

    @classmethod
    def XsdLiteral (cls, value):
        return "u'%s'" % (value,)

# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).
    
class string (unicode, _PST_mixin):
    """string.
    
    http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#string"""
    _XsdBaseType = anySimpleType

    @classmethod
    def XsdLiteral (cls, value):
        return "'%s'" % (value,)

_PrimitiveDatatypes.append(string)

# It is illegal to subclass the bool type in Python, so we subclass
# int instead.
class boolean (int, _PST_mixin):
    """boolean.

    http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#boolean"""
    _XsdBaseType = anySimpleType
    
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
        if value in (1, 0, 'true', 'false'):
            if value in (1, 'true'):
                iv = True
            else:
                iv = False
            return super(boolean, cls).__new__(cls, iv, *args, **kw)
        raise ValueError('[xsd:boolean] Initializer "%s" not valid for type' % (value,))


_PrimitiveDatatypes.append(boolean)

class decimal (float, _PST_mixin):
    """decimal.
    
    http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#decimal

    @todo The Python base type for this is wrong. Consider
    http://code.google.com/p/mpmath/.

    """
    _XsdBaseType = anySimpleType

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(decimal)

class float (float, _PST_mixin):
    """float.

    http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#float"""
    _XsdBaseType = anySimpleType

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(float)

class double (float, _PST_mixin):
    _XsdBaseType = anySimpleType

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(double)

class duration (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(duration)

class dateTime (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(dateTime)

class time (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(time)

class date (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(date)

class gYearMonth (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(gYearMonth)

class gYear (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(gYear)

class gMonthDay (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(gMonthDay)

class gDay (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(gDay)

class gMonth (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(gMonth)

class hexBinary (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(hexBinary)

class base64Binary (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(base64Binary)

class anyURI (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(anyURI)

class QName (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(QName)

class NOTATION (_PST_mixin):
    _XsdBaseType = anySimpleType
_PrimitiveDatatypes.append(NOTATION)

class normalizedString (string):
    pass
_DerivedDatatypes.append(normalizedString)

class token (normalizedString):
    pass
_DerivedDatatypes.append(token)

class language (token):
    pass
_DerivedDatatypes.append(language)

class NMTOKEN (token):
    pass
_DerivedDatatypes.append(NMTOKEN)
_ListDatatypes.append( ( 'NMTOKENS', 'NMTOKEN' ) )

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
_ListDatatypes.append( ( 'IDREFS', 'IDREF' ) )

class ENTITY (NCName):
    pass
_DerivedDatatypes.append(ENTITY)
_ListDatatypes.append( ( 'ENTITIES', 'ENTITY' ) )

class integer (long, _PST_mixin):
    """integer.

    http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#integer"""
    _XsdBaseType = decimal
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
        pts_std_map.setdefault(dtc, td)
    for dtc in _DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.XsdSuperType()]
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateDerivedInstance(name, schema.getTargetNamespace(), parent_std, dtc))
        assert td.isResolved()
        pts_std_map.setdefault(dtc, td)
    for (list_name, element_name) in _ListDatatypes:
        element_std = schema._lookupTypeDefinition(element_name)
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateListInstance(list_name, schema.getTargetNamespace(), element_std))
        assert td.isResolved()
    return schema
