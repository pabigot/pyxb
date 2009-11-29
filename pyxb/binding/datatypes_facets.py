"""Generated file that augments the standard schema L{datatype
definitions<pyxb.binding.datatypes>} with their respective
U{constraining facets<http://www.w3.org/TR/xmlschema-2/index.html#rf-facets>}.  At
one time, the C{maintainer/xsdfacet.py} script could be used to
generate this.  No idea if that's still true.
"""
import facets
from datatypes import *
gDay._CF_pattern = facets.CF_pattern()
gDay._CF_enumeration = facets.CF_enumeration(value_datatype=gDay)
gDay._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
gDay._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
gDay._CF_minInclusive = facets.CF_minInclusive(value_datatype=gDay)
gDay._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
gDay._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=gDay)
gDay._InitializeFacetMap(gDay._CF_pattern,
   gDay._CF_enumeration,
   gDay._CF_minExclusive,
   gDay._CF_whiteSpace,
   gDay._CF_minInclusive,
   gDay._CF_maxExclusive,
   gDay._CF_maxInclusive)
gMonthDay._CF_pattern = facets.CF_pattern()
gMonthDay._CF_enumeration = facets.CF_enumeration(value_datatype=gMonthDay)
gMonthDay._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
gMonthDay._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
gMonthDay._CF_minInclusive = facets.CF_minInclusive(value_datatype=gMonthDay)
gMonthDay._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
gMonthDay._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=gMonthDay)
gMonthDay._InitializeFacetMap(gMonthDay._CF_pattern,
   gMonthDay._CF_enumeration,
   gMonthDay._CF_minExclusive,
   gMonthDay._CF_whiteSpace,
   gMonthDay._CF_minInclusive,
   gMonthDay._CF_maxExclusive,
   gMonthDay._CF_maxInclusive)
gYearMonth._CF_pattern = facets.CF_pattern()
gYearMonth._CF_enumeration = facets.CF_enumeration(value_datatype=gYearMonth)
gYearMonth._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
gYearMonth._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
gYearMonth._CF_minInclusive = facets.CF_minInclusive(value_datatype=gYearMonth)
gYearMonth._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
gYearMonth._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=gYearMonth)
gYearMonth._InitializeFacetMap(gYearMonth._CF_pattern,
   gYearMonth._CF_enumeration,
   gYearMonth._CF_minExclusive,
   gYearMonth._CF_whiteSpace,
   gYearMonth._CF_minInclusive,
   gYearMonth._CF_maxExclusive,
   gYearMonth._CF_maxInclusive)
ENTITIES._CF_minLength = facets.CF_minLength(value=nonNegativeInteger(1))
ENTITIES._CF_maxLength = facets.CF_maxLength()
ENTITIES._CF_whiteSpace = facets.CF_whiteSpace()
ENTITIES._CF_length = facets.CF_length()
ENTITIES._CF_enumeration = facets.CF_enumeration(value_datatype=ENTITIES)
ENTITIES._CF_pattern = facets.CF_pattern()
ENTITIES._InitializeFacetMap(ENTITIES._CF_minLength,
   ENTITIES._CF_maxLength,
   ENTITIES._CF_whiteSpace,
   ENTITIES._CF_length,
   ENTITIES._CF_enumeration,
   ENTITIES._CF_pattern)
IDREFS._CF_minLength = facets.CF_minLength(value=nonNegativeInteger(1))
IDREFS._CF_maxLength = facets.CF_maxLength()
IDREFS._CF_whiteSpace = facets.CF_whiteSpace()
IDREFS._CF_length = facets.CF_length()
IDREFS._CF_enumeration = facets.CF_enumeration(value_datatype=IDREFS)
IDREFS._CF_pattern = facets.CF_pattern()
IDREFS._InitializeFacetMap(IDREFS._CF_minLength,
   IDREFS._CF_maxLength,
   IDREFS._CF_whiteSpace,
   IDREFS._CF_length,
   IDREFS._CF_enumeration,
   IDREFS._CF_pattern)
time._CF_pattern = facets.CF_pattern()
time._CF_enumeration = facets.CF_enumeration(value_datatype=time)
time._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
time._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
time._CF_minInclusive = facets.CF_minInclusive(value_datatype=time)
time._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
time._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=time)
time._InitializeFacetMap(time._CF_pattern,
   time._CF_enumeration,
   time._CF_minExclusive,
   time._CF_whiteSpace,
   time._CF_minInclusive,
   time._CF_maxExclusive,
   time._CF_maxInclusive)
