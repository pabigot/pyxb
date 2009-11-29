import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import pyxb.binding.basis
import os.path
schema_path = '%s/../schemas/test-collision.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path, binding_style=pyxb.binding.basis.BINDING_STYLE_PROPERTY)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.utils import domutils

import unittest

class TestCollision (unittest.TestCase):

    def setUp (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.BINDING_STYLE_PROPERTY)

    def tearDown (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.DEFAULT_BINDING_STYLE)

    def testBasic (self):
        self.assertEqual(pyxb.binding.basis.CURRENT_BINDING_STYLE, pyxb.binding.basis.BINDING_STYLE_PROPERTY)
        instance = color(color_.red, color_=color_.green)
        self.assertEqual('<color color="green"><color>red</color></color>', instance.toxml(root_only=True))
        instance.color = color_.blue
        self.assertEqual('<color color="green"><color>blue</color></color>', instance.toxml(root_only=True))
        instance.color_ = color_.red
        self.assertEqual('<color color="red"><color>blue</color></color>', instance.toxml(root_only=True))

if __name__ == '__main__':
    unittest.main()
