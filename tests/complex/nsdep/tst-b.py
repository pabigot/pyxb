from pyxb.utils.domutils import BindingDOMSupport
import unittest

import bindings._A as A
import bindings._B as B

class Test (unittest.TestCase):
    def setUp (self):
        BindingDOMSupport.DeclareNamespace(A.Namespace, 'a')
        BindingDOMSupport.DeclareNamespace(B.Namespace, 'b')
        
    def tearDown (self):
        BindingDOMSupport.Reset(prefix_map=True)
        
    def tests (self):
        # Element {URN:nsdep:A}e1 uses Python identifier e1
        # Element {URN:nsdep:A}A_b_e1 uses Python identifier A_b_e1
        x = A.A_c_e1("A.b.e1", "e1")
        self.assertEqual('<a:A_c_e1 xmlns:a="URN:nsdep:A"><a:A_b_e1>A.b.e1</a:A_b_e1><a:e1>e1</a:e1></a:A_c_e1>', x.toxml(root_only=True))
        self.assertEqual(A.tA_c, type(x))

        # Element {URN:nsdep:A}e1 uses Python identifier e1
        # Element {URN:nsdep:B}B_b_e1 uses Python identifier B_b_e1
        # Element {URN:nsdep:A}A_b_e1 uses Python identifier A_b_e1
        # Element {URN:nsdep:B}e1 uses Python identifier e1_
        y = B.B_c_e1("B.e1", "A.e1", "B.b.e1", x.A_b_e1)
        self.assertEqual('A.e1', y.e1)
        self.assertEqual('B.b.e1', y.B_b_e1)
        self.assertEqual('A.b.e1', y.A_b_e1)
        self.assertEqual(A.strA, type(y.A_b_e1))
        self.assertEqual('B.e1', y.e1_)

if '__main__' == __name__:
    unittest.main()
