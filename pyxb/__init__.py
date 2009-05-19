"""PyXB stands for Python U{W3C XML Schema<http://www.w3.org/XML/Schema>} Bindings, and is pronounced
"pixbee".

This is the top-level entrypoint to the PyXB system.  Importing this
gets you all the L{exceptions<pyxb.exceptions_.PyXBException>}, and
L{pyxb.Namespace}.  For more functionality, delve into these
submodules:
 - L{pyxb.binding} Module used to generate the bindings and at runtime to
   support the generated bindings

 - L{pyxb.utils} Common utilities used in parsing, generating, and
   executing.  These modules must be imported separately.

 - L{pyxb.xmlschema} Module holding the
   L{structures<pyxb.xmlschema.structures>} that convert XMLSchema
   from a DOM model to a Python class model based on the XMLSchema
   components

"""

class cscRoot (object):
    """This little bundle of joy exists because in Python 2.6 it
    became an error to invoke C{object.__init__} with parameters (unless
    you also override C{__new__}, in which case it's only a warning.
    Whatever.).  Since I'm bloody not going to check in every class
    whether C{super(Myclass,self)} refers to C{object} (even if I could
    figure out how to do that, 'cuz the obvious solutions don't work),
    we'll just make this thing the root of all U{cooperative super
    calling<http://www.geocities.com/foetsch/python/new_style_classes.htm#super>}
    hierarchies."""
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

# Bring in Namespace
import Namespace
