import dict
import urlparse
import urllib2
from xml.dom import minidom

port_uri = 'http://services.aonaware.com/DictService/DictService.asmx'
op_path = '/DictionaryList'
uri = '%s%s' % (port_uri, op_path)
dle_xml = urllib2.urlopen(uri).read()
dle_dom = minidom.parseString(dle_xml)
dle = dict.ArrayOfDictionary.createFromDOM(dle_dom.documentElement)

op_path = '/DictionaryInfo'
for d in dle.Dictionary():
    print '%s (%s)' % (d.Name(), d.Id())
    di_req = dict.DictionaryInfo(dictId=d.Id())
    args = { }
    for (t, eu) in di_req._ElementMap.items():
        args[eu.name().localName()] = eu.value(di_req)
    uri = '%s%s?%s' % (port_uri, op_path, '&'.join(['%s=%s' % _i for _i in args.items()]))
    resp = urllib2.urlopen(uri).read()
    di_resp = dict.CreateFromDOM(minidom.parseString(resp).documentElement)
    print di_resp
