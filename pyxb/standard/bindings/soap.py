from raw.soap import *
import pyxb.standard.bindings.raw.soap as raw_soap
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin

class binding (raw_soap.binding, _WSDL_binding_mixin):
    pass
raw_soap.binding._SetClassRef(binding)

class address (raw_soap.address, _WSDL_port_mixin):
    pass
raw_soap.address._SetClassRef(address)
