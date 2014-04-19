import pyxb
import spirit

instance = spirit.CreateFromDocument(file('sample.xml').read())
assert 'generated' == instance.busInterfaces.busInterface[1].mirroredSlave.baseAddresses.remapAddress[0].resolve
