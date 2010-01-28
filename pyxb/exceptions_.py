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

    """The arguments passed to the exception constructor."""
    _args = None

    """The keywords passed to the exception constructor.

    @note: Do not pop values from the keywords array in subclass
    constructors that recognize and extract values from them.  They
    should be kept around so they're accessible generically."""
    _kw = None

    @property
    def message (self):
        '''A message to help a human understand the problem.'''
        if self.__message is None:
            return str(self)
        return self.__message

    def __str__ (self):
        """Override to use the system-provided message, if available."""
        if self.__message is not None:
            return '%s: %s' % (type(self).__name__, self.__message)
        return exceptions.Exception.__str__(self)

    def __init__ (self, *args, **kw):
        """Create an exception indicating a PyXB-related problem.

        @keyword message : Text to provide the user with information about the problem.
        """
        self.__message = kw.get('message')
        self._args = args
        self._kw = kw
        exceptions.Exception.__init__(self, *args)

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

    @property
    def element_use (self):
        """The L{pyxb.binding.content.ElementUse} instance to which the content should conform, if available."""
        return self.__elementUse

    @property
    def container (self):
        """The L{pyxb.binding.basis.complexTypeDefinition} instance to which the content would belong, if available."""
        return self.__container

    @property
    def content (self):
        """The value which could not be reconciled with the content model."""
        return self.__content
    
    def __init__ (self, content, **kw):
        """Raised when processing document and an element does not match the content model.

        @param content : The value that could not be reconciled with the content model
        @keyword container : Optional binding instance into which the content was to be assigned
        @keyword element_use : Optional reference to an element use identifying the element to which the value was to be reconciled
        """
        self.__content = content
        self.__container = kw.get('container')
        self.__elementUse = kw.get('element_use')
        if self.__container is not None:
            kw.setdefault('message', '%s cannot accept wildcard content %s' % (self.__container, self.__content))
        elif self.__elementUse is not None:
            kw.setdefault('message', '%s not consistent with content model for %s' % (self.__content, self.__elementUse))
        else:
            kw.setdefault('message', str(self.__content))
        StructuralBadDocumentError.__init__(self, **kw)

class UnrecognizedElementError (UnrecognizedContentError):
    """Raised when creating an instance from a document with an unrecognized root element."""

    @property
    def element_name (self):
        """The L{pyxb.namespace.ExpandedName} of the element that was not recognized."""
        return self.__elementName

    @property
    def dom_node (self):
        """The DOM node associated with the unrecognized element, if available."""
        return self.__domNode

    def __init__ (self, **kw):
        """Raised when creating an instance from a document with an unrecognized root element.

        @keyword element_name : The expanded name of the outermost element
        @keyword dom_node : The DOM node of the outermost element, if available
        """
        self.__domNode = kw.get('dom_node')
        self.__elementName = kw.get('element_name')
        if self.__elementName is None:
            if self.__domNode is not None:
                import pyxb.namespace
                self.__elementName = pyxb.namespace.ExpandedName(self.__domNode.namespaceURI, self.__domNode.localName)
            else:
                raise LogicError('No source for element_name  in UnrecognizedElementError')
        kw.setdefault('message', 'No element binding available for %s' % (self.__elementName,))
        UnrecognizedContentError.__init__(self, self.__domNode, **kw)

class ExtraContentError (StructuralBadDocumentError):
    """Raised when processing document and there is more material in an element content than expected."""

class ContentInNilElementError (ExtraContentError):
    """Raised when an element that is marked to be nil has content."""
    pass

class MissingContentError (StructuralBadDocumentError):
    """Raised when processing document and expected content is not present.  See also UnrecognizedContentError."""

class NotAnElementError (UnrecognizedContentError):
    """Raised when processing document and a tag that is a type but not an element is encountered."""

    @property
    def element_name (self):
        """The L{pyxb.namespace.ExpandedName} of the element that was not recognized."""
        return self.__elementName

    @property
    def containing_type (self):
        """The L{pyxb.binding.content.complexTypeDefinition} in which the element was unrecognized."""
        return self.__containingType

    def __init__ (self, element_name, containing_type, **kw):
        """Raised when a document inner element is recognized as a type rather than an element.

        @param element_name : The name of the inner element from the document
        @param containing_type : The L{pyxb.binding.content.complexTypeDefinition} class in which the lookup failed
        """
        self.__elementName = element_name
        self.__containingType = containing_type
        kw.setdefault('message', 'Unable to locate element %s in type %s' % (element_name, self.__containingType._ExpandedName))
        UnrecognizedContentError.__init__(self, None, **kw)

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
