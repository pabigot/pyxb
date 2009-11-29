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

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        if 0 < len(args):
            value = args[0]
            args = args[1:]
            if value in (1, 0, '1', '0', 'true', 'false'):
                if value in (1, '1', 'true'):
                    iv = True
                else:
                    iv = False
                return super(boolean, cls).__new__(cls, iv, *args, **kw)
            raise BadTypeValueError('[xsd:boolean] Initializer "%s" not valid for type' % (value,))
        return super(boolean, cls).__new__(cls, *args, **kw)

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

class duration (basis.simpleTypeDefinition, datetime.timedelta):
    """U{http://www.w3.org/TR/xmlschema-2/#duration}

    This class uses the Python C{datetime.timedelta} class as its
    underlying representation.  This works fine as long as no months
    or years are involved, and no negative durations are involved.
    Because the XML Schema value space is so much larger, it is kept
    distinct from the Python value space, which reduces to integral
    days, seconds, and microseconds.

    In other words, the implementation of this type is a little
    shakey.

    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('duration')

    __Lexical_re = re.compile('^(?P<neg>-?)P((?P<years>\d+)Y)?((?P<months>\d+)M)?((?P<days>\d+)D)?(?P<Time>T((?P<hours>\d+)H)?((?P<minutes>\d+)M)?(((?P<seconds>\d+)(?P<fracsec>\.\d+)?)S)?)?$')

    # We do not use weeks
    __XSDFields = ( 'years', 'months', 'days', 'hours', 'minutes', 'seconds' )
    __PythonFields = ( 'days', 'seconds', 'microseconds', 'minutes', 'hours' )

    def negativeDuration (self):
        return self.__negativeDuration
    __negativeDuration = None

    def durationData (self):
        return self.__durationData
    __durationData = None

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        text = args[0]
        have_kw_update = False
        if isinstance(text, (str, unicode)):
            match = cls.__Lexical_re.match(text)
            if match is None:
                raise BadTypeValueError('Value "%s" not in %s lexical space' % (text, cls._ExpandedName)) 
            match_map = match.groupdict()
            if 'T' == match_map.get('Time', None):
                # Can't have T without additional time information
                raise BadTypeValueError('Value "%s" not in %s lexical space' % (text, cls._ExpandedName)) 

            negative_duration = ('-' == match_map.get('neg', None))

            fractional_seconds = 0.0
            if match_map.get('fracsec', None) is not None:
                fractional_seconds = types.FloatType('0%s' % (match_map['fracsec'],))
                usec = types.IntType(1000000 * fractional_seconds)
                if negative_duration:
                    kw['microseconds'] = - usec
                else:
                    kw['microseconds'] = usec
            else:
                # Discard any bogosity passed in by the caller
                kw.pop('microsecond', None)

            data = { }
            for fn in cls.__XSDFields:
                v = match_map.get(fn, 0)
                if v is None:
                    v = 0
                data[fn] = types.IntType(v)
                if fn in cls.__PythonFields:
                    if negative_duration:
                        kw[fn] = - data[fn]
                    else:
                        kw[fn] = data[fn]
            data['seconds'] += fractional_seconds
            have_kw_update = True
        elif isinstance(text, cls):
            data = text.durationData()
            negative_duration = text.negativeDuration()
        elif isinstance(text, datetime.timedelta):
            data = { 'days' : text.days,
                     'seconds' : text.seconds + (text.microseconds / 1000000.0) }
            negative_duration = (0 > data['days'])
            if negative_duration:
                data['days'] = 1 - data['days']
                data['seconds'] = 24 * 60 * 60.0 - data['seconds']
            data['minutes'] = 0
            data['hours'] = 0
        if not have_kw_update:
            rem_time = data['seconds']
            use_seconds = rem_time
            if (0 != (rem_time % 1)):
                data['microseconds'] = types.IntType(1000000 * (rem_time % 1))
                rem_time = rem_time // 1
            if 60 <= rem_time:
                data['seconds'] = rem_time % 60
                rem_time = data['minutes'] + (rem_time // 60)
            if 60 <= rem_time:
                data['minutes'] = rem_time % 60
                rem_time = data['hours'] + (rem_time // 60)
            data['hours'] = rem_time % 24
            data['days'] += (rem_time // 24)
            for fn in cls.__PythonFields:
                if fn in data:
                    if negative_duration:
                        kw[fn] = - data[fn]
                    else:
                        kw[fn] = data[fn]
                else:
                    kw.pop(fn, None)
            kw['microseconds'] = data.pop('microseconds', 0)
            data['seconds'] += kw['microseconds'] / 1000000.0
            
        rv = super(duration, cls).__new__(cls, **kw)
        rv.__durationData = data
        rv.__negativeDuration = negative_duration
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        elts = []
        if value.negativeDuration():
            elts.append('-')
        elts.append('P')
        for k in ( 'years', 'months', 'days' ):
            v = value.__durationData.get(k, 0)
            if 0 != v:
                elts.append('%d%s' % (v, k[0].upper()))
        time_elts = []
        for k in ( 'hours', 'minutes' ):
            v = value.__durationData.get(k, 0)
            if 0 != v:
                time_elts.append('%d%s' % (v, k[0].upper()))
        v = value.__durationData.get('seconds', 0)
        if 0 != v:
            time_elts.append('%gS' % (v,))
        if 0 < len(time_elts):
            elts.append('T')
            elts.extend(time_elts)
        return ''.join(elts)
        
_PrimitiveDatatypes.append(duration)

class _PyXBDateTime_base (basis.simpleTypeDefinition):

    __PatternMap = { '%Y' : '(?P<negYear>-?)(?P<year>\d{4,})'
                   , '%m' : '(?P<month>\d{2})'
                   , '%d' : '(?P<day>\d{2})'
                   , '%H' : '(?P<hour>\d{2})'
                   , '%M' : '(?P<minute>\d{2})'
                   , '%S' : '(?P<second>\d{2})(?P<fracsec>\.\d+)?'
                   , '%Z' : '(?P<tzinfo>Z|[-+]\d\d:\d\d)' }
    @classmethod
    def _DateTimePattern (cls, pattern):
        for (k, v) in cls.__PatternMap.items():
            pattern = pattern.replace(k, v)
        return pattern

    __Fields = ( 'year', 'month', 'day', 'hour', 'minute', 'second' )

    _DefaultYear = 1983
    _DefaultMonth = 6
    _DefaultDay = 18

    @classmethod
    def _LexicalToKeywords (cls, text, lexical_re):
        match = lexical_re.match(text)
        if match is None:
            raise BadTypeValueError('Value "%s" not in %s lexical space' % (text, cls._ExpandedName)) 
        match_map = match.groupdict()
        kw = { }
        for (k, v) in match_map.iteritems():
            if (k in cls.__Fields) and (v is not None):
                kw[k] = types.IntType(v)
        if '-' == match_map.get('negYear', None):
            kw['year'] = - kw['year']
        if match_map.get('fracsec', None) is not None:
            kw['microsecond'] = types.IntType(1000000 * types.FloatType('0%s' % (match_map['fracsec'],)))
        else:
            # Discard any bogosity passed in by the caller
            kw.pop('microsecond', None)
        if match_map.get('tzinfo', None) is not None:
            kw['tzinfo'] = pyxb.utils.utility.UTCOffsetTimeZone(match_map['tzinfo'], flip=True)
        else:
            kw.pop('tzinfo', None)
        return kw

    @classmethod
    def _SetKeysFromPython_csc (cls, python_value, kw, fields):
        for f in fields:
            kw[f] = getattr(python_value, f)
        return getattr(super(_PyXBDateTime_base, cls), '_SetKeysFromPython_csc', lambda *a,**kw: None)(python_value, kw, fields)

    @classmethod
    def _SetKeysFromPython (cls, python_value, kw, fields):
        return cls._SetKeysFromPython_csc(python_value, kw, fields)

class _PyXBDateTimeZone_base (_PyXBDateTime_base):
    def hasTimeZone (self):
        """True iff the time represented included time zone information.

        Whether True or not, the moment denoted by an instance is
        assumed to be in UTC.  That state is expressed in the lexical
        space iff hasTimeZone is True.
        """
        return self.__hasTimeZone
    def _setHasTimeZone (self, has_time_zone):
        self.__hasTimeZone = has_time_zone
    __hasTimeZone = False

    @classmethod
    def _AdjustForTimezone (cls, kw):
        tzoffs = kw.pop('tzinfo', None)
        has_time_zone = kw.pop('_force_timezone', False)
        if tzoffs is not None:
            use_kw = kw.copy()
            use_kw.setdefault('year', cls._DefaultYear)
            use_kw.setdefault('month', cls._DefaultMonth)
            use_kw.setdefault('day', cls._DefaultDay)
            dt = datetime.datetime(tzinfo=tzoffs, **use_kw)
            dt = tzoffs.fromutc(dt)
            for k in kw.iterkeys():
                kw[k] = getattr(dt, k)
            has_time_zone = True
        return has_time_zone
        
    @classmethod
    def _SetKeysFromPython_csc (cls, python_value, kw, fields):
        if python_value.tzinfo is not None:
            kw['tzinfo'] = pyxb.utils.utility.UTCOffsetTimeZone(python_value.tzinfo.utcoffset(python_value), flip=True)
        else:
            kw.pop('tzinfo', None)
        return getattr(super(_PyXBDateTimeZone_base, cls), '_SetKeysFromPython_csc', lambda *a,**kw: None)(python_value, kw, fields)

class dateTime (_PyXBDateTimeZone_base, datetime.datetime):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#dateTime}

    This class uses the Python C{datetime.datetime} class as its
    underlying representation.  Note that per the XMLSchema spec, all
    dateTime objects are in UTC, and that timezone information in the
    string representation in XML is an indication of the local time
    zone's offset from UTC.  Presence of time zone information in the
    lexical space is preserved through the value of the L{hasTimeZone()}
    field.

    @warning: The value space of Python's C{datetime.datetime} class
    is more restricted than that of C{xs:datetime}.  As a specific
    example, Python does not support negative years or years with more
    than four digits.  For now, the convenience of having an object
    that is compatible with Python is more important than supporting
    the full value space.  In the future, the choice may be left up to
    the developer.
    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('dateTime')

    __Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%Y-%m-%dT%H:%M:%S%Z?$'))
    __Fields = ( 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'tzinfo' )
    
    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        ctor_kw = { }
        if 1 == len(args):
            value = args[0]
            if isinstance(value, types.StringTypes):
                ctor_kw.update(cls._LexicalToKeywords(value, cls.__Lexical_re))
            elif isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
                cls._SetKeysFromPython(value, ctor_kw, cls.__Fields)
                if isinstance(value, _PyXBDateTimeZone_base):
                    ctor_kw['_force_timezone'] = True
            elif isinstance(value, (types.IntType, types.LongType)):
                raise TypeError('function takes at least 3 arguments (%d given)' % (len(args),))
            else:
                raise BadTypeValueError('Unexpected type %s in %s' % (type(value), cls._ExpandedName))
        elif 3 <= len(args):
            for fi in range(len(cls.__Fields)):
                fn = cls.__Fields[fi]
                if fi < len(args):
                    ctor_kw[fn] = args[fi]
                elif fn in kw:
                    ctor_kw[fn] = kw[fn]
                kw.pop(fn, None)
                fi += 1
        else:
            raise TypeError('function takes at least 3 arguments (%d given)' % (len(args),))

        has_time_zone = cls._AdjustForTimezone(ctor_kw)
        kw.update(ctor_kw)
        year = kw.pop('year')
        month = kw.pop('month')
        day = kw.pop('day')
        rv = super(dateTime, cls).__new__(cls, year, month, day, **kw)
        rv._setHasTimeZone(has_time_zone)
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        iso = value.isoformat()
        if 0 <= iso.find('.'):
            iso = iso.rstrip('0')
        if value.hasTimeZone():
            iso += 'Z'
        return iso

    __UTCZone = pyxb.utils.utility.UTCOffsetTimeZone(0)
    __LocalZone = pyxb.utils.utility.LocalTimeZone()

    @classmethod
    def today (cls):
        """Return today.

        Just like datetime.datetime.today(), except this one sets a
        tzinfo field so it's clear the value is UTC."""
        return cls(datetime.datetime.now(cls.__UTCZone))

    def aslocal (self):
        """Returns a C{datetime.datetime} instance denoting the same
        time as this instance but adjusted to be in the local time
        zone.

        @rtype: C{datetime.datetime} (B{NOT} C{xsd.dateTime})
        """
        return self.replace(tzinfo=self.__UTCZone).astimezone(self.__LocalZone)

