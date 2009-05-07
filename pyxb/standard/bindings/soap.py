from raw.soapbind import *
import pyxb.standard.bindings.raw.soapbind as raw_soapbind
from pyxb.standard.bindings.wsdl import _WSDL_binding_mixin, _WSDL_tBinding_mixin

class tBinding (raw_soapbind.tBinding, _WSDL_tBinding_mixin):
    pass
raw_soapbind.tBinding._SetClassRef(tBinding)

class binding (raw_soapbind.binding, _WSDL_binding_mixin):
    pass
raw_soapbind.binding._SetClassRef(binding)
