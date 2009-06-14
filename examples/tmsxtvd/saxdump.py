xml_file = 'tmsdatadirect_sample.xml'

import pyxb.binding.saxer
import tmstvd

import time

t1 = time.time()
saxer = pyxb.binding.saxer.make_parser()
handler = saxer.getContentHandler()
t2 = time.time()
saxer.parse(open(xml_file))
t3 = time.time()
instance = handler.rootObject()

print 'Ready to go'
for s in instance.stations().station():
    print 'Station %s is %s, id %d' % (s.callSign(), s.name(), s.id())
    
for p in instance.programs().program():
    print '%s "%s" episode %s: %s' % (p.showType(), p.title(),  p.syndicatedEpisodeNumber(), p.subtitle())

print 'Read %f, parse and bind %f' % (t2-t1, t3-t2)
