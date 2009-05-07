from pyxb.standard.bindings.raw.http import *
import pyxb.standard.bindings.raw.http as raw_http
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_tBinding_mixin

class bindingType (raw_http.bindingType, _WSDL_tBinding_mixin):
    pass
raw_http.bindingType._SetClassRef(bindingType)

class binding (raw_http.binding, _WSDL_binding_mixin):
    pass
raw_http.binding._SetClassRef(binding)
