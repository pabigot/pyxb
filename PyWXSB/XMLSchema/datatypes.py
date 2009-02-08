"""Classes supporting XMLSchema Part 2: Datatypes"""

import structures as xsc
import types

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

class anySimpleType (xsc.PythonSimpleTypeSupport):
    @classmethod
    def StringToPython (cls, value):
        return value

    @classmethod
    def PythonToString (cls, value):
        return value
# anySimpleType is not treated as a primitive, because its variety must be absent (not atomic).
    
class string (anySimpleType):
    # NOTE: The PythonType for this is *NOT* types.StringType, since
    # the value may be a unicode string.

    @classmethod
    def StringToPython (cls, value):
        return value

    @classmethod
    def PythonToString (cls, value):
        return value
_PrimitiveDatatypes.append(string)

class boolean (anySimpleType):
    PythonType = types.BooleanType

    @classmethod
    def StringToPython (cls, value):
        if 'true' == value:
            return True
        if 'false' == value:
            return False
        raise ValueError('boolean: Invalid value "%s"' % (value,))

    @classmethod
    def PythonToString (cls, value):
        if value:
            return 'true'
        return 'false'
_PrimitiveDatatypes.append(boolean)

class decimal (anySimpleType):
    pass
_PrimitiveDatatypes.append(decimal)

class float (anySimpleType):
    pass
_PrimitiveDatatypes.append(float)

class double (anySimpleType):
    pass
_PrimitiveDatatypes.append(double)

class duration (anySimpleType):
    pass
_PrimitiveDatatypes.append(duration)

class dateTime (anySimpleType):
    pass
_PrimitiveDatatypes.append(dateTime)

class time (anySimpleType):
    pass
_PrimitiveDatatypes.append(time)

class date (anySimpleType):
    pass
_PrimitiveDatatypes.append(date)

class gYearMonth (anySimpleType):
    pass
_PrimitiveDatatypes.append(gYearMonth)

class gYear (anySimpleType):
    pass
_PrimitiveDatatypes.append(gYear)

class gMonthDay (anySimpleType):
    pass
_PrimitiveDatatypes.append(gMonthDay)

class gDay (anySimpleType):
    pass
_PrimitiveDatatypes.append(gDay)

class gMonth (anySimpleType):
    pass
_PrimitiveDatatypes.append(gMonth)

class hexBinary (anySimpleType):
    pass
_PrimitiveDatatypes.append(hexBinary)

class base64Binary (anySimpleType):
    pass
_PrimitiveDatatypes.append(base64Binary)

class anyURI (anySimpleType):
    pass
_PrimitiveDatatypes.append(anyURI)

class QName (anySimpleType):
    pass
_PrimitiveDatatypes.append(QName)

class NOTATION (anySimpleType):
    pass
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

class integer (decimal):
    PythonType = types.LongType

    @classmethod
    def StringToPython (cls, value):
        try:
            return cls.PythonType(value)
        except ValueError, e:
            raise ValueError('%s: Invalid value "%s"' % (cls.__class__.__name__, value))

    @classmethod
    def PythonToString (cls, value):
        return str(value)
_DerivedDatatypes.append(integer)

class nonPositiveInteger (integer):
    @classmethod
    def StringToPython (cls, value):
        rv = integer.StringToPython(value)
        if 0 < rv:
            raise ValueError('nonPositiveInteger: Invalid value "%s"' % (value,))
        return rv
_DerivedDatatypes.append(nonPositiveInteger)

class negativeInteger (nonPositiveInteger):
    @classmethod
    def StringToPython (cls, value):
        rv = nonPositiveInteger.StringToPython(value)
        if 0 <= rv:
            raise ValueError('negativeInteger: Invalid value "%s"' % (value,))
        return rv
_DerivedDatatypes.append(negativeInteger)

class long (integer):
    pass
_DerivedDatatypes.append(long)

class int (long):
    pass
_DerivedDatatypes.append(int)

class short (int):
    pass
_DerivedDatatypes.append(short)

class byte (short):
    pass
_DerivedDatatypes.append(byte)

class nonNegativeInteger (integer):
    @classmethod
    def StringToPython (cls, value):
        rv = integer.StringToPython(value)
        if 0 > rv:
            raise ValueError('nonNegativeInteger: Invalid value "%s" produced %d' % (value, rv))
        return rv
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
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreatePrimitiveInstance(name, schema.getTargetNamespace(), dtc()))
        assert td.isResolved()
        pts_std_map.setdefault(dtc, td)
    for dtc in _DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.SuperType()]
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateDerivedInstance(name, schema.getTargetNamespace(), parent_std, dtc()))
        assert td.isResolved()
        pts_std_map.setdefault(dtc, td)
    for (list_name, element_name) in _ListDatatypes:
        element_std = schema._lookupTypeDefinition(element_name)
        td = schema._addNamedComponent(xsc.SimpleTypeDefinition.CreateListInstance(list_name, schema.getTargetNamespace(), element_std))
        assert td.isResolved()
    return schema