_PrimitiveDatatypes.append(dateTime)

class time (_PyXBDateTimeZone_base, datetime.time):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#time}

    This class uses the Python C{datetime.time} class as its
    underlying representation.  Note that per the XMLSchema spec, all
    dateTime objects are in UTC, and that timezone information in the
    string representation in XML is an indication of the local time
    zone's offset from UTC.  Presence of time zone information in the
    lexical space is preserved through the value of the
    L{hasTimeZone()} field.
    """
    
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('time')

    __Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%H:%M:%S%Z?$'))
    __Fields = ( 'hour', 'minute', 'second', 'microsecond' )
    
    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        ctor_kw = { }
        if 1 <= len(args):
            value = args[0]
            if isinstance(value, types.StringTypes):
                ctor_kw.update(cls._LexicalToKeywords(value, cls.__Lexical_re))
            elif isinstance(value, datetime.time):
                cls._SetKeysFromPython(value, ctor_kw, cls.__Fields)
            elif isinstance(value, (types.IntType, types.LongType)):
                for fn in range(min(len(args), len(cls.__Fields))):
                    ctor_kw[cls.__Fields[fn]] = args[fn]
            else:
                raise BadTypeValueError('Unexpected type %s' % (type(value),))

        has_time_zone = cls._AdjustForTimezone(ctor_kw)
        kw.update(ctor_kw)
        rv = super(time, cls).__new__(cls, **kw)
        rv._setHasTimeZone(has_time_zone)
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        iso = value.isoformat()
        if 0 <= iso.find('.'):
            iso = iso.rstrip('0')
        if value.hasTimeZone():
            iso += 'Z'
        return iso

_PrimitiveDatatypes.append(time)

class _PyXBDateOnly_base (_PyXBDateTime_base, datetime.date):
    _XsdBaseType = anySimpleType

    __DateFields = ( 'year', 'month', 'day' )
    _ISO_beginYear = 0
    _ISO_endYear = 4
    _ISO_beginMonth = 5
    _ISO_endMonth = 7
    _ISO_beginDay = 8
    _ISO_endDay = 10
    _ISOBegin = _ISO_beginYear
    _ISOEnd = _ISO_endDay

    def __getattribute__ (self, attr):
        ga = super(_PyXBDateOnly_base, self).__getattribute__
        cls = ga('__class__')
        if (attr in cls.__DateFields) and not (attr in cls._Fields):
            raise AttributeError(self, attr)
        return ga(attr)

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        ctor_kw = { }
        ctor_kw['year'] = cls._DefaultYear
        ctor_kw['month'] = cls._DefaultMonth
        ctor_kw['day'] = cls._DefaultDay
        if 1 == len(args):
            value = args[0]
            if isinstance(value, types.StringTypes):
                ctor_kw.update(cls._LexicalToKeywords(value, cls._Lexical_re))
            elif isinstance(value, datetime.date):
                cls._SetKeysFromPython(value, ctor_kw, cls._Fields)
            elif isinstance(value, (types.IntType, types.LongType)):
                if (1 != len(cls._Fields)):                
                    raise TypeError('function takes exactly %d arguments (%d given)' % (len(cls._Fields), len(args)))
                ctor_kw[cls._Fields[0]] = value
            else:
                raise BadTypeValueError('Unexpected type %s' % (type(value),))
        elif len(cls._Fields) == len(args):
            for fi in range(len(cls._Fields)):
                ctor_kw[cls._Fields[fi]] = args[fi]
        else:
            raise TypeError('function takes exactly %d arguments (%d given)' % (len(cls._Fields), len(args)))

        kw.update(ctor_kw)
        argv = []
        for f in cls.__DateFields:
            argv.append(kw.pop(f))
        return super(_PyXBDateOnly_base, cls).__new__(cls, *argv, **kw)

    @classmethod
    def XsdLiteral (cls, value):
        return value.isoformat()[cls._ISOBegin:cls._ISOEnd]

class date (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#date}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('date')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%Y-%m-%d$'))
    _Fields = ( 'year', 'month', 'day' )

_PrimitiveDatatypes.append(date)

class gYearMonth (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#gYearMonth}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYearMonth')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%Y-%m$'))
    _Fields = ( 'year', 'month' )
    _ISOEnd = _PyXBDateOnly_base._ISO_endMonth

_PrimitiveDatatypes.append(gYearMonth)

class gYear (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#gYear}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYear')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%Y$'))
    _Fields = ( 'year', )
    _ISOEnd = _PyXBDateOnly_base._ISO_endYear
_PrimitiveDatatypes.append(gYear)

class gMonthDay (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#gMonthDay}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonthDay')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%m-%d$'))
    _Fields = ( 'month', 'day' )
    _ISOBegin = _PyXBDateOnly_base._ISO_beginMonth
_PrimitiveDatatypes.append(gMonthDay)

class gDay (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#gDay}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gDay')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%d$'))
    _Fields = ( 'day', )
    _ISOBegin = _PyXBDateOnly_base._ISO_beginDay
_PrimitiveDatatypes.append(gDay)

class gMonth (_PyXBDateOnly_base):
    """U{http://www.w3.org/TR/xmlschema-2/index.html#gMonth}

    This class uses the Python C{datetime.date} class as its
    underlying representation.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonth')
    _Lexical_re = re.compile(_PyXBDateTime_base._DateTimePattern('^%m$'))
    _Fields = ( 'month', )
    _ISOBegin = _PyXBDateOnly_base._ISO_beginMonth
    _ISOEnd = _PyXBDateOnly_base._ISO_endMonth
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

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        value = args[0]
        rem_args = args[1:]
        if isinstance(value, types.StringTypes):
            (length, binary_value) = cls._ConvertString(value)
        else:
            (length, binary_value) = cls._ConvertValue(value)
        rv = super(hexBinary, cls).__new__(cls, binary_value, *rem_args, **kw)
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

class anyURI (basis.simpleTypeDefinition, unicode):
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
    # ignore the additional requirement that it be declared as an
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
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anyType')
    _ContentTypeTag = basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    _HasWildcardElement = True
    _AttributeWildcard = content.Wildcard(namespace_constraint=content.Wildcard.NC_any, process_contents=content.Wildcard.PC_lax)

    # Generate from tests/schemas/anyType.xsd
    _ContentModel = content.ContentModel(state_map = {
      1 : content.ContentModelState(state=1, is_final=True, transitions=[
        content.ContentModelTransition(term=content.Wildcard(process_contents=content.Wildcard.PC_lax, namespace_constraint=content.Wildcard.NC_any), next_state=1, element_use=None),
    ])
})

