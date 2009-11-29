import pyxb.bundles.opengis.gml as gml
dv = gml.DegreesType(32, direction='N')
print dv.toxml()
