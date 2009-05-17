"""XMLSchema -- Classes to support processing W3C XML Schema definitions.

This module supports processing DOM model representations of XML schema into a
Python object representation of the schema component model.

The module also provides a top-level class that supports schema processing.
"""

# Get the schema component datatypes
import structures

# Get the bindings relevant to schemas.  NB: Other implementations may be used
# in the future.
from structures import Schema as schema

## Local Variables:
## fill-column:78
## End:
    
