"""PyWXSB -- Python W3C XML Schema Bindings.

binding - Module used to generate the bindings and at runtime to
support the generated bindings

utils - Common utilities used in parsing, generating, and running

xmlschema - Class that convert XMLSchema from a DOM model to a Python
class model based on the XMLSchema components

"""

class cscRoot (object):
    """This little bundle of joy exists because in Python 2.6 it
    became an error to invoke object.__init__ with parameters (unless
    you also override __new__, in which case it's only a warning.
    Whatever.).  Since I'm bloody not going to check in every class
    whether super(Myclass,self) refers to object (even if I could
    figure out how to do that, 'cuz the obvious solutions don't work),
    we'll just make this thing the root of all cooperative super
    calling hierarchies."""
    def __init__ (self, *args, **kw):
        # Oh gross.  If this class descends from unicode or string, we
        # get here when object is *not* our direct superclass.  In
        # that case, we have to pass the arguments on up, or the
        # strings don't get created right.  Below is the only way I've
        # figured out to detect the situation.
        if self.__class__ != self.__class__.mro()[-1]:
            super(cscRoot, self).__init__(*args, **kw)

# Bring in the exception hierarchy
from exceptions_ import *
