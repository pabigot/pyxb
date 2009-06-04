# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Classes supporting U{XMLSchema Part 2: Datatypes<http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html>}.

Each L{simple type definition<pyxb.xmlschema.structures.SimpleTypeDefinition>} component
instance is paired with at most one L{basis.simpleTypeDefinition}
class, which is a subclass of a Python type augmented with facets and
other constraining information.  This file contains the definitions of
these types.

We want the simple datatypes to be efficient Python values, but to
also hold specific constraints that don't apply to the Python types.
To do this, we subclass each PST.  Primitive PSTs inherit from the
Python type that represents them, and from a
pyxb.binding.basis.simpleTypeDefinition class which adds in the
constraint infrastructure.  Derived PSTs inherit from the parent PST.

There is an exception to this when the Python type best suited for a
derived SimpleTypeDefinition differs from the type associated with its
parent STD: for example, L{xsd:integer<integer>} has a value range
that requires it be represented by a Python C{long}, but
L{xsd:int<int>} allows representation by a Python C{int}.  In this
case, the derived PST class is structured like a primitive type, but
the PST associated with the STD superclass is recorded in a class
variable C{_XsdBaseType}.

Note the strict terminology: "datatype" refers to a class which is a
subclass of a Python type, while "type definition" refers to an
instance of either SimpleTypeDefinition or ComplexTypeDefinition.

