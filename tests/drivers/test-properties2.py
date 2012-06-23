# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import pyxb.binding.basis
import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-collision.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.utils import domutils

import unittest

class TestCollision (unittest.TestCase):

    def testBasic (self):
        instance = color(color_.red, color_=color_.green)
        self.assertEqual('<color color="green"><color>red</color></color>', instance.toxml("utf-8", root_only=True))
        instance.color = color_.blue
        self.assertEqual('<color color="green"><color>blue</color></color>', instance.toxml("utf-8", root_only=True))
        instance.color_ = color_.red
        self.assertEqual('<color color="red"><color>blue</color></color>', instance.toxml("utf-8", root_only=True))

if __name__ == '__main__':
    unittest.main()