date._CF_pattern = facets.CF_pattern()
date._CF_enumeration = facets.CF_enumeration(value_datatype=date)
date._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
date._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
date._CF_minInclusive = facets.CF_minInclusive(value_datatype=date)
date._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
date._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=date)
date._InitializeFacetMap(date._CF_pattern,
   date._CF_enumeration,
   date._CF_minExclusive,
   date._CF_whiteSpace,
   date._CF_minInclusive,
   date._CF_maxExclusive,
   date._CF_maxInclusive)
NMTOKENS._CF_minLength = facets.CF_minLength(value=nonNegativeInteger(1))
NMTOKENS._CF_maxLength = facets.CF_maxLength()
NMTOKENS._CF_whiteSpace = facets.CF_whiteSpace()
NMTOKENS._CF_length = facets.CF_length()
NMTOKENS._CF_enumeration = facets.CF_enumeration(value_datatype=NMTOKENS)
NMTOKENS._CF_pattern = facets.CF_pattern()
NMTOKENS._InitializeFacetMap(NMTOKENS._CF_minLength,
   NMTOKENS._CF_maxLength,
   NMTOKENS._CF_whiteSpace,
   NMTOKENS._CF_length,
   NMTOKENS._CF_enumeration,
   NMTOKENS._CF_pattern)
duration._CF_pattern = facets.CF_pattern()
duration._CF_enumeration = facets.CF_enumeration(value_datatype=duration)
duration._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
duration._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
duration._CF_minInclusive = facets.CF_minInclusive(value_datatype=duration)
duration._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
duration._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=duration)
duration._InitializeFacetMap(duration._CF_pattern,
   duration._CF_enumeration,
   duration._CF_minExclusive,
   duration._CF_whiteSpace,
   duration._CF_minInclusive,
   duration._CF_maxExclusive,
   duration._CF_maxInclusive)
gMonth._CF_pattern = facets.CF_pattern()
gMonth._CF_enumeration = facets.CF_enumeration(value_datatype=gMonth)
gMonth._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
gMonth._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
gMonth._CF_minInclusive = facets.CF_minInclusive(value_datatype=gMonth)
gMonth._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
gMonth._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=gMonth)
gMonth._InitializeFacetMap(gMonth._CF_pattern,
   gMonth._CF_enumeration,
   gMonth._CF_minExclusive,
   gMonth._CF_whiteSpace,
   gMonth._CF_minInclusive,
   gMonth._CF_maxExclusive,
   gMonth._CF_maxInclusive)
hexBinary._CF_minLength = facets.CF_minLength()
hexBinary._CF_maxLength = facets.CF_maxLength()
hexBinary._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
hexBinary._CF_length = facets.CF_length()
hexBinary._CF_enumeration = facets.CF_enumeration(value_datatype=hexBinary)
hexBinary._CF_pattern = facets.CF_pattern()
hexBinary._InitializeFacetMap(hexBinary._CF_minLength,
   hexBinary._CF_maxLength,
   hexBinary._CF_whiteSpace,
   hexBinary._CF_length,
   hexBinary._CF_enumeration,
   hexBinary._CF_pattern)
double._CF_pattern = facets.CF_pattern()
double._CF_enumeration = facets.CF_enumeration(value_datatype=double)
double._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
double._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
double._CF_minInclusive = facets.CF_minInclusive(value_datatype=double)
double._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
double._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=double)
double._InitializeFacetMap(double._CF_pattern,
   double._CF_enumeration,
   double._CF_minExclusive,
   double._CF_whiteSpace,
   double._CF_minInclusive,
   double._CF_maxExclusive,
   double._CF_maxInclusive)
QName._CF_minLength = facets.CF_minLength()
QName._CF_maxLength = facets.CF_maxLength()
QName._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
QName._CF_length = facets.CF_length()
QName._CF_enumeration = facets.CF_enumeration(value_datatype=QName)
QName._CF_pattern = facets.CF_pattern()
QName._InitializeFacetMap(QName._CF_minLength,
   QName._CF_maxLength,
   QName._CF_whiteSpace,
   QName._CF_length,
   QName._CF_enumeration,
   QName._CF_pattern)
NOTATION._CF_minLength = facets.CF_minLength()
NOTATION._CF_maxLength = facets.CF_maxLength()
NOTATION._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
NOTATION._CF_length = facets.CF_length()
NOTATION._CF_enumeration = facets.CF_enumeration(value_datatype=NOTATION)
NOTATION._CF_pattern = facets.CF_pattern()
NOTATION._InitializeFacetMap(NOTATION._CF_minLength,
   NOTATION._CF_maxLength,
   NOTATION._CF_whiteSpace,
   NOTATION._CF_length,
   NOTATION._CF_enumeration,
   NOTATION._CF_pattern)
