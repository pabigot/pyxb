from pyxb.standard.bindings.raw.soaphttp import *
import pyxb.standard.bindings.raw.soaphttp as raw_soaphttp
from pyxb.standard.bindings.wsdl import _WSDL_Binding_mixin

class binding (raw_soaphttp.binding, _WSDL_Binding_mixin):
    pass
raw_soaphttp.binding._SetClassRef(binding)

    
