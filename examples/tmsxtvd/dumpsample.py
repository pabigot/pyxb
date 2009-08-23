import tmstvd
import pyxb.utils.domutils as domutils
import xml.dom.minidom
import pyxb.utils.saxdom
import pyxb.binding.saxer
import time
#import cProfile

# Extend the anonymous class used by the xtvd element to add a method
# we can use to test equality of two instances.  Normally, you'd just
# refer to the complex type binding class itself, but we don't know
# what PyXB named it.
class my_xtvd (tmstvd.xtvd.typeDefinition()):
    def equal (self, other, verbose=False):
        if len(self.stations.station) != len(other.stations.station):
            return False
        for i in range(len(self.stations.station)):
            s = self.stations.station[i]
            o = other.stations.station[i]
            if (s.callSign != o.callSign) or (s.name != o.name) or (s.id != o.id):
                return False
            if verbose:
                print 'Match station %s is %s, id %d' % (s.callSign, s.name, s.id)
        return True
tmstvd.xtvd.typeDefinition()._SetSupersedingClass(my_xtvd)

# The sample document.
xml_file = 'tmsdatadirect_sample.xml'

print 'Generating binding from %s with minidom' % (xml_file,)
mt1 = time.time()
xmls = open(xml_file).read()
mt2 = time.time()
dom = xml.dom.minidom.parseString(xmls)
mt3 = time.time()
#cProfile.run('tmstvd.CreateFromDOM(dom.documentElement)', 'dom.prf')
dom_instance = tmstvd.CreateFromDOM(dom.documentElement)
print 'minidom first callSign at %s' %(dom_instance.stations.station[0].callSign._location(),)
mt4 = time.time()

print 'Generating binding from %s with SAXDOM' % (xml_file,)
dt1 = time.time()
dom = pyxb.utils.saxdom.parseString(xmls, location_base=xml_file)
dt2 = time.time()
#cProfile.run('tmstvd.CreateFromDOM(dom.documentElement)', 'saxdom.prf')
saxdom_instance = tmstvd.CreateFromDOM(dom.documentElement)
print 'SAXDOM first callSign at %s' % (saxdom_instance.stations.station[0].callSign._location(),)
dt3 = time.time()

print 'Generating binding from %s with SAX' % (xml_file,)
st1 = time.time()
saxer = pyxb.binding.saxer.make_parser(location_base=xml_file)
handler = saxer.getContentHandler()
st2 = time.time()
saxer.parse(open(xml_file))
#cProfile.run('saxer.parse(open(xml_file))', 'sax.prf')
st3 = time.time()
sax_instance = handler.rootObject()
print 'SAXER first callSign at %s' % (sax_instance.stations.station[0].callSign._location(),)

print 'DOM-based read %f, parse %f, bind %f, total %f' % (mt2-mt1, mt3-mt2, mt4-mt3, mt4-mt2)
print 'SAXDOM-based parse %f, bind %f, total %f' % (dt2-dt1, dt3-dt2, dt3-dt1)
print 'SAX-based read %f, parse and bind %f, total %f' % (st2-st1, st3-st2, st3-st1)
print "Equality test on DOM vs SAX: %s" % (dom_instance.equal(sax_instance),)
print "Equality test on SAXDOM vs SAX: %s" % (saxdom_instance.equal(sax_instance, verbose=True),)

