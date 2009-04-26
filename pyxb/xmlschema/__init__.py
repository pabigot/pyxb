"""XMLSchema -- Classes to support processing W3C XML Schema definitions.

This module supports processing DOM model representations of XML
schema.  It contains several sub-modules:

* structures defines XML Schema structure components corresponding to
  the schema data model.  These classes closely conform to
  http://www.w3.org/TR/xmlschema-1/.

* datatypes addes the pre-defined schema datatypes such as string and
  integer to the XMLSchema namespace.  These classes closely conform
  to http://www.w3.org/TR/xmlschema-2/.

* facets defines structures that constrain the lexical and value space
  of simple types.

The module also provides a top-level class that supports schema
processing.
"""

# Get the schema component datatypes
import structures

# Get the built-in datatypes
#import datatypes

# Get the bindings relevant to schemas.  NB: Other implementations may
# be used in the future.
from bootstrap import schema
