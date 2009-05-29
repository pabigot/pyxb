import po3
import pyxb.utils.domutils
xml = file('po3.xml').read()
dom = pyxb.utils.domutils.StringToDOM(xml)
order = po3.CreateFromDOM(dom.documentElement)

print '%s is sending %s %d thing(s):' % (order.billTo().name(), order.shipTo().name(), len(order.items().item()))
for item in order.items().item():
    print '  Quantity %d of %s at $%s' % (item.quantity().content(), item.productName(), item.USPrice())
