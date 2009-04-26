"""Classes supporting XMLSchema Part 2: Datatypes.

Each SimpleTypeDefinition component instance is paired with at most
one PythonSimpleType (PST), which is a subclass of a Python type
augmented with facets and other constraining information.  This file
contains the definitions of these types.

We want the simple datatypes to be efficient Python values, but to
also hold specific constraints that don't apply to the Python types.
To do this, we subclass each PST.  Primitive PSTs inherit from the
Python type that represents them, and from a
pyxb.binding.basis.simpleTypeDefinition class which adds in the
constraint infrastructure.  Derived PSTs inherit from the parent PST.

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

from pyxb.exceptions_ import *
import types
import pyxb.Namespace as Namespace
import pyxb.utils.domutils as domutils
import pyxb.utils.utility as utility
import basis

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

# We use unicode as the Python type for anything that isn't a normal
# primitive type.  Presumably, only enumeration and pattern facets
# will be applied.
class anySimpleType (basis.simpleTypeDefinition, unicode):
    """http://www.w3.org/TR/xmlschema-2/#dt-anySimpleType"""
    _XsdBaseType = None
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return value
# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).
    
class string (basis.simpleTypeDefinition, unicode):
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
class boolean (basis.simpleTypeDefinition, int):
    """boolean.

    http://www.w3.org/TR/xmlschema-2/#boolean"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    
    @classmethod
    def XsdLiteral (cls, value):
        if value:
            return 'true'
        return 'false'

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

class decimal (basis.simpleTypeDefinition, types.FloatType):
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

class float (basis.simpleTypeDefinition, types.FloatType):
    """float.

    http://www.w3.org/TR/xmlschema-2/#float"""
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(float)

class double (basis.simpleTypeDefinition, types.FloatType):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(double)

class duration (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(duration)

class dateTime (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(dateTime)

class time (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(time)

class date (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(date)

class gYearMonth (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gYearMonth)

class gYear (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gYear)

class gMonthDay (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gMonthDay)

class gDay (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gDay)

class gMonth (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
_PrimitiveDatatypes.append(gMonth)

class hexBinary (basis.simpleTypeDefinition, types.LongType):
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

class base64Binary (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdValueLength (cls, value):
        raise NotImplementedError('No length calculation for base64Binary')

_PrimitiveDatatypes.append(base64Binary)

class anyURI (basis.simpleTypeDefinition, types.UnicodeType):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

    @classmethod
    def XsdLiteral (cls, value):
        return unicode(value)

_PrimitiveDatatypes.append(anyURI)

class QName (basis.simpleTypeDefinition, unicode):
    _XsdBaseType = anySimpleType
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdValueLength (cls, value):
        """Section 4.3.1.3: Legacy length return None to indicate no check"""
        return None

    __localName = None
    __prefix = None

    def prefix (self):
        """Return the prefix portion of the QName, or None if the name is not qualified."""
        if self.__localName is None:
            self.__resolveLocals()
        return self.__prefix

    def localName (self):
        """Return the local portion of the QName."""
        if self.__localName is None:
            self.__resolveLocals()
        return self.__localName

    def __resolveLocals (self):
        if self.find(':'):
            (self.__prefix, self.__localName) = self.split(':', 1)
        else:
            self.__localName = unicode(self)

    @classmethod
    def XsdLiteral (cls, value):
        return unicode(value)

_PrimitiveDatatypes.append(QName)

class NOTATION (basis.simpleTypeDefinition):
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

class NMTOKENS (basis.STD_list):
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

class IDREFS (basis.STD_list):
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    pass
_DerivedDatatypes.append(ENTITY)

class ENTITIES (basis.STD_list):
    _ItemType = ENTITY
_ListDatatypes.append(ENTITIES)

class integer (basis.simpleTypeDefinition, long):
    """integer.

    http://www.w3.org/TR/xmlschema-2/#integer"""
    _XsdBaseType = decimal
    _Namespace = Namespace.XMLSchema
    @classmethod
    def XsdLiteral (cls, value):
        return '%d' % (value,)

_DerivedDatatypes.append(integer)

class nonPositiveInteger (integer):
    pass
_DerivedDatatypes.append(nonPositiveInteger)

class negativeInteger (nonPositiveInteger):
    pass
_DerivedDatatypes.append(negativeInteger)

class long (integer):
    pass
_DerivedDatatypes.append(long)

class int (basis.simpleTypeDefinition, types.IntType):
    _XsdBaseType = long
    _Namespace = Namespace.XMLSchema

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

    pass
_DerivedDatatypes.append(int)

class short (int):
    pass
_DerivedDatatypes.append(short)

class byte (short):
    pass
_DerivedDatatypes.append(byte)

class nonNegativeInteger (integer):
    pass
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

import datatypes_facets
import content

class anyType (basis.CTD_mixed):
    """http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType"""
    @classmethod
    def Factory (cls, *args, **kw):
        return anyType()

    _Content = content.Particle(1, 1,
                                content.ModelGroup(content.ModelGroup.C_SEQUENCE,
                                                   [ content.Particle(0, None,
                                                                      content.Wildcard(namespace_constraint=content.Wildcard.NC_any,
                                                                                       process_contents=content.Wildcard.PC_lax)
                                                                      ) # end Particle
                                                     ]) # end ModelGroup
                                ) # end Particle
