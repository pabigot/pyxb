# See http://www.weather.gov/forecasts/xml/OGC_services/

import time
import urllib2
import ndfd.dwGML
import opengis.gml
import opengis.ows
import pyxb.binding.datatypes as xsd
import sys

parameters = [ 'mint', 'maxt', 'temp', 'pop12', 'wspd', 'wdir' ]
url_base = 'http://www.weather.gov/forecasts/xml/OGC_services/ndfdOWSserver.php'
kw = {
    'service' : 'WFS',
    'version' : '1.1.0',
    'typename' : 'Forecast_GmlObs',
    'Request' : 'GetFeature',
    #'latLonList' : '44.9893,-93.1515',
    'latLonList' : '32.2281,-110.899',
    'time' : xsd.dateTime(xsd.dateTime.today() + xsd.duration('PT12H')).xsdLiteral(),
    'params' : ','.join(parameters)
    }

url = url_base + '?' + '&'.join('%s=%s' % _v for _v in kw.items())

xmls = urllib2.urlopen(url).read()
file('xforecast.xml', 'w').write(xmls)
#xmls = file('xforecast.xml').read()

res = ndfd.dwGML.CreateFromDocument(xmls)

if res._element() == opengis.ows.ExceptionReport:
    for ex in res.Exception():
        print '%s (%s): %s' % (ex.exceptionCode(), ex.locator(), ''.join([_txt for _txt in ex.ExceptionText()]))
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
        if isinstance(fcv, opengis.gml.MeasureType):
            print ' %s: %s %s' % (fcv._element().name().localName(), fcv.value(), fcv.uom)
        else:
            print fcv._element().name()
