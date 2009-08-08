import pyxb.bundles.opengis.sos_1_0 as sos
import pyxb.utils.utility
import sys
import traceback

# Import to define bindings for namespaces that appear in instance documents
import pyxb.bundles.opengis.sampling_1_0 as sampling
import pyxb.bundles.opengis.swe_1_0_1 as swe
import pyxb.bundles.opengis.tml

for f in sys.argv[1:]:
    print '------------------ %s' % (f,)
    xmls = pyxb.utils.utility.TextFromURI(f)
    try:
        instance = sos.CreateFromDocument(xmls)
        #print xmls
        print instance.toxml()
    except Exception, e:
        print '%s failed: %s' % (f, e)
        traceback.print_exception(*sys.exc_info())
    
