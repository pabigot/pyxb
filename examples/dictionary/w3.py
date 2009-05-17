import pyxb.Namespace
import pyxb.xmlschema as xs
import sys

import pyxb.standard.bindings.wsdl as wsdl
import pyxb.standard.bindings.http as http
import pyxb.utils.domutils as domutils
from xml.dom import Node
from xml.dom import minidom
import pyxb.binding.generate

import urllib2
WSDL_uri = 'http://services.aonaware.com/DictService/DictService.asmx?WSDL'
#uri_src = urllib2.urlopen(WSDL_uri)
uri_src = open('dict.wsdl')
doc = minidom.parseString(uri_src.read())

#for ai in range(0, root.attributes.length):
#    attr = root.attributes.item(ai)
#    print '%s = %s [%s]' % (attr.name, attr.value, attr.namespaceURI)

spec = wsdl.definitions.CreateFromDOM(doc.documentElement, process_schema=True)

for s in spec.service():
    print 'Service: %s' % (s.name(),)
    if s.documentation():
        print s.documentation()
    for p in s.port():
        b = p.bindingReference()
        prot = b.protocolBinding()
        if not (isinstance(prot, http.binding) and ('POST' == prot.verb())):
            continue
        print '  Port %s at %s' % (p.name(), p.addressReference().location())
        ptr = b.portTypeReference()
        for op in b.operation():
            pt_op = ptr.operationMap()[op.name()]
            if op.operationReference() is not None:
                print '    %s (at %s)' % (op.name(), op.operationReference().locationInformation())
            else:
                print '    %s' % (op.name(),)
            print '      %s' % (pt_op.documentation(),)
            print '      Input: %s' % (pt_op.input()[0].message(),)
            print '      Output: %s' % (pt_op.output()[0].message(),)

