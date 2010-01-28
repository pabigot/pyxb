import pyxb
import po1

xml = file('badcontent.xml').read()
try:
    order = po1.CreateFromDocument(xml, location_base='badcontent.xml')
except pyxb.UnrecognizedContentError, e:
    print 'Unrecognized element "%s" at %s' % (e.content.expanded_name, e.content.location)

