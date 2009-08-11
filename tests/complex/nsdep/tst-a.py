from pyxb.utils.domutils import BindingDOMSupport
import unittest

import bindings._A as A

class Test (unittest.TestCase):
    def setUp (self):
        BindingDOMSupport.DeclareNamespace(A.Namespace, 'a')
        
    def tearDown (self):
        BindingDOMSupport.Reset(prefix_map=True)
        
    def tests (self):
        x = A.A_c_e1("A_b_e1", "e1")
        self.assertEqual('<a:A_c_e1 xmlns:a="URN:nsdep:A"><a:A_b_e1>A_b_e1</a:A_b_e1><a:e1>e1</a:e1></a:A_c_e1>', x.toxml(root_only=True))

if '__main__' == __name__:
    unittest.main()
