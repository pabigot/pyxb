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
    def __init__ (self, namespace, *args, **kw):
        PyXBException.__init__(self, *args, **kw)
        self.__namespace = namespace

    def namespace (self): return self.__namespace

class NamespaceArchiveError (PyXBException):
    """Problem related to namespace archives"""
    pass

class SchemaUniquenessError (PyXBException):
    """Raised when somebody tries to create a schema component using a
    schema that has already been used in that namespace.  Import and
    include processing would have avoided this, so somebody asked for
    it specifically."""
    def __init__ (self, namespace, schema_location, existing_schema, *args, **kw):
        # Prior to 2.5, exceptions did not inherit from object, and
        # super could not be used.
        #super(SchemaUniquenessError, self).__init__(*args, **kw)
        PyXBException.__init__(self, *args, **kw)
        self.__namespace = namespace
        self.__schemaLocation = schema_location
        self.__existingSchema = existing_schema

    def namespace (self): return self.__namespace
    def schemaLocation (self): return self.__schemaLocation
    def existingSchema (self): return self.__existingSchema

class BindingGenerationError (PyXBException):
    """Raised when something goes wrong generating the binding classes"""
    pass

class NamespaceUniquenessError (NamespaceError):
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

class ContentInNilElementError (ExtraContentError):
    """Raised when an element that is marked to be nil has content."""
    pass

class MissingContentError (StructuralBadDocumentError):
    """Raised when processing document and expected content is not present.  See also UnrecognizedContentError."""

class NotAnElementError (UnrecognizedContentError):
    """Raised when processing document and a tag that is a type but not an element is encountered."""

class UnrecognizedAttributeError (BadDocumentError):
    """Raised when an attribute is found that is not sanctioned by the content model."""

class ValidationError (PyXBException):
    """Raised when something in the infoset fails to satisfy a content model or attribute requirement."""
    pass

class AttributeValidationError (ValidationError):
    """Raised when an attribute requirement is not satisfied."""
    pass

class ProhibitedAttributeError (AttributeValidationError):
    """Raised when an attribute that is prohibited is provided in an element."""

class MissingAttributeError (AttributeValidationError):
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

class BindingValidationError (ValidationError):
    """Raised when the content of a binding object is not consistent with its content model"""
    pass

class UnexpectedNonElementContentError (ValidationError):
    """Raised when an element is given non-element content but may not contain such."""
    pass

class NoContentModel (BindingValidationError):
     """Raised when an operation is attempted that requires a content
     model, but the complex type has empty or simple content."""
     pass

class BindingError (PyXBException):
    """Raised when the bindings are mis-used."""
    pass

class NotSimpleContentError (BindingError):
    """Raised when an operation that requires simple content is
    invoked on a complex type that does not have simple content."""
    pass

class NotComplexContentError (BindingError):
    """Raised when an operation is attempted that requires a content
    model, but the complex type has empty or simple content."""
    pass

class PyXBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class UsageError (PyXBError):
    """Raised when the code detects arguments to a public
    operation."""

class LogicError (PyXBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when a code branch is taken that has not yet been implemented."""
