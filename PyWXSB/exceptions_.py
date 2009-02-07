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
    '''Raised when a name is referenced that is not defined in the appropriate namesace.'''
    __namespace = None
    __ncName = None

class PyWXSBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class LogicError (PyWXSBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when a code branch is taken that has not yet been implemented."""
