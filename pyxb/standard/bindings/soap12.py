from raw.soap12 import *
import pyxb.standard.bindings.raw.soap12 as raw_soap12
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_tBinding_mixin

class tBinding (raw_soap12.tBinding, _WSDL_tBinding_mixin):
    pass
raw_soap12.tBinding._SetClassRef(tBinding)

class binding (raw_soap12.binding, _WSDL_binding_mixin):
    pass
raw_soap12.binding._SetClassRef(binding)
    
