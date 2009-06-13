from pyxb.standard.bindings.raw.http import *
import pyxb.standard.bindings.raw.http as raw_http
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class bindingType (raw_http.bindingType, _WSDL_binding_mixin):
    pass
raw_http.bindingType._SetSupersedingClass(bindingType)

class addressType (raw_http.addressType, _WSDL_port_mixin):
    pass
raw_http.addressType._SetSupersedingClass(addressType)

class operationType (raw_http.operationType, _WSDL_operation_mixin):
    def locationInformation (self):
        return self.location()
raw_http.operationType._SetSupersedingClass(operationType)
