from pyxb.standard.bindings.raw.soaphttp import *
import pyxb.standard.bindings.raw.soaphttp as raw_soaphttp
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_tBinding_mixin

class bindingType (raw_soaphttp.bindingType, _WSDL_tBinding_mixin):
    pass
raw_soaphttp.bindingType._SetClassRef(bindingType)

class binding (raw_soaphttp.binding, _WSDL_binding_mixin):
    pass
raw_soaphttp.binding._SetClassRef(binding)
