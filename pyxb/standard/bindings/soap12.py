from raw.soap12 import *
import pyxb.standard.bindings.raw.soap12 as raw_soap12
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class binding (raw_soap12.binding, _WSDL_binding_mixin):
    pass
raw_soap12.binding._SetSupersedingClass(binding)
    
class address (raw_soap12.address, _WSDL_port_mixin):
    pass
raw_soap12.address._SetSupersedingClass(address)

class operation (raw_soap12.operation, _WSDL_operation_mixin):
    def locationInformation (self):
        rvl = []
        if self.soapAction() is not None:
            rvl.append('action=%s' % (self.soapAction(),))
        if self.style() is not None:
            rvl.append('style=%s' % (self.style(),))
        if self.soapActionRequired():
            rvl.append('REQUIRED')
        return ','.join(rvl)
raw_soap12.operation._SetSupersedingClass(operation)
