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
        pass

    #def __new__ (cls, *args, **kw):
    #    return object.__new__(cls)

from exceptions_ import *
