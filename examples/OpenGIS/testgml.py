#  PYTHONPATH=../..:. PYXB_ARCHIVE_PATH=opengis/iso19139:+ ../../scripts/pyxbgen -u gmlapp.xsd -m gmlapp

import opengis.gml_3_2 as gml
import gmlapp

env = gml.GridEnvelopeType([0, 0], [4, 4])
#print env.toxml()
limits = gml.GridLimitsType(env)
point = gml.pos([-93.25, 43.5])
origin = gml.PointPropertyType(gml.Point(gml.pos([-93.25, 43.5]), id='_origin'))
offset_vector = gml.VectorType([0, 0])

grid = gml.RectifiedGrid(limits, 'latitude longitude', origin, offset_vector, dimension=2)
grid.setId('_%x' % id(grid))
domain = gml.domainSet(grid)
#print domain.toxml()

val_template = gmlapp.Temperature(nilReason='template', _nil=True, uom='urn:x-si:v1999:uom:degreesC')
val_instance = gmlapp.Temperature(34.2, uom='urn:x-si:v1999:uom:degreesC')
#instance = gml.valueComponent()
#instance.setAbstractValue(val_instance)
instance = gml.valueComponent(AbstractValue=val_instance)
#print instance.toxml()

xml = '''<?xml version="1.0" ?>
<gml:valueComponent xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:app="URN:gmlapp"><app:Temperature uom="urn:x-si:v1999:uom:degreesC">34.2</app:Temperature></gml:valueComponent>
'''
instance = gml.CreateFromDocument(xml)

instance = gml.valueComponents(AbstractValue=[val_instance])
#print instance.toxml()

xml = '''<?xml version="1.0" ?>
<gml:valueComponents xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:app="URN:gmlapp"><app:Temperature uom="urn:x-si:v1999:uom:degreesC">34.2</app:Temperature></gml:valueComponents>
'''
instance = gml.CreateFromDocument(xml)

vc = gml.valueComponents(AbstractValue=val_template)
rp = gml.rangeParameters(gml.CompositeValue(vc, id='_vc'))
data = gml.tupleList('34.2 35.4')
range = gml.rangeSet(DataBlock=gml.DataBlockType(rp, data))

gc = gml.RectifiedGridCoverage(domain, range)
gc.setId('_%x' % (id(gc),))

xml = gc.toxml()
print xml
instance = gml.CreateFromDocument(xml)
xml2 = instance.toxml()

assert xml == xml2

print xml2


