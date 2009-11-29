import pyxb
import ipo
import xml.dom.minidom
import time

xml_text = file('ipo.xml').read()

order = ipo.CreateFromDOM(xml.dom.minidom.parseString(xml_text).documentElement)

print '%s is sending %s %d thing(s):' % (order.billTo().name(), order.shipTo().name(), len(order.items().item()))
for item in order.items().item():
    print '  Quantity %d of%s at $%s' % (item.quantity(), item.productName(), item.USPrice())

# Give Mary more
try:
    item.setQuantity(100)
except pyxb.BadTypeValueError, e:
    print 'Too many: %s' % (e,)
    item.setQuantity(10)
print 'Increased quantity to %d' % (item.quantity(),)
