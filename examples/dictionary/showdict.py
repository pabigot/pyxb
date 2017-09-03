# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import dict
from pyxb.utils.six.moves.urllib.request import urlopen
import pyxb.utils.domutils as domutils
from xml.dom import minidom

# Get the list of dictionaries available from the service.
port_uri = 'http://services.aonaware.com/DictService/DictService.asmx'
uri = port_uri + '/DictionaryList'
dle_xml = urlopen(uri).read()
dle_dom = domutils.StringToDOM(dle_xml)
dle = dict.ArrayOfDictionary.createFromDOM(dle_dom)

op_path = '/DictionaryInfo'
for d in dle.Dictionary:
    # Create a REST-style query to retrieve the information about this dictionary.
    uri = '%s%s?dictId=%s' % (port_uri, op_path, d.Id)
    resp = urlopen(uri).read()
    print("%s (%s) : %d chars" % (d.Name, d.Id, len(resp)));

    # The response is a simple type derived from string, so we can
    # just extract and print it.  Excluded by default since it has
    # leading and trailing whitespace that causes problems with using
    # git to store the expected output.
    di_resp = dict.CreateFromDOM(domutils.StringToDOM(resp))
    if sys.stdout.isatty():
        print("%s\n" % di_resp);
