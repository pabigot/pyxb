import PyWXSB.generate

code = PyWXSB.generate.GeneratePython('schemas/test-union.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestUnion (unittest.TestCase):
    def test (self):
        self.assertRaises(LogicError, myUnion, 5)
        self.assertEqual(5, myUnion.Factory(5))
        self.assertEqual(5, myUnion.Factory('5'))
        self.assertRaises(BadTypeValueError, myUnion.Factory, 10)
        self.assert_(isinstance(myUnion.Factory('5'), singleDigit))
        self.assert_(isinstance(myUnion.Factory('one'), english))
        self.assertEqual(welsh.un, myUnion.Factory('un'))
        self.assert_(isinstance(myUnion.Factory('un'), welsh))
        self.assertEqual(english.one, myUnion.Factory('one'))
        self.assertRaises(LogicError, myUnion, 'five')

    def testList (self):
        my_list = unionList([ myUnion.Factory(4), myUnion.Factory('one')])
        self.assertEqual(2, len(my_list))

    def testRestrictedUnion (self):
        self.assertEqual(ones.one, ones.Factory('one'))
        self.assertRaises(BadTypeValueError, ones.Factory, 'two')
        self.assertEqual(ones.un, ones.Factory('un'))

if __name__ == '__main__':
    unittest.main()
    
