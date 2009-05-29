"""PyXB stands for Python U{W3C XML
Schema<http://www.w3.org/XML/Schema>} Bindings, and is pronounced
"pixbee".  It enables translation between XML instance documents and
Python objects following rules specified by an XML Schema document.

This is the top-level entrypoint to the PyXB system.  Importing this
gets you all the L{exceptions<pyxb.exceptions_.PyXBException>}, and
L{pyxb.namespace}.  For more functionality, delve into these
submodules:

 - L{pyxb.xmlschema} Module holding the
   L{structures<pyxb.xmlschema.structures>} that convert XMLSchema
   from a DOM model to a Python class model based on the XMLSchema
   components.  Use this when you need to operate on the component
   model.

 - L{pyxb.binding} Module used to generate the bindings and at runtime
   to support the generated bindings.  Use this if you need to use the
   binding model or content model.

 - L{pyxb.utils} Common utilities used in parsing, generating, and
   executing.  The submodules must be imported separately.

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
        # Oh gross.  If this class descends from list (and probably dict), we
        # get here when object is *not* our direct superclass.  In that case,
        # we have to pass the arguments on up, or the strings don't get
        # created right.  Below is the only way I've figured out to detect the
        # situation.
        #
        # Note that we might also get here if you mix-in a class that used
        # object as a parent instead of cscRoot.  Don't do that.  If you do,
        # comment out the print in the if body to see where you screwed up.
        if issubclass(self.__class__.mro()[-2], ( list, dict )):
            super(cscRoot, self).__init__(*args)

__version__ = '0.2.0'
"""The version of PyXB"""

__url__ = 'http://pyxb.sourceforge.net'
"""The URL for PyXB's homepage"""

__license__ = 'Apache License 2.0'

# Bring in the exception hierarchy
from exceptions_ import *

# Bring in namespace stuff
import namespace

## Local Variables:
## fill-column:78
## End:
