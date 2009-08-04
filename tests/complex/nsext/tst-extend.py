import common4app

x = common4app.extended('hi', 'there')
assert x.elt() == 'hi'
assert x.extElt() == 'there'

import common
assert issubclass(common4app.extended.typeDefinition(), common.base.typeDefinition())
