import GeoCoder
import time
import pyxb.utils.domutils as domutils
import sys
import pyxb
import pyxb.binding
import pyxb.standard.bindings.soapenv as soapenv

import xml.dom
from xml.dom import minidom

class geocode_ (pyxb.binding.basis.complexTypeDefinition):
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _ExpandedName = pyxb.namespace.ExpandedName(GeoCoder.Namespace, 'geocode')

    __location = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, 'location'), 'location', '__geocode_location', False)
    def location (self):
        return self.__location.value(self)
    def setLocation (self, new_value):
        return self.__location.set(self, new_value)

    _ElementMap = { __location.name() : __location }

GeoCoder.Namespace.addCategoryObject('typeBinding', u'geocode', geocode_)

geocode = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(GeoCoder.Namespace, u'geocode'), geocode_)
GeoCoder.Namespace.addCategoryObject('elementBinding', geocode.name().localName(), geocode)

geocodeResponse = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(GeoCoder.Namespace, u'geocodeResponse'), GeoCoder.ArrayOfGeocoderResult)
GeoCoder.Namespace.addCategoryObject('elementBinding', geocodeResponse.name().localName(), geocodeResponse)

geocode_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'location'), pyxb.binding.datatypes.string, scope=geocode))
geocode_._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=False, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=geocode_._UseForTag(pyxb.namespace.ExpandedName(None, u'location'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=3, is_final=True, transitions=[
    ])
})

import urllib2

pyxb.namespace.XMLSchema.validateComponentModel()

address = '111 Main St, Anytown, KS'
if 1 < len(sys.argv):
    address = sys.argv[1]

env = soapenv.Envelope()
env.setBody(geocode(address))

query_xml = env.toDOM().toxml()
uri = urllib2.Request('http://rpc.geocoder.us/service/soap/',
                      query_xml,
                      { 'SOAPAction' : "http://rpc.geocoder.us/Geo/Coder/US#geocode", 'Content-Type': 'text/xml' } )

rxml = urllib2.urlopen(uri).read()
print rxml
doc = minidom.parseString(rxml)
print doc.toprettyxml()

response = soapenv.CreateFromDOM(doc.documentElement)
gcr = response.Body().wildcardElements()[0]
items = gcr.childNodes[0].childNodes
print "\n".join([ "Element %s" % _en for _en in GeoCoder.GeocoderAddressResult._ElementMap.keys() ])

for i in items:
    r = GeoCoder.GeocoderAddressResult(_dom_node=i)
    print r

sys.exit(0)

if isinstance(gcr, xml.dom.Node):
    gcr = GeoCoder.CreateFromDOM(gcr)
print gcr.__class__
print gcr._ElementMap.keys()
for item in gcr.item():
    print item
    
