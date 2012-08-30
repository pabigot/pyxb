# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb.binding.datatypes as xsd

class Test_decimal (unittest.TestCase):
    def testRange (self):
        self.fail("Datatype decimal test not implemented")

if __name__ == '__main__':
    unittest.main()
