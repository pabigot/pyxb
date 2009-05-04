import weather

from xml.dom import minidom

doc = minidom.parse('85711.xml')

fc_return = weather.ForecastReturn.CreateFromDOM(doc.documentElement)
if fc_return.Success():
    print 'Got response for %s, %s:' % (fc_return.City(), fc_return.State())
    for fc in fc_return.ForecastResult().Forecast():
        print '%s: %s, from %s to %s' % (fc.Date(), fc.Desciption(), fc.Temperatures().MorningLow(), fc.Temperatures().DaytimeHigh())
        
    
