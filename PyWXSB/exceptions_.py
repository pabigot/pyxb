"""Extensions of standard exceptions for PyWXSB events.

Yeah, I'd love this module to be named exceptions.py, but it can't
because the standard library has one of those, and we need to
reference it below.
"""

import exceptions

class PyWXSBException (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user should fix."""
    pass

class SchemaValidationError (PyWXSBException):
    """Raised when the XML hierarchy does not appear to be valid for an XML schema."""
    pass

class BadTypeValueError (PyWXSBException):
    """Raised when a value in an XML attribute does not conform to the simple type."""
    pass

class NotInNamespaceError (PyWXSBException):
    '''Raised when a name is referenced that is not defined in the appropriate namespace.'''
    __namespace = None
    __ncName = None

class BadPropertyError (PyWXSBException):
    """Raised when a schema component property is accessed on a component instance that does not define that property."""
    pass

class BadDocumentError (PyWXSBException):
    """Raised when processing document content and an error is encountered."""
    pass

class UnrecognizedElementError (BadDocumentError):
    """Raised when processing document and an unrecognized element is encountered."""

class ExtraContentError (BadDocumentError):
    """Raised when processing document and there is more material in an element content than expected."""

class NotAnElementError (UnrecognizedElementError):
    """Raised when processing document and a tag that is a type but not an element is encountered."""

class ProhibitedAttributeError (BadDocumentError):
    """Raised when an attribute that is prohibited is provided in an element."""

class MissingAttributeError (BadDocumentError):
    """Raised when an attribute that is required is missing in an element."""

class AttributeChangeError (BadDocumentError):
    """Raised when an attribute with a fixed value constraint is set to a different value."""

class PyWXSBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class LogicError (PyWXSBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when a code branch is taken that has not yet been implemented."""
