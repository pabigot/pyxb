import pyxb.bundles.opengis.gml as gml
dv = gml.DegreesType(32, direction='N')
print dv.toDOM(element_name='degrees').toxml("utf-8")
