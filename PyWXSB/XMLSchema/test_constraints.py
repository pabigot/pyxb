from PyWXSB.exceptions_ import *
import unittest
import PyWXSB.XMLSchema.facets as facets
import PyWXSB.XMLSchema.datatypes as datatypes

# 4.3.1 length
# 4.3.2 minLength
# 4.3.3 maxLength
# NEED 4.3.4 pattern
# 4.3.5 enumeration
# NEED 4.3.6 whiteSpace
# 4.3.7 maxInclusive
# 4.3.8 maxExclusive
# 4.3.9 minExclusive
# 4.3.10 minInclusive
# 4.3.11 totalDigits
# 4.3.12 fractionDigits

class TLA (datatypes.string):
    pass
TLA._CF_length =  facets.CF_length(super_facet=datatypes.string._CF_length, value=datatypes.nonNegativeInteger(3))
TLA._InitializeFacetMap(TLA._CF_length)

class Password (datatypes.string):
    pass
Password._CF_minLength =  facets.CF_minLength(super_facet=datatypes.string._CF_minLength, value=datatypes.nonNegativeInteger(8))
Password._CF_maxLength =  facets.CF_maxLength(super_facet=datatypes.string._CF_maxLength, value=facets.CF_maxLength._ValueDatatype(15))
Password._InitializeFacetMap(Password._CF_minLength, Password._CF_maxLength)

class AFew (datatypes._PST_list):
    _ItemType = datatypes.integer
    pass
AFew._CF_minLength =  facets.CF_minLength(super_facet=datatypes.string._CF_minLength, value=datatypes.nonNegativeInteger(2))
AFew._CF_maxLength =  facets.CF_maxLength(super_facet=datatypes.string._CF_maxLength, value=facets.CF_maxLength._ValueDatatype(4))
AFew._InitializeFacetMap(AFew._CF_minLength, AFew._CF_maxLength)

class Hand (datatypes.NMTOKENS):
    pass
Hand._CF_length =  facets.CF_length(super_facet=datatypes.string._CF_length, value=datatypes.nonNegativeInteger(5))
Hand._InitializeFacetMap(Hand._CF_length)

class Cardinals (datatypes.string, facets._Enumeration_mixin):
    pass
Cardinals._CF_enumeration = facets.CF_enumeration(value_datatype=Cardinals, super_facet=datatypes.string._CF_enumeration, enum_prefix=None)
Cardinals.one = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'one')
Cardinals.two = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'two')
Cardinals.three = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'three')
Cardinals._InitializeFacetMap(Cardinals._CF_enumeration)

class ExclusiveFloat (datatypes.float):
    pass
ExclusiveFloat._CF_minExclusive =  facets.CF_minExclusive(super_facet=datatypes.float._CF_minExclusive, value_datatype=datatypes.float, value=datatypes.float(-5))
ExclusiveFloat._CF_maxExclusive =  facets.CF_maxExclusive(super_facet=datatypes.float._CF_maxExclusive, value_datatype=datatypes.float, value=datatypes.float(7))
ExclusiveFloat._InitializeFacetMap(ExclusiveFloat._CF_minExclusive, ExclusiveFloat._CF_maxExclusive)

class FixedPoint (datatypes.decimal):
    pass
FixedPoint._CF_totalDigits =  facets.CF_totalDigits(super_facet=datatypes.decimal._CF_totalDigits, value=facets.CF_totalDigits._ValueDatatype(5))
FixedPoint._CF_fractionDigits =  facets.CF_fractionDigits(super_facet=datatypes.decimal._CF_maxExclusive, value=facets.CF_fractionDigits._ValueDatatype(2))
FixedPoint._InitializeFacetMap(FixedPoint._CF_totalDigits, FixedPoint._CF_fractionDigits)

class testMaxInclusive (unittest.TestCase):
    def test (self):
        self.assertEqual(5, datatypes.byte(5))
        self.assertRaises(BadTypeValueError, datatypes.byte, 256)
        self.assertRaises(BadTypeValueError, datatypes.byte, 255)
        self.assertEquals(127, datatypes.byte(127))
        self.assertRaises(BadTypeValueError, datatypes.byte, -150)
        self.assertRaises(BadTypeValueError, datatypes.byte, -129)
        self.assertEquals(-128, datatypes.byte(-128))

