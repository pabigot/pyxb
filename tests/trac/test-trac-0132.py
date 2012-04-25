# -*- coding: utf-8 -*-

import pyxb
import unittest

class TestTrac0132 (unittest.TestCase):
    message = u'bad character \u2620'
    def testDecode (self):
        e = pyxb.PyXBException(self.message)
        self.assertEqual(self.message, e.message)

if __name__ == '__main__':
    unittest.main()
