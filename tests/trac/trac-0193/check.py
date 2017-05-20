import trac193
import pyxb.binding.datatypes as xs

bdv = trac193.Money._UseForTag('Value').elementBinding().typeDefinition()
assert bdv == xs.integer
assert trac193.Money._UseForTag('Currency').elementBinding().typeDefinition() == xs.anySimpleType
assert trac193.Money._UseForTag('Season').elementBinding().typeDefinition() == xs.anyType

rdv = trac193.OpenDeliveries._UseForTag('Value').elementBinding().typeDefinition()
assert rdv == xs.integer
assert trac193.OpenDeliveries._UseForTag('Currency').elementBinding().typeDefinition() == xs.anySimpleType
assert trac193.OpenDeliveries._UseForTag('Season').elementBinding().typeDefinition() == xs.anyType

assert issubclass(rdv, bdv)
