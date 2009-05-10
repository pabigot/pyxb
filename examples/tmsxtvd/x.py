import tms
import pyxb.utils.domutils
import xml.dom
import xml.dom.minidom
import pyxb.Namespace

xmls = open('tmsdatadirect_sample.xml').read()
dom = xml.dom.minidom.parseString(xmls)

instance = tms.CreateFromDOM(dom.documentElement)
print instance
