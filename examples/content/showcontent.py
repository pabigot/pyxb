import content

v = content.numbers(1, 2, attribute=3)
v.complex().setStyle("decimal")
print v.toxml()
print 3 * v.simple()
print 4 * v.complex().content()
print 5 * v.attribute()

