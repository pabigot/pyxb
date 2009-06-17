import GeoCoder
import time
import pyxb.utils.domutils as domutils
import sys
import pyxb
import pyxb.binding
import pyxb.standard.bindings.soapenv as soapenv

import xml.dom
from xml.dom import minidom

import urllib2

pyxb.namespace.XMLSchema.validateComponentModel()

address = '111 Main St, Anytown, KS'
if 1 < len(sys.argv):
    address = sys.argv[1]

env = soapenv.Envelope()
env.setBody(GeoCoder.geocode(address))

query_xml = env.toDOM().toxml()

print query_xml

uri = urllib2.Request('http://rpc.geocoder.us/service/soap/',
                      query_xml,
                      { 'SOAPAction' : "http://rpc.geocoder.us/Geo/Coder/US#geocode", 'Content-Type': 'text/xml' } )

rxml = urllib2.urlopen(uri).read()
doc = minidom.parseString(rxml)
print doc.toprettyxml()
response = soapenv.CreateFromDOM(doc.documentElement)

# OK, here we get into ugliness due to WSDL's concept of schema not
# being consistent with XML Schema, even though it uses the same
# namespace.  See
# http://tech.groups.yahoo.com/group/soapbuilders/message/5879.  In
# short, the WSDL spec shows an example using soapenc:Array where a
# restriction was used to set the value of the wsdl:arrayType
# attribute.  This restriction failed to duplicate the element content
# of the base type, resulting in a content type of empty in the
# restricted type.  Consequently, PyXB can't get the information out
# of the DOM node, and we have to skip over the wildcard items to find
# something we can deal with.

gcr = response.Body().wildcardElements()[0]
items = gcr.childNodes[0].childNodes

for i in items:
    item = GeoCoder.GeocoderAddressResult(_dom_node=i)
    if (item.lat() is None) or item.lat()._isNil():
        print 'Warning: Address did not resolve'
    print '''
%s %s %s %s %s
%s, %s  %s
%s %s''' % (item.number(), item.prefix(), item.street(), item.type(), item.suffix(),
            item.city(), item.state(), item.zip(),
            item.lat(), item.long())
    print item
    
