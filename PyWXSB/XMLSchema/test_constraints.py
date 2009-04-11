from PyWXSB.exceptions_ import *
import unittest
import facets
import datatypes

# 4.3.1 length
# 4.3.2 minLength
# 4.3.3 maxLength
# NEED 4.3.4 pattern
# 4.3.5 enumeration
# NEED 4.3.6 whiteSpace
# 4.3.7 maxInclusive
# NEED 4.3.8 maxExclusive
# NEED 4.3.9 minExclusive
# 4.3.10 minInclusive
# NEED 4.3.11 totalDigits
# NEED 4.3.12 fractionDigits

class TLA (datatypes.string):

    pass
TLA._CF_length =  facets.CF_length(super_facet=datatypes.string._CF_length, value=datatypes.nonNegativeInteger(3))
TLA._InitializeFacetMap(TLA._CF_length)

class Password (datatypes.string):
    pass
Password._CF_minLength =  facets.CF_minLength(super_facet=datatypes.string._CF_minLength, value=datatypes.nonNegativeInteger(8))
Password._CF_maxLength =  facets.CF_maxLength(super_facet=datatypes.string._CF_maxLength, value=facets.CF_maxLength._ValueDatatype(15))
Password._InitializeFacetMap(Password._CF_minLength, Password._CF_maxLength)

class Cardinals (datatypes.string, facets._Enumeration_mixin):
    pass
Cardinals._CF_enumeration = facets.CF_enumeration(value_datatype=Cardinals, super_facet=datatypes.string._CF_enumeration, enum_prefix=None)
Cardinals.one = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'one')
Cardinals.two = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'two')
Cardinals.three = Cardinals._CF_enumeration.addEnumeration(unicode_value=u'three')
Cardinals._InitializeFacetMap(Cardinals._CF_enumeration)

class testMaxInclusive (unittest.TestCase):
    def test (self):
        self.assertEqual(5, datatypes.byte(5))
        self.assertRaises(BadTypeValueError, datatypes.byte, 256)
        self.assertRaises(BadTypeValueError, datatypes.byte, 255)
        self.assertEquals(127, datatypes.byte(127))

class testMinInclusive (unittest.TestCase):
    def test (self):
        self.assertEqual(5, datatypes.byte(5))
        self.assertRaises(BadTypeValueError, datatypes.byte, -150)
        self.assertRaises(BadTypeValueError, datatypes.byte, -129)
        self.assertEquals(-128, datatypes.byte(-128))

class testLength (unittest.TestCase):
    def test (self):
        self.assertEqual('one', TLA('one'))
        self.assertRaises(BadTypeValueError, TLA, 'three')
        self.assertRaises(BadTypeValueError, TLA, 'un')

class testMinMaxLength (unittest.TestCase):
    def test (self):
        self.assertRaises(BadTypeValueError, Password, 7*'x')
        self.assertEqual(8 * 'x', Password(8*'x'))
        self.assertEqual(15 * 'x', Password(15*'x'))
        self.assertRaises(BadTypeValueError, Password, 16*'x')
        
class testEnumeration (unittest.TestCase):
    def test (self):
        self.assertEqual(Cardinals.one, Cardinals('one'))
        self.assertEqual(Cardinals.one, Cardinals(u'one'))
        self.assertEqual(Cardinals.three, Cardinals('three'))
        self.assertEqual(Cardinals.three, Cardinals(u'three'))
        self.assertRaises(BadTypeValueError, Cardinals, 'One')
        self.assertRaises(BadTypeValueError, Cardinals, 'four')
