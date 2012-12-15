# -*- coding: utf-8 -*-
import pyxb.bundles.common.xhtml1 as xhtml
import pyxb.utils.domutils
import xml.dom.minidom
from xml.dom import Node

pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(xhtml.Namespace)

src = file('in.xhtml').read()
i1 = xhtml.CreateFromDocument(src)
xmls = i1.toDOM().toxml('utf-8')
file('out.xhtml', 'w').write(xmls)
