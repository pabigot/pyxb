# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Extensions of standard exceptions for PyXB events.

Yeah, I'd love this module to be named exceptions.py, but it can't
because the standard library has one of those, and we need to
reference it below.
"""

import exceptions

class PyXBException (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user should fix."""
    pass

class SchemaValidationError (PyXBException):
    """Raised when the XML hierarchy does not appear to be valid for an XML schema."""
    pass

class NamespaceError (PyXBException):
    """Violation of some rule relevant to XML Namespaces"""
    pass

class BindingGenerationError (PyXBException):
    """Raised when something goes wrong generating the binding classes"""
    pass

class NamespaceUniquenessError (PyXBException):
    """Raised when an attempt is made to record multiple objects of the same name in the same namespace category."""
    pass

class BadTypeValueError (PyXBException):
    """Raised when a value in an XML attribute does not conform to the simple type."""
    pass

class NotInNamespaceError (PyXBException):
    '''Raised when a name is referenced that is not defined in the appropriate namespace.'''
    __namespace = None
    __ncName = None

class BadPropertyError (PyXBException):
    """Raised when a schema component property is accessed on a component instance that does not define that property."""
    pass

class BadDocumentError (PyXBException):
    """Raised when processing document content and an error is encountered."""
    pass

class StructuralBadDocumentError (BadDocumentError):
    """Raised when processing document and the content model is not satisfied."""

class AbstractElementError (StructuralBadDocumentError):
    """Raised when attempting to construct an element that is abstract."""
    pass

class UnrecognizedContentError (StructuralBadDocumentError):
    """Raised when processing document and an element does not match the content model."""

class UnrecognizedElementError (UnrecognizedContentError):
    """Raised when creating an instance from a document with an unrecognized root element."""

class ExtraContentError (StructuralBadDocumentError):
    """Raised when processing document and there is more material in an element content than expected."""

class MissingContentError (StructuralBadDocumentError):
    """Raised when processing document and expected content is not present.  See also UnrecognizedContentError."""

class NotAnElementError (UnrecognizedContentError):
    """Raised when processing document and a tag that is a type but not an element is encountered."""

class UnrecognizedAttributeError (BadDocumentError):
    """Raised when an attribute is found that is not sanctioned by the content model."""

class ProhibitedAttributeError (BadDocumentError):
    """Raised when an attribute that is prohibited is provided in an element."""

class MissingAttributeError (BadDocumentError):
    """Raised when an attribute that is required is missing in an element."""

class AttributeChangeError (BadDocumentError):
    """Raised when an attribute with a fixed value constraint is set to a different value."""

class AbstractInstantiationError (PyXBException):
    """Raised when somebody tries to instantiate an abstract complex type."""

class DOMGenerationError (PyXBException):
    """Raised when converting binding to DOM and something goes wrong."""
    pass

class NoNillableSupportError (PyXBException):
    """Raised when checking _isNil on a type that does not support nillable."""
    pass

class BindingValidationError (PyXBException):
    """Raised when the content of a binding object is not consistent with its content model"""
    pass

class NotSimpleContentError (BindingValidationError):
    """Raised when an operation that requires simple content is
    invoked on a complex type that does not have simple content."""
    pass

class NoContentModel (BindingValidationError):
    """Raised when an operation is attempted that requires a content
    model, but the complex type has empty or simple content."""

class PyXBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class LogicError (PyXBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when a code branch is taken that has not yet been implemented."""
