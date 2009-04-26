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
import re

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
        raise BadTypeValueError('[xsd:boolean] Initializer "%s" not valid for type' % (value,))


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
    """See http:///www.w3.org/TR/xmlschema-2/index.html#normalizedString

    Normalized strings can't have carriage returns, linefeeds, or
    tabs in them."""

    # All descendents of normalizedString constrain the lexical/value
    # space in some way.  Subclasses should set the _ValidRE class
    # variable to a compiled regular expression that matches valid
    # input, or the _InvalidRE class variable to a compiled regular
    # expression that detects invalid inputs.
    #
    # Alternatively, subclasses can override the _ValidateString
    # class.
    
    # @todo Implement pattern constraints and just rely on them

    # No CR, LF, or TAB
    __BadChars = re.compile("[\r\n\t]")

    _ValidRE = None
    _InvalidRE = None
    
    @classmethod
    def __ValidateString (cls, value):
        # This regular expression doesn't work.  Don't know why.
        #if cls.__BadChars.match(value) is not None:
        #    raise BadTypeValueError('CR/NL/TAB characters illegal in %s' % (cls.__name__,))
        if (0 <= value.find("\n")) or (0 <= value.find("\r")) or (0 <= value.find("\t")):
            raise BadTypeValueError('CR/NL/TAB characters illegal in %s' % (cls.__name__,))
        if cls._ValidRE is not None:
            match_object = cls._ValidRE.match(value)
            if match_object is None:
                raise BadTypeValueError('%s pattern constraint violation for "%s"' % (cls.__name__, value))
        if cls._InvalidRE is not None:
            match_object = cls._InvalidRE.match(value)
            if not (match_object is None):
                raise BadTypeValueError('%s pattern constraint violation for "%s"' % (cls.__name__, value))
        return True

    @classmethod
    def _ValidateString_va (cls, value):
        """Post-extended method to validate that a string matches a given pattern.

        If you can express the valid strings as a compiled regular
        expression in the class variable _ValidRE, or the invalid
        strings as a compiled regular expression in the class variable
        _InvalidRE, you can just use those.  If the acceptable matches
        are any trickier, you should invoke the superclass
        implementation, and if it returns True then perform additional
        tests."""
        super_fn = getattr(super(normalizedString, cls), '_ValidateString_va', lambda *a,**kw: True)
        if not super_fn(value):
            return False
        return cls.__ValidateString(value)

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        if not isinstance(value, (str, unicode)):
            raise BadTypeValueError('%s value must be a string' % (cls.__name__,))
        if not cls._ValidateString_va(value):
            raise BadTypeValueError('%s lexical/value space violation for "%s"' % (cls.__name__, value))
        super_fn = getattr(super(normalizedString, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)

_DerivedDatatypes.append(normalizedString)
assert normalizedString.XsdSuperType() == string

class token (normalizedString):
    """See http:///www.w3.org/TR/xmlschema-2/index.html#token

    Tokens cannot leading or trailing space characters; any
    carriage return, line feed, or tab characters; nor any occurrence
    of two or more consecutive space characters."""
    
    @classmethod
    def _ValidateString_va (cls, value):
        super_fn = getattr(super(token, cls), '_ValidateString_va', lambda *a,**kw: True)
        if not super_fn(value):
            return False
        if value.startswith(" "):
            raise BadTypeValueError('Leading spaces in token')
        if value.endswith(" "):
            raise BadTypeValueError('Trailing spaces in token')
        if 0 <= value.find('  '):
            raise BadTypeValueError('Multiple internal spaces in token')
        return True
_DerivedDatatypes.append(token)

class language (token):
    """See http:///www.w3.org/TR/xmlschema-2/index.html#language"""
    _ValidRE = re.compile('^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$')
_DerivedDatatypes.append(language)

class NMTOKEN (token):
    """See http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Nmtoken

    NMTOKEN is an identifier that can start with any character that is
    legal in it."""
    _ValidRE = re.compile('^[-_.:A-Za-z0-9]*$')
_DerivedDatatypes.append(NMTOKEN)

class NMTOKENS (basis.STD_list):
    _ItemType = NMTOKEN
_ListDatatypes.append(NMTOKENS)

class Name (token):
    """See http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Name"""
    _ValidRE = re.compile('^[A-Za-z_:][-_.:A-Za-z0-9]*$')
_DerivedDatatypes.append(Name)

class NCName (Name):
    """See http://www.w3.org/TR/1999/REC-xml-names-19990114/index.html#NT-NCName"""
    _ValidRE = re.compile('^[A-Za-z_][-_.A-Za-z0-9]*$')
_DerivedDatatypes.append(NCName)

class ID (NCName):
    # Lexical and value space match that of parent NCName
    pass
_DerivedDatatypes.append(ID)

class IDREF (NCName):
    # Lexical and value space match that of parent NCName
    pass
_DerivedDatatypes.append(IDREF)

class IDREFS (basis.STD_list):
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    # Lexical and value space match that of parent NCName; we're gonna
    # ignore the additioanl requirement that it be declared as an
    # unparsed entity
    #
    # @todo Don't ignore the requirement that this be declared as an
    # unparsed entity.
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
