import dict
import urllib2
import pyxb.utils.domutils as domutils
from xml.dom import minidom

# Get the list of dictionaries available from the service.
port_uri = 'http://services.aonaware.com/DictService/DictService.asmx'
uri = port_uri + '/DictionaryList'
dle_xml = urllib2.urlopen(uri).read()
dle_dom = domutils.StringToDOM(dle_xml)
dle = dict.ArrayOfDictionary.createFromDOM(dle_dom)

op_path = '/DictionaryInfo'
for d in dle.Dictionary:
    # Create a REST-style query to retrieve the information about this dictionary.
    uri = '%s%s?dictId=%s' % (port_uri, op_path, d.Id)
    resp = urllib2.urlopen(uri).read()
    # The response is a simple type derived from string, so we can
    # just extract and print it.
    di_resp = dict.CreateFromDOM(domutils.StringToDOM(resp))
    # Do the "encode" garbage because one of these dictionaries has a
    # non-ASCII character
    print "%s (%s)\n%s\n" % (d.Name.encode('utf-8'), d.Id.encode('utf-8'), di_resp.encode('utf-8'))
