import po1
import pyxb.utils.domutils
xml = file('po1.xml').read()
dom = pyxb.utils.domutils.StringToDOM(xml)
order = po1.CreateFromDOM(dom.documentElement)

print '%s is sending %s %d thing(s):' % (order.billTo().name(), order.shipTo().name(), len(order.items().item()))
for item in order.items().item():
    print '  Quantity %d of %s at $%s' % (item.quantity(), item.productName(), item.USPrice())
