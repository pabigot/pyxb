import pyxb
import po3
import address

az = address.USState('AZ')
addr = address.USAddress()
addr.name = 'Robert Smith'
addr.street = '8 Oak Avenue'
addr.city = 'Anytown'
addr.state = 'AK'
addr.zip = 12341

print addr.toxml()

try:
    ny = address.USState('NY')
    assert False
except pyxb.BadTypeValueError, e:
    print e



#print '%s is sending %s %d thing(s):' % (order.billTo.name, order.shipTo.name, len(order.items.item))
#for item in order.items.item:
#    print '  Quantity %d of %s at $%s' % (item.quantity.content, item.productName, item.USPrice)