decimal._CF_fractionDigits = facets.CF_fractionDigits()
decimal._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=decimal)
decimal._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
decimal._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
decimal._CF_totalDigits = facets.CF_totalDigits()
decimal._CF_enumeration = facets.CF_enumeration(value_datatype=decimal)
decimal._CF_minInclusive = facets.CF_minInclusive(value_datatype=decimal)
decimal._CF_pattern = facets.CF_pattern()
decimal._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
decimal._InitializeFacetMap(decimal._CF_fractionDigits,
   decimal._CF_maxInclusive,
   decimal._CF_minExclusive,
   decimal._CF_whiteSpace,
   decimal._CF_totalDigits,
   decimal._CF_enumeration,
   decimal._CF_minInclusive,
   decimal._CF_pattern,
   decimal._CF_maxExclusive)
gYear._CF_pattern = facets.CF_pattern()
gYear._CF_enumeration = facets.CF_enumeration(value_datatype=gYear)
gYear._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
gYear._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
gYear._CF_minInclusive = facets.CF_minInclusive(value_datatype=gYear)
gYear._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
gYear._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=gYear)
gYear._InitializeFacetMap(gYear._CF_pattern,
   gYear._CF_enumeration,
   gYear._CF_minExclusive,
   gYear._CF_whiteSpace,
   gYear._CF_minInclusive,
   gYear._CF_maxExclusive,
   gYear._CF_maxInclusive)
boolean._CF_pattern = facets.CF_pattern()
boolean._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
boolean._InitializeFacetMap(boolean._CF_pattern,
   boolean._CF_whiteSpace)
base64Binary._CF_minLength = facets.CF_minLength()
base64Binary._CF_maxLength = facets.CF_maxLength()
base64Binary._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
base64Binary._CF_length = facets.CF_length()
base64Binary._CF_enumeration = facets.CF_enumeration(value_datatype=base64Binary)
base64Binary._CF_pattern = facets.CF_pattern()
base64Binary._InitializeFacetMap(base64Binary._CF_minLength,
   base64Binary._CF_maxLength,
   base64Binary._CF_whiteSpace,
   base64Binary._CF_length,
   base64Binary._CF_enumeration,
   base64Binary._CF_pattern)
float._CF_pattern = facets.CF_pattern()
float._CF_enumeration = facets.CF_enumeration(value_datatype=float)
float._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
float._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
float._CF_minInclusive = facets.CF_minInclusive(value_datatype=float)
float._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
float._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=float)
float._InitializeFacetMap(float._CF_pattern,
   float._CF_enumeration,
   float._CF_minExclusive,
   float._CF_whiteSpace,
   float._CF_minInclusive,
   float._CF_maxExclusive,
   float._CF_maxInclusive)
anyURI._CF_minLength = facets.CF_minLength()
anyURI._CF_maxLength = facets.CF_maxLength()
anyURI._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
anyURI._CF_length = facets.CF_length()
anyURI._CF_enumeration = facets.CF_enumeration(value_datatype=anyURI)
anyURI._CF_pattern = facets.CF_pattern()
anyURI._InitializeFacetMap(anyURI._CF_minLength,
   anyURI._CF_maxLength,
   anyURI._CF_whiteSpace,
   anyURI._CF_length,
   anyURI._CF_enumeration,
   anyURI._CF_pattern)
string._CF_minLength = facets.CF_minLength()
string._CF_maxLength = facets.CF_maxLength()
string._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.preserve)
string._CF_length = facets.CF_length()
string._CF_enumeration = facets.CF_enumeration(value_datatype=string)
string._CF_pattern = facets.CF_pattern()
string._InitializeFacetMap(string._CF_minLength,
   string._CF_maxLength,
   string._CF_whiteSpace,
   string._CF_length,
   string._CF_enumeration,
   string._CF_pattern)
dateTime._CF_pattern = facets.CF_pattern()
dateTime._CF_enumeration = facets.CF_enumeration(value_datatype=dateTime)
dateTime._CF_minExclusive = facets.CF_minExclusive(value_datatype=anySimpleType)
dateTime._CF_whiteSpace = facets.CF_whiteSpace(value=facets._WhiteSpace_enum.collapse)
dateTime._CF_minInclusive = facets.CF_minInclusive(value_datatype=dateTime)
dateTime._CF_maxExclusive = facets.CF_maxExclusive(value_datatype=anySimpleType)
dateTime._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=dateTime)
dateTime._InitializeFacetMap(dateTime._CF_pattern,
   dateTime._CF_enumeration,
   dateTime._CF_minExclusive,
   dateTime._CF_whiteSpace,
   dateTime._CF_minInclusive,
   dateTime._CF_maxExclusive,
   dateTime._CF_maxInclusive)
