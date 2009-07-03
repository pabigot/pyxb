import bindings.A as A
import bindings.B as B

# Element {URN:nsdep:A}e1 uses Python identifier e1
# Element {URN:nsdep:A}A_b_e1 uses Python identifier A_b_e1
x = A.A_c_e1("A.b.e1", "e1")
print x.toxml()
print type(x)

# Element {URN:nsdep:A}e1 uses Python identifier e1
# Element {URN:nsdep:B}B_b_e1 uses Python identifier B_b_e1
# Element {URN:nsdep:A}A_b_e1 uses Python identifier A_b_e1
# Element {URN:nsdep:B}e1 uses Python identifier e1_
y = B.B_c_e1("B.e1", "A.e1", "B.b.e1", x.A_b_e1())
print y.e1()
print y.B_b_e1()
print '%s (%s)' % (y.A_b_e1(), type(y.A_b_e1()))
print y.e1_()
