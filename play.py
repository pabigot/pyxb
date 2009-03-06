import PyWXSB.XMLSchema as xs
import PyWXSB.Namespace as Namespace
from PyWXSB.generate import PythonGenerator as Generator

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/kml21.xsd' ]

Namespace.XMLSchema.modulePath('xs.datatypes')

for file in files:
    try:
        wxs = xs.schema().CreateFromDOM(minidom.parse(file))
        ns = wxs.getTargetNamespace()
        enum_prefix_map = [ ( 'colorModeEnum', 'CM' )
                          , ( 'styleStateEnum', 'SS' )
                          , ( 'itemIconStateEnum', 'IIS' )
                          , ( 'listItemTypeEnum', 'LIT' )
                          , ( 'unitsEnum', 'Units' )
                          ]
        for (std_name, enum_prefix) in enum_prefix_map:
            cm = ns.lookupTypeDefinition(std_name)
            if cm is not None:
                facet = cm.facets().get(xs.facets.CF_enumeration, None)
                if facet is not None:
                    facet.enumPrefix('%s_' % enum_prefix)

        gen = Generator(ns, 'xs')
        print "\n".join(gen.generateDefinitions([ns.lookupTypeDefinition('formChoice')]))
        #print "\n".join(gen.generateDefinitions([ns.lookupTypeDefinition('viewRefreshModeEnum')]))
        #print "\n".join(gen.generateDefinitions([ns.lookupTypeDefinition('NetworkLinkControlType')]))
        #print "\n".join(gen.generateDefinitions(ns.typeDefinitions()))

    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())


