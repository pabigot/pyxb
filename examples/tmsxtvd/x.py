import tms
import pyxb.utils.domutils
import xml.dom
import xml.dom.minidom
import pyxb.Namespace

print 'Reading'
xmls = open('tmsdatadirect_sample.xml').read()
print 'Parsing'
dom = xml.dom.minidom.parseString(xmls)
print 'Generating binding'
instance = tms.CreateFromDOM(dom.documentElement)
print 'Ready to go'
for s in instance.stations().station():
    print 'Station %s is %s, id %d' % (s.callSign(), s.name(), s.id())
    
for p in instance.programs().program():
    print '%s "%s" episode %s: %s' % (p.showType(), p.title(),  p.syndicatedEpisodeNumber(), p.subtitle())
