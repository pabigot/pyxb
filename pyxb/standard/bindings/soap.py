from raw.soap import *
import pyxb.standard.bindings.raw.soap as raw_soap
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class binding (raw_soap.binding, _WSDL_binding_mixin):
    pass
raw_soap.binding._SetSupersedingClass(binding)

class address (raw_soap.address, _WSDL_port_mixin):
    pass
raw_soap.address._SetSupersedingClass(address)

class operation (raw_soap.operation, _WSDL_operation_mixin):
    def locationInformation (self):
        rvl = []
        if self.soapAction() is not None:
            rvl.append('action=%s' % (self.soapAction(),))
        if self.style() is not None:
            rvl.append('style=%s' % (self.style(),))
        return ','.join(rvl)
raw_soap.operation._SetSupersedingClass(operation)
