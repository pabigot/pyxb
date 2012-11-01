import pyxb
import poc

xml = file('poc.xml').read()
try:
    pobObject = poc.CreateFromDocument(xml, location_base='poc.xml')
    print pobObject.toxml()
except pyxb.UnrecognizedContentError, e:
    print 'Unrecognized element "%s" at %s' % (e.content.expanded_name, e.content.location)
