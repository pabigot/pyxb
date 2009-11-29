import po1

xml = file('po1.xml').read()
order = po1.CreateFromDocument(xml)

print '%s is sending %s %d thing(s):' % (order.billTo.name, order.shipTo.name, len(order.items.item))
for item in order.items.item:
    print '  Quantity %d of %s at $%s' % (item.quantity, item.productName, item.USPrice)
