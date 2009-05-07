from raw.soap12 import *
import pyxb.standard.bindings.raw.soap12 as raw_soap12
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_port_mixin

class binding (raw_soap12.binding, _WSDL_binding_mixin):
    pass
raw_soap12.binding._SetClassRef(binding)
    
class address (raw_soap12.address, _WSDL_port_mixin):
    pass
raw_soap12.address._SetClassRef(address)
