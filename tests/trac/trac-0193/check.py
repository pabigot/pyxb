import trac193
import pyxb.binding.datatypes as xs

bdv = trac193.Money._UseForTag('Value').elementBinding().typeDefinition()
assert bdv == xs.integer
assert trac193.Money._UseForTag('Currency').elementBinding().typeDefinition() == xs.anySimpleType
assert trac193.Money._UseForTag('Season').elementBinding().typeDefinition() == xs.anyType

rdv = trac193.OpenDeliveries._UseForTag('Value').elementBinding().typeDefinition()
assert rdv == trac193.Value
assert trac193.OpenDeliveries._UseForTag('Currency').elementBinding().typeDefinition() == trac193.Currency
assert trac193.OpenDeliveries._UseForTag('Season').elementBinding().typeDefinition() == trac193.Season

assert xs.integer != trac193.Value
assert xs.anySimpleType != trac193.Currency
assert xs.anyType != trac193.Season

# In fact something that refines xs.int (Python int) is not a subclass
# of xs.integer (Python long).  This is a flaw in PyXB's data type
# hierarchy which can't be easily fixed, so ignore it.
assert not issubclass(rdv, bdv)
