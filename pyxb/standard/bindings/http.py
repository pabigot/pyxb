from pyxb.standard.bindings.raw.http import *
import pyxb.standard.bindings.raw.http as raw_http
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class binding (raw_http.binding, _WSDL_binding_mixin):
    pass
raw_http.binding._SetSupersedingClass(binding)

class address (raw_http.address, _WSDL_port_mixin):
    pass
raw_http.address._SetSupersedingClass(address)

class operation (raw_http.operation, _WSDL_operation_mixin):
    def locationInformation (self):
        return self.location()
raw_http.operation._SetSupersedingClass(operation)