class testMinMaxExclusive (unittest.TestCase):
    def test (self):
        self.assertRaises(BadTypeValueError, ExclusiveFloat, -10.0)
        self.assertRaises(BadTypeValueError, ExclusiveFloat, -5.0)
        self.assertEqual(-4.0, ExclusiveFloat(-4.0))
        self.assertEqual(0.0, ExclusiveFloat(0.0))
        self.assertEqual(6.875, ExclusiveFloat(6.875))
        self.assertRaises(BadTypeValueError, ExclusiveFloat, 7.0)

class testLength (unittest.TestCase):
    def test (self):
        self.assertEqual('one', TLA('one'))
        self.assertRaises(BadTypeValueError, TLA, 'three')
        self.assertRaises(BadTypeValueError, TLA, 'un')

    def testList (self):
        t = datatypes.NMTOKEN('card')
        self.assertRaises(BadTypeValueError, Hand, 4 * [t])
        self.assertEqual(5, len(Hand(5 * [t])))
        self.assertRaises(BadTypeValueError, Hand, 6 * [t])

class testMinMaxLength (unittest.TestCase):
    def test (self):
        self.assertRaises(BadTypeValueError, Password, 7*'x')
        self.assertEqual(8 * 'x', Password(8*'x'))
        self.assertEqual(15 * 'x', Password(15*'x'))
        self.assertRaises(BadTypeValueError, Password, 16*'x')
        
    def testList (self):
        i = datatypes.integer(2)
        self.assertRaises(BadTypeValueError, AFew, [])
        self.assertRaises(BadTypeValueError, AFew, [i])
        self.assertEqual(2, len(AFew(2 * [i])))
        self.assertEqual(3, len(AFew(3 * [i])))
        self.assertEqual(4, len(AFew(4 * [i])))
        self.assertRaises(BadTypeValueError, AFew, 5 * [i])

class testEnumeration (unittest.TestCase):
    def test (self):
        self.assertEqual(Cardinals.one, Cardinals('one'))
        self.assertEqual(Cardinals.one, Cardinals(u'one'))
        self.assertEqual(Cardinals.three, Cardinals('three'))
        self.assertEqual(Cardinals.three, Cardinals(u'three'))
        self.assertRaises(BadTypeValueError, Cardinals, 'One')
        self.assertRaises(BadTypeValueError, Cardinals, 'four')

class testDigits (unittest.TestCase):
    def testTotalDigits (self):
        self.assertEqual(1, FixedPoint(1))
        self.assertEqual(12, FixedPoint(12))
        self.assertEqual(123, FixedPoint(123))
        self.assertEqual(1234, FixedPoint(1234))
        self.assertEqual(12345, FixedPoint(12345))
        self.assertRaises(BadTypeValueError, FixedPoint, 123456)
        self.assertRaises(BadTypeValueError, FixedPoint, 1234567)
        self.assertEqual(-1, FixedPoint(-1))
        self.assertEqual(-12, FixedPoint(-12))
        self.assertEqual(-123, FixedPoint(-123))
        self.assertEqual(-1234, FixedPoint(-1234))
        self.assertEqual(-12345, FixedPoint(-12345))
        self.assertRaises(BadTypeValueError, FixedPoint, -123456)
        self.assertRaises(BadTypeValueError, FixedPoint, -1234567)

    def testFractionDigits (self):
        self.assertEqual(1, FixedPoint(1))
        self.assertEqual(1.2, FixedPoint(1.2))
        self.assertEqual(1.23, FixedPoint(1.23))
        self.assertRaises(BadTypeValueError, FixedPoint, 1.234)
        self.assertEqual(12, FixedPoint(12))
        self.assertEqual(12.3, FixedPoint(12.3))
        self.assertEqual(12.34, FixedPoint(12.34))
        self.assertRaises(BadTypeValueError, FixedPoint, 12.345)
        self.assertEqual(-1, FixedPoint(-1))
        self.assertEqual(-1.2, FixedPoint(-1.2))
        self.assertEqual(-1.23, FixedPoint(-1.23))
        self.assertRaises(BadTypeValueError, FixedPoint, -1.234)
        self.assertEqual(-12, FixedPoint(-12))
        self.assertEqual(-12.3, FixedPoint(-12.3))
        self.assertEqual(-12.34, FixedPoint(-12.34))
        self.assertRaises(BadTypeValueError, FixedPoint, -12.345)

if __name__ == '__main__':
    unittest.main()