"""

from pyxb.exceptions_ import *
import types
import pyxb.namespace
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
    """See U{http://www.w3.org/TR/xmlschema-2/#dt-anySimpleType}"""
    _XsdBaseType = None
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anySimpleType')

    @classmethod
    def XsdLiteral (cls, value):
        return value
# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).
    
class string (basis.simpleTypeDefinition, unicode):
    """string.
    
    U{http://www.w3.org/TR/xmlschema-2/#string}"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('string')

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
class boolean (basis.simpleTypeDefinition, types.IntType):
    """boolean.

    U{http://www.w3.org/TR/xmlschema-2/#boolean}"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('boolean')
    
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
    
    U{http://www.w3.org/TR/xmlschema-2/#decimal}

    @todo: The Python base type for this is wrong. Consider
    U{http://code.google.com/p/mpmath/}.

    """
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('decimal')

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(decimal)

class float (basis.simpleTypeDefinition, types.FloatType):
    """float.

    U{http://www.w3.org/TR/xmlschema-2/#float}"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('float')

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(float)

class double (basis.simpleTypeDefinition, types.FloatType):
    """double.

    U{http://www.w3.org/TR/xmlschema-2/#double}"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('double')

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

_PrimitiveDatatypes.append(double)

import time as python_time
import datetime

class duration (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('duration')
_PrimitiveDatatypes.append(duration)

class _TimeZone (datetime.tzinfo):
    """A tzinfo subclass that helps deal with UTC conversions"""

    # Regular expression that matches valid ISO8601 time zone suffixes
    __Lexical_re = re.compile('^([-+])(\d\d):(\d\d)$')

    # The offset in minutes east of UTC.
    __utcOffset = 0

    def __init__ (self, spec=None, flip=False):
        """Create a time zone instance.

        If spec is not None, it must conform to the ISO8601 time zone
        sequence (Z, or [+-]HH:MM).

        If flip is True, the time zone offset is flipped, resulting in
        the conversion from localtime to UTC rather than the default
        of UTC to localtime.
        """

        if spec is None:
            return
        if 'Z' == spec:
            return
        match = self.__Lexical_re.match(spec)
        if match is None:
            raise ValueError('Bad time zone: %s' % (spec,))
        self.__utcOffset = int(match.group(2)) * 60 + int(match.group(3))
        if '-' == match.group(1):
            self.__utcOffset = - self.__utcOffset
        if flip:
            self.__utcOffset = - self.__utcOffset

    def utcoffset (self, dt):
        return datetime.timedelta(minutes=self.__utcOffset)

    def tzname (self, dt):
        if 0 == self.__utcOffset:
            return 'UTC'
        if 0 > self.__utcOffset:
            return 'UTC-%02d%02d' % divmod(-self.__utcOffset, 60)
            return 'UTC+%02d%02d' % divmod(self.__utcOffset, 60)
    
    def dst (self, dt):
        return datetime.timedelta()


class dateTime (basis.simpleTypeDefinition, datetime.datetime):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#dateTime}

    This class uses the Python C{datetime.datetime} class as its
    underlying representation.  Note that per the XMLSchema spec, all
    dateTime objects are in UTC, and that timezone information in the
    string representation in XML is an indication of the local time
    zone's offset from UTC.  Presence of time zone information in the
    lexical space is preserved through the value of the L{hasTimeZone()}
    field.
    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('dateType')

    __Lexical_re = re.compile('^(?P<negYear>-?)(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?P<fracsec>\.\d*)?(?P<tzinfo>Z|[-+]\d\d:\d\d)?$')

    # The fields in order of appearance in a time.struct_time instance
    __Fields = ( 'year', 'month', 'day', 'hour', 'minute', 'second' )
    # All non-tzinfo keywords for datetime constructor
    __Fields_us = __Fields + ('microsecond',)
    
    __hasTimeZone = False
    def hasTimeZone (self):
        """True iff the time represented included time zone information.

        Whether True or not, the moment denoted by an instance is
        assumed to be in UTC.  That state is expressed in the lexical
        space iff hasTimeZone is True.
        """
        return self.__hasTimeZone

    def __new__ (cls, *args, **kw):
        if 0 == len(args):
            now = python_time.gmtime()
            args = (datetime.datetime(*(now[:7])),)
        value = args[0]
        tzoffs = None
        ctor_kw = { }
        if isinstance(value, types.StringTypes):
            match = cls.__Lexical_re.match(value)
            if match is None:
                raise BadTypeValueError('Value not in dateTime lexical space') 
            match_map = match.groupdict()
            for f in cls.__Fields:
                ctor_kw[f] = int(match_map[f])
            if match_map['negYear']:
                ctor_kw['year'] = - year
            if match_map['fracsec']:
                ctor_kw['microsecond'] = int(1000000 * float('0%s' % (match_map['fracsec'],)))
            if match_map['tzinfo']:
                ctor_kw['tzinfo'] = _TimeZone(match_map['tzinfo'], flip=True)
        elif isinstance(value, datetime.datetime):
            for f in cls.__Fields_us:
                ctor_kw[f] = getattr(value, f)
            if value.tzinfo is not None:
                ctor_kw['tzinfo'] = _TimeZone(value.tzinfo.utcoffset(), flip=True)
        else:
            raise BadTypeValueError('Unexpected type %s' % (type(value),))
        tzoffs = ctor_kw.pop('tzinfo', None)
        has_time_zone = False
        if tzoffs is not None:
            dt = datetime.datetime(tzinfo=tzoffs, **ctor_kw)
            dt = tzoffs.fromutc(dt)
            ctor_kw = { }
            [ ctor_kw.setdefault(_field, getattr(dt, _field)) for _field in cls.__Fields_us ]
            has_time_zone = True
            
        year = ctor_kw.pop('year')
        month = ctor_kw.pop('month')
        day = ctor_kw.pop('day')
        kw.update(ctor_kw)
        rv = super(dateTime, cls).__new__(cls, year, month, day, **kw)
        rv.__hasTimeZone = has_time_zone
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        iso = value.isoformat()
        if 0 <= iso.find('.'):
            iso = iso.rstrip('0')
        if value.hasTimeZone():
            iso += 'Z'
        return iso

_PrimitiveDatatypes.append(dateTime)

class time (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('time')
_PrimitiveDatatypes.append(time)

class date (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('date')
_PrimitiveDatatypes.append(date)

class gYearMonth (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYearMonth')
_PrimitiveDatatypes.append(gYearMonth)

class gYear (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYear')
_PrimitiveDatatypes.append(gYear)

class gMonthDay (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonthDay')
_PrimitiveDatatypes.append(gMonthDay)

class gDay (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gDay')
_PrimitiveDatatypes.append(gDay)

class gMonth (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonth')
_PrimitiveDatatypes.append(gMonth)

class hexBinary (basis.simpleTypeDefinition, types.LongType):
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('hexBinary')

    __length = None
    def length (self):
        """Return the length of the value, in octets."""
        return self.__length

    @classmethod
    def _ConvertString (cls, text):
        """Convert a sequence of pairs of hex digits into a length (in
        octets) and a binary value."""
        assert isinstance(text, types.StringTypes)
        value = 0L
        length = 0
        while (length < len(text)):
            v = ord(text[length].lower())
            if (ord('0') <= v) and (v <= ord('9')):
                value = (value << 4) + v - ord('0')
            elif (ord('a') <= v) and (v <= ord('f')):
                value = (value << 4) + v - ord('a') + 10
            else:
                raise BadTypeValueError('Non-hexadecimal values in %s' % (cls.__class__.__name__,))
            length += 1
        if 0 == length:
            raise BadTypeValueError('%s must be non-empty string' % (cls.__class__.__name__,))
        if (length & 0x01):
            raise BadTypeValueError('%s value ends mid-octet' % (cls.__class__.__name__,))
        return (length >> 1, value)

    @classmethod
    def _ConvertValue (cls, value):
        """Given an integral value, return a pair consisting of the
        number of octets required to represent the value, and the
        value."""
        length = 0
        if 0 == value:
            length = 1
        else:
            mv = value
            while (0 != mv):
                length += 1
                mv = mv >> 4
            length = (length+1) >> 1
        return (length, value)

    def __new__ (cls, value, *args, **kw):
        if isinstance(value, types.StringTypes):
            (length, binary_value) = cls._ConvertString(value)
        else:
            (length, binary_value) = cls._ConvertValue(value)
        rv = super(hexBinary, cls).__new__(cls, binary_value, *args, **kw)
        rv.__length = length
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        mv = value
        length = value.length()
        pieces = []
        while (0 < length):
            pieces.append('%2.2X' % (mv & 0xFF,))
            mv = mv >> 8
            length -= 1
        pieces.reverse()
        return ''.join(pieces)

    @classmethod
    def XsdValueLength (cls, value):
        return value.length()

_PrimitiveDatatypes.append(hexBinary)

class base64Binary (basis.simpleTypeDefinition):
    """@attention: Not implemented"""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('base64Binary')

    @classmethod
    def XsdValueLength (cls, value):
        raise NotImplementedError('No length calculation for base64Binary')

_PrimitiveDatatypes.append(base64Binary)

class anyURI (basis.simpleTypeDefinition, types.UnicodeType):
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anyURI')

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

    @classmethod
    def XsdLiteral (cls, value):
        return unicode(value)

_PrimitiveDatatypes.append(anyURI)

class QName (basis.simpleTypeDefinition, unicode):
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('QName')

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

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        if not isinstance(value, types.StringTypes):
            raise BadTypeValueError('%s value must be a string' % (cls.__name__,))
        if 0 <= value.find(':'):
            (prefix, local) = value.split(':', 1)
            if (NCName._ValidRE.match(prefix) is None) or (NCName._ValidRE.match(local) is None):
                raise BadTypeValueError('%s lexical/value space violation for "%s"' % (cls.__name__, value))
        else:
            if NCName._ValidRE.match(value) is None:
                raise BadTypeValueError('%s lexical/value space violation for "%s"' % (cls.__name__, value))
        super_fn = getattr(super(QName, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)


_PrimitiveDatatypes.append(QName)

class NOTATION (basis.simpleTypeDefinition):
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NOTATION')

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
    
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('normalizedString')

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
        if not isinstance(value, types.StringTypes):
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
    
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('token')

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
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('language')
    _ValidRE = re.compile('^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$')
_DerivedDatatypes.append(language)

class NMTOKEN (token):
    """See http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Nmtoken

    NMTOKEN is an identifier that can start with any character that is
    legal in it."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NMTOKEN')
    _ValidRE = re.compile('^[-_.:A-Za-z0-9]*$')
_DerivedDatatypes.append(NMTOKEN)

class NMTOKENS (basis.STD_list):
    _ItemType = NMTOKEN
_ListDatatypes.append(NMTOKENS)

class Name (token):
    """See http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Name"""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('Name')
    _ValidRE = re.compile('^[A-Za-z_:][-_.:A-Za-z0-9]*$')
_DerivedDatatypes.append(Name)

class NCName (Name):
    """See http://www.w3.org/TR/1999/REC-xml-names-19990114/index.html#NT-NCName"""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NCName')
    _ValidRE = re.compile('^[A-Za-z_][-_.A-Za-z0-9]*$')
_DerivedDatatypes.append(NCName)

class ID (NCName):
    # Lexical and value space match that of parent NCName
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ID')
    pass
_DerivedDatatypes.append(ID)

class IDREF (NCName):
    # Lexical and value space match that of parent NCName
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('IDREF')
    pass
_DerivedDatatypes.append(IDREF)

class IDREFS (basis.STD_list):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('IDREFS')
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    # Lexical and value space match that of parent NCName; we're gonna
    # ignore the additioanl requirement that it be declared as an
    # unparsed entity
    #
    # @todo Don't ignore the requirement that this be declared as an
    # unparsed entity.
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ENTITY')
    pass
_DerivedDatatypes.append(ENTITY)

class ENTITIES (basis.STD_list):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ENTITIES')
    _ItemType = ENTITY
_ListDatatypes.append(ENTITIES)

class integer (basis.simpleTypeDefinition, types.LongType):
    """integer.

    http://www.w3.org/TR/xmlschema-2/#integer"""
    _XsdBaseType = decimal
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('integer')

    @classmethod
    def XsdLiteral (cls, value):
        return '%d' % (value,)

_DerivedDatatypes.append(integer)

class nonPositiveInteger (integer):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('nonPositiveInteger')
_DerivedDatatypes.append(nonPositiveInteger)

class negativeInteger (nonPositiveInteger):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('negativeInteger')
_DerivedDatatypes.append(negativeInteger)

class long (integer):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('long')
_DerivedDatatypes.append(long)

class int (basis.simpleTypeDefinition, types.IntType):
    _XsdBaseType = long
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('int')

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

    pass
_DerivedDatatypes.append(int)

class short (int):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('short')
_DerivedDatatypes.append(short)

class byte (short):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('byte')
_DerivedDatatypes.append(byte)

class nonNegativeInteger (integer):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('nonNegativeInteger')
_DerivedDatatypes.append(nonNegativeInteger)

class unsignedLong (nonNegativeInteger):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedLong')
_DerivedDatatypes.append(unsignedLong)

class unsignedInt (unsignedLong):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedInt')
_DerivedDatatypes.append(unsignedInt)

class unsignedShort (unsignedInt):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedShort')
_DerivedDatatypes.append(unsignedShort)

class unsignedByte (unsignedShort):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedByte')
_DerivedDatatypes.append(unsignedByte)

class positiveInteger (nonNegativeInteger):
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('positiveInteger')
_DerivedDatatypes.append(positiveInteger)

import datatypes_facets
import content

class anyType (basis.complexTypeDefinition):
    """http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType"""
    @classmethod
    def Factory (cls, *args, **kw):
        return anyType()

    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anyType')
    _ContentTypeTag = basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    
    # Generate from tests/schemas/anyType.xsd
    _ContentModel = content.ContentModel(state_map = {
      1 : content.ContentModelState(state=1, is_final=True, transitions=[
        content.ContentModelTransition(term=content.Wildcard(process_contents=content.Wildcard.PC_lax, namespace_constraint=content.Wildcard.NC_any), next_state=1, element_use=None),
    ])
})

