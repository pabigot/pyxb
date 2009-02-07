"""XMLSchema -- Classes to support processing W3C XML Schema definitions.

This module supports processing DOM model representations of XML
schema.  It contains two sub-modules:

* structures defines XML Schema structure components corresponding to
  the schema data model

* datatypes addes the pre-defined schema datatypes such as string and
  integer to the XMLSchema namespace

The module also provides a top-level class that supports schema
processing.
"""



# Get the schema component datatypes
import structures

# Get the built-in datatypes
import datatypes

# Get the bindings relevant to schemas.  NB: Other implementations may
# be used in the future.
from bootstrap import schema
