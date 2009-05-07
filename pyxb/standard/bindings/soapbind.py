from raw.soapbind import *
import pyxb.standard.bindings.raw.soapbind as raw_soapbind
from pyxb.standard.bindings.wsdl import _WSDL_Binding_mixin

class binding (raw_soapbind.binding, _WSDL_Binding_mixin):
    pass
raw_soapbind.binding._SetClassRef(binding)
