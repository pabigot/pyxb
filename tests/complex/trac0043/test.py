import A
x = A.a2('a2m-value', 'legal')
print x.toxml()

import B
myobj = B.b1(x, 'legal')
print myobj.a2elt.a2member
print myobj.a2elt.a2b
print myobj.ba
print myobj.toxml()


