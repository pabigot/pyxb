# See http://www.weather.gov/forecasts/xml/OGC_services/

import time
import urllib2
import ndfd.dwGML
import pyxb.bundles.opengis.gml
import pyxb.bundles.opengis.ows
import pyxb.binding.datatypes as xsd
import sys

# Coordinates for which weather is requested.  See examples/geocoder
# for a utility that obtains the lat/lon for a US street address.
lat_lon = [ '38.898748',  '-77.037684' ]
if 3 <= len(sys.argv):
    lat_lon = sys.argv[1:3]

parameters = [ 'mint', 'maxt', 'temp', 'pop12', 'wspd', 'wdir' ]
url_base = 'http://www.weather.gov/forecasts/xml/OGC_services/ndfdOWSserver.php'
kw = {
    'service' : 'WFS',
    'version' : '1.1.0',
    'typename' : 'Forecast_GmlObs',
    'Request' : 'GetFeature',
    'latLonList' : ','.join(lat_lon),
    'time' : xsd.dateTime(xsd.dateTime.today() + xsd.duration('PT12H')).xsdLiteral(),
    'params' : ','.join(parameters)
    }

url = url_base + '?' + '&'.join('%s=%s' % _v for _v in kw.items())

print '# Retrieving %s' % (url,)
xmls = urllib2.urlopen(url).read()
file('forecast.xml', 'w').write(xmls)
#xmls = file('forecast.xml').read()

print '# Parsing response'
res = ndfd.dwGML.CreateFromDocument(xmls)

if res._element() == pyxb.bundles.opengis.ows.ExceptionReport:
    for ex in res.Exception:
        print '%s (%s): %s' % (ex.exceptionCode, ex.locator, ''.join([_txt for _txt in ex.ExceptionText]))
    sys.exit(1)

for fm in res.featureMember:
    obs = fm.Feature
    when = obs.validTime.TimePrimitive.timePosition.value()
    tgt = obs.target
    # Customize gml:TargetPropertyType for this
    where = tgt.Feature or tgt.Geometry
    # Customize gml:PointType: convert coordinates and coord into pos
    print 'For %s at %s:' % ('%f %f' % tuple(where.pos.value()), when)
    fc = obs.resultOf.Object
    for fcv in fc.content():
        ln = fcv._element().name().localName()
        if isinstance(fcv, pyxb.bundles.opengis.gml.MeasureType):
            print ' %s: %s %s' % (ln, fcv.value(), fcv.uom)
        elif isinstance(fcv, pyxb.bundles.opengis.gml.CodeOrNullListType):
            for v in fcv.value():
                print ' %s: %s' % (ln, v)
        elif isinstance(fcv, pyxb.binding.datatypes.anyURI):
            print ' %s: %s' % (ln, fcv)
        else:
            print ' %s type %s' % (fcv._element().name(), type(fcv))
        
