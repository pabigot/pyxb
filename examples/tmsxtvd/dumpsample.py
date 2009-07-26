import tmstvd
import pyxb.utils.domutils as domutils
import pyxb.binding.saxer
import time

# Extend the anonymous class used by the xtvd element to add a method
# we can use to test equality of two instances.  Normally, you'd just
# refer to the complex type binding class itself, but we don't know
# what PyXB named it.
class my_xtvd (tmstvd.xtvd.typeDefinition()):
    def equal (self, other):
        if len(self.stations.station) != len(other.stations.station):
            return False
        for i in range(len(self.stations.station)):
            s = self.stations.station[i]
            o = other.stations.station[i]
            if (s.callSign != o.callSign) or (s.name != o.name) or (s.id != o.id):
                return False
            print 'Match station %s is %s, id %d' % (s.callSign, s.name, s.id)
        return True
tmstvd.xtvd.typeDefinition()._SetSupersedingClass(my_xtvd)

# The sample document.
xml_file = 'tmsdatadirect_sample.xml'

print 'Generating binding from %s with DOM' % (xml_file,)
dt1 = time.time()
xmls = open(xml_file).read()
dt2 = time.time()
dom = domutils.StringToDOM(xmls)
dt3 = time.time()
dom_instance = tmstvd.CreateFromDOM(dom.documentElement)
dt4 = time.time()

print 'Generating binding from %s with SAX' % (xml_file,)
st1 = time.time()
saxer = pyxb.binding.saxer.make_parser()
handler = saxer.getContentHandler()
st2 = time.time()
saxer.parse(open(xml_file))
st3 = time.time()
sax_instance = handler.rootObject()

print 'DOM-based read %f, parse %f, bind %f' % (dt2-dt1, dt3-dt2, dt4-dt3)
print 'SAX-based read %f, parse and bind %f' % (st2-st1, st3-st2)
print "Equality test on DOM vs SAX: %s" % (dom_instance.equal(sax_instance),)

