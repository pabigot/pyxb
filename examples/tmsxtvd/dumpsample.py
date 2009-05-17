import tmstvd
import pyxb.utils.domutils
import xml.dom
import xml.dom.minidom
import pyxb.Namespace
import time

t1 = time.time()
xmls = open('tmsdatadirect_sample.xml').read()
t2 = time.time()
dom = xml.dom.minidom.parseString(xmls)
t3 = time.time()
instance = tmstvd.CreateFromDOM(dom.documentElement)
t4 = time.time()
print 'Ready to go'
for s in instance.stations().station():
    print 'Station %s is %s, id %d' % (s.callSign(), s.name(), s.id())
    
for p in instance.programs().program():
    print '%s "%s" episode %s: %s' % (p.showType(), p.title(),  p.syndicatedEpisodeNumber(), p.subtitle())

print 'Read %f, parse %f, bind %f' % (t2-t1, t3-t2, t4-t3)
