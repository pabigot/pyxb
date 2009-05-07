from raw.soap12 import *
import pyxb.standard.bindings.raw.soap12 as raw_soap12
from pyxb.standard.bindings.wsdl import _WSDL_Binding_mixin

class binding (raw_soap12.binding, _WSDL_Binding_mixin):
    pass
raw_soap12.binding._SetClassRef(binding)

    
