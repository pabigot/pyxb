import B
from pyxb import BIND

myobj = B.b1(BIND('a2m-value', 'legal'), 'legal')
print myobj.a2elt.a2member
print myobj.a2elt.a2b
print myobj.ba
print myobj.toxml()

myobj.a2elt = BIND('anotherValue', 'legal')
print myobj.toxml()
