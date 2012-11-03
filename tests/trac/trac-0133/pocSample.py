import pyxb
import poc

xml = file('poc.xml').read()
pobObject = poc.CreateFromDocument(xml, location_base='poc.xml')
print pobObject.toxml()