normalizedString._CF_whiteSpace = facets.CF_whiteSpace(super_facet=string._CF_whiteSpace, value=facets._WhiteSpace_enum.replace)
normalizedString._InitializeFacetMap(normalizedString._CF_whiteSpace)
integer._CF_fractionDigits = facets.CF_fractionDigits(value=nonNegativeInteger(0))
integer._CF_pattern = facets.CF_pattern()
integer._CF_pattern.addPattern(pattern=u'[\\-+]?[0-9]+')
integer._InitializeFacetMap(integer._CF_fractionDigits,
   integer._CF_pattern)
nonPositiveInteger._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=nonPositiveInteger, value=nonPositiveInteger(0))
nonPositiveInteger._InitializeFacetMap(nonPositiveInteger._CF_maxInclusive)
token._CF_whiteSpace = facets.CF_whiteSpace(super_facet=normalizedString._CF_whiteSpace, value=facets._WhiteSpace_enum.collapse)
token._InitializeFacetMap(token._CF_whiteSpace)
nonNegativeInteger._CF_minInclusive = facets.CF_minInclusive(value_datatype=nonNegativeInteger, value=nonNegativeInteger(0))
nonNegativeInteger._InitializeFacetMap(nonNegativeInteger._CF_minInclusive)
long._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=long, value=long(9223372036854775807))
long._CF_minInclusive = facets.CF_minInclusive(value_datatype=long, value=long(-9223372036854775808))
long._InitializeFacetMap(long._CF_maxInclusive,
   long._CF_minInclusive)
negativeInteger._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=negativeInteger, super_facet=nonPositiveInteger._CF_maxInclusive, value=negativeInteger(-1))
negativeInteger._InitializeFacetMap(negativeInteger._CF_maxInclusive)
Name._CF_pattern = facets.CF_pattern()
Name._CF_pattern.addPattern(pattern=u'\\i\\c*')
Name._InitializeFacetMap(Name._CF_pattern)
NMTOKEN._CF_pattern = facets.CF_pattern()
NMTOKEN._CF_pattern.addPattern(pattern=u'\\c+')
NMTOKEN._InitializeFacetMap(NMTOKEN._CF_pattern)
positiveInteger._CF_minInclusive = facets.CF_minInclusive(value_datatype=positiveInteger, super_facet=nonNegativeInteger._CF_minInclusive, value=positiveInteger(1))
positiveInteger._InitializeFacetMap(positiveInteger._CF_minInclusive)
language._CF_pattern = facets.CF_pattern()
language._CF_pattern.addPattern(pattern=u'[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*')
language._InitializeFacetMap(language._CF_pattern)
unsignedLong._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=unsignedLong, value=unsignedLong(18446744073709551615))
unsignedLong._InitializeFacetMap(unsignedLong._CF_maxInclusive)
int._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=int, super_facet=long._CF_maxInclusive, value=int(2147483647))
int._CF_minInclusive = facets.CF_minInclusive(value_datatype=int, super_facet=long._CF_minInclusive, value=int(-2147483648))
int._InitializeFacetMap(int._CF_maxInclusive,
   int._CF_minInclusive)
NCName._CF_pattern = facets.CF_pattern(super_facet=Name._CF_pattern)
NCName._CF_pattern.addPattern(pattern=u'[\\i-[:]][\\c-[:]]*')
NCName._InitializeFacetMap(NCName._CF_pattern)
unsignedInt._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=unsignedInt, super_facet=unsignedLong._CF_maxInclusive, value=unsignedInt(4294967295))
unsignedInt._InitializeFacetMap(unsignedInt._CF_maxInclusive)
short._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=short, super_facet=int._CF_maxInclusive, value=short(32767))
short._CF_minInclusive = facets.CF_minInclusive(value_datatype=short, super_facet=int._CF_minInclusive, value=short(-32768))
short._InitializeFacetMap(short._CF_maxInclusive,
   short._CF_minInclusive)
ENTITY._InitializeFacetMap()
IDREF._InitializeFacetMap()
ID._InitializeFacetMap()
unsignedShort._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=unsignedShort, super_facet=unsignedInt._CF_maxInclusive, value=unsignedShort(65535))
unsignedShort._InitializeFacetMap(unsignedShort._CF_maxInclusive)
byte._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=byte, super_facet=short._CF_maxInclusive, value=byte(127))
byte._CF_minInclusive = facets.CF_minInclusive(value_datatype=byte, super_facet=short._CF_minInclusive, value=byte(-128))
byte._InitializeFacetMap(byte._CF_maxInclusive,
   byte._CF_minInclusive)
unsignedByte._CF_maxInclusive = facets.CF_maxInclusive(value_datatype=unsignedByte, super_facet=unsignedShort._CF_maxInclusive, value=unsignedByte(255))
unsignedByte._InitializeFacetMap(unsignedByte._CF_maxInclusive)

