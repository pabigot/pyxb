import weather
import time
import pyxb.utils.domutils as domutils
import sys

from xml.dom import minidom

import urllib2

#uri = 'http://ws.cdyne.com/WeatherWS/Weather.asmx/GetCityForecastByZIP?ZIP=55108'

query = weather.GetCityForecastByZIP(ZIP=55108)

bds = domutils.BindingDOMSupport()
doc = query.toDOM(bds).finalize()
query_xml = doc.documentElement.toxml()

query_xml = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>%s
  </soap:Body>
</soap:Envelope>
''' % (query_xml,)

host = 'http://ws.cdyne.com'
uri = urllib2.Request(host + '/WeatherWS/Weather.asmx', query_xml, { 'SOAPAction' : "http://ws.cdyne.com/WeatherWS/GetCityForecastByZIP", 'Content-Type': 'text/xml' } )

xml = urllib2.urlopen(uri).read()
#print xml
doc = minidom.parseString(xml)

body = doc.documentElement.firstChild
body = weather.CreateFromDOM(body.firstChild)
fc_return = body.GetCityForecastByZIPResult()
if fc_return.Success():
    print 'Got response for %s, %s:' % (fc_return.City(), fc_return.State())
    for fc in fc_return.ForecastResult().Forecast():
        print '%s: %s, from %s to %s' % (time.strftime('%A, %B %d %Y', fc.Date().timetuple()), fc.Desciption(), fc.Temperatures().MorningLow(), fc.Temperatures().DaytimeHigh())
        
    
