import xml.dom.minidom
import DWML
import datetime
import pyxb.binding.datatypes as xsd
import urllib2
import time

# Get the next seven days forecast for two locations
zip = [ 85711, 55108 ]
begin = xsd.dateTime()
end = xsd.dateTime(begin + datetime.timedelta(7))

# Create the REST URI for this query
uri = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?zipCodeList=%s&product=time-series&begin=%s&end=%s&maxt=maxt&mint=mint' % ("+".join([ str(_zc) for _zc in zip ]), begin.xsdLiteral(), end.xsdLiteral())
print uri

# Retrieve the data
xmls = urllib2.urlopen(uri).read()
print xmls

# Convert it to  DWML object
doc = xml.dom.minidom.parseString(xmls)
dom = doc.documentElement
r = DWML.CreateFromDOM(dom)

product = r.head().product()
print '%s %s' % (product.title(), product.category())
source = r.head().source()
print '%s (%s)' % (source.production_center().content(), source.production_center().sub_center())
data = r.data()

for i in range(len(data.location())):
    loc = data.location()[i]
    for j in range(len(loc.location_key())):
        key = loc.location_key()[j].content()
        print '%s [%s %s]' % (key, loc.point()[j].latitude(), loc.point()[j].longitude())
        for p in data.parameters():
            if p.applicable_location() != key:
                continue
            mint = maxt = None
            for t in p.temperature():
                if 'maximum' == t.type():
                    maxt = t
                elif 'minimum' == t.type():
                    mint = t
                print '%s (%s): %s' % (t.name()[0], t.units(), " ".join([ str(_v.content()) for _v in t.value() ]))
            time_layout = None
            for tl in data.time_layout():
                if tl.layout_key().content() == mint.time_layout():
                    time_layout = tl
                    break
            for ti in range(len(time_layout.start_valid_time())):
                start = time_layout.start_valid_time()[ti]
                end = time_layout.end_valid_time()[ti]
                print '%s to %s: min %s, max %s' % (time.strftime('%A, %B %d %H:%M:%S', start.timetuple()),
                                                    time.strftime('%H:%M:%S', end.timetuple()),
                                                    mint.value()[ti], maxt.value()[ti])
                
