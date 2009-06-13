from raw.soap import *
import pyxb.standard.bindings.raw.soap as raw_soap
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class tBinding (raw_soap.tBinding, _WSDL_binding_mixin):
    pass
raw_soap.tBinding._SetSupersedingClass(tBinding)

class tAddress (raw_soap.tAddress, _WSDL_port_mixin):
    pass
raw_soap.tAddress._SetSupersedingClass(tAddress)

class tOperation (raw_soap.tOperation, _WSDL_operation_mixin):
    def locationInformation (self):
        rvl = []
        if self.soapAction() is not None:
            rvl.append('action=%s' % (self.soapAction(),))
        if self.style() is not None:
            rvl.append('style=%s' % (self.style(),))
        return ','.join(rvl)
raw_soap.tOperation._SetSupersedingClass(tOperation)
