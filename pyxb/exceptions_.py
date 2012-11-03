# -*- coding: utf-8 -*-
# Copyright 2009-2012, Peter A. Bigot
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

    def __init__ (self, *args, **kw):
        """Create an exception indicating a PyXB-related problem.

        If no args are present, a default argument is taken from the
        C{message} keyword.

        @keyword message : Text to provide the user with information about the problem.
        """
        if 0 == len(args) and 'message' in kw:
            args = (kw.pop('message'),)
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

class NotInNamespaceError (PyXBException):
    '''Raised when a name is referenced that is not defined in the appropriate namespace.'''
    __namespace = None
    __ncName = None

class BadDocumentError (PyXBException):
    """Raised when processing document content and an error is encountered."""
    pass

class StructuralBadDocumentError (BadDocumentError):
    """Raised when processing document and the content model is not satisfied."""
    @property
    def element_use (self):
        """The L{pyxb.binding.content.ElementDeclaration} instance to which the content should conform, if available."""
        return self.__elementUse

    @property
    def container (self):
        """The L{pyxb.binding.basis.complexTypeDefinition} instance to which the content would belong, if available."""
        return self.__container

    @property
    def content (self):
        """The value which could not be reconciled with the content model."""
        return self.__content
    
    def __init__ (self, *args, **kw):
        """Raised when processing document and the content model is not satisfied.

        @keyword content : The value that could not be reconciled with the content model
        @keyword container : Optional binding instance into which the content was to be assigned
        @keyword element_use : Optional reference to an element use identifying the element to which the value was to be reconciled
        """
        self.__content = kw.pop('content', None)
        if args:
            self.__content = args[0]
        self.__container = kw.pop('container', None)
        self.__elementUse = kw.pop('element_use', None)
        if self.__content is not None:
            if self.__container is not None:
                kw.setdefault('message', '%s cannot accept wildcard content %s' % (self.__container, self.__content))
            elif self.__elementUse is not None:
                kw.setdefault('message', '%s not consistent with content model for %s' % (self.__content, self.__elementUse))
            else:
                kw.setdefault('message', str(self.__content))
        BadDocumentError.__init__(self, **kw)

class UnrecognizedDOMRootNodeError (StructuralBadDocumentError):
    """A root DOM node could not be resolved to a schema element"""

    node = None
    """The L{xml.dom.Element} instance that could not be recognized"""

    def __get_node_name (self):
        """The QName of the L{node} as a L{pyxb.namespace.ExpandedName}"""
        import pyxb.namespace
        return  pyxb.namespace.ExpandedName(self.node.namespaceURI, self.node.localName)
    node_name = property(__get_node_name)

    def __init__ (self, node):
        """@param node: the value for the L{node} attribute."""
        self.node = node
        super(UnrecognizedDOMRootNodeError, self).__init__(node)

class UnrecognizedContentError (StructuralBadDocumentError):
    """Raised when processing document and an element does not match the content model."""
    pass

class ExtraContentError (UnrecognizedContentError):
    """Raised when processing document and there is more material in an element content than expected."""
    pass

class BindingValidationError (UnrecognizedContentError):
    """Raised when the content of a binding object is not consistent with its content model"""
    pass

class UnexpectedNonElementContentError (UnrecognizedContentError):
    """Raised when an element is given non-element content but may not contain such."""
    pass

class ValidationError (PyXBException):
    """Raised when something in the infoset fails to satisfy a content model or attribute requirement."""
    pass

class SimpleTypeValueError (ValidationError):
    """Raised when a simple type value does not satisfy its constraints."""
    type = None
    """The L{pyxb.binding.basis.simpleTypeDefinition} that constrains values."""
    
    value = None
    """The value that violates the constraints of L{type}.  In some
    cases this is a tuple of arguments passed to a constructor that
    failed with a built-in exception likeC{ValueError} or
    C{OverflowError}."""

    def __init__ (self, type, value):
        """@param type: the value for the L{type} attribute.
        @param value: the value for the L{value} attribute.
        """
        self.type = type
        self.value = value
        super(SimpleTypeValueError, self).__init__(type, value)

class SimpleListValueError (SimpleTypeValueError):
    """Raised when a list simple type contains a member that does not satisfy its constraints.

    In this case, L{type} is the type of the list, and the value
    C{type._ItemType} is the type for which the value is
    unacceptable."""
    pass

class SimpleUnionValueError (SimpleTypeValueError):
    """Raised when a union simple type contains a member that does not satisfy its constraints.

    In this case, L{type} is the type of the union, and the value
    C{type._MemberTypes} is the set of types for which the value is
    unacceptable."""
    pass

class SimpleFacetValueError (SimpleTypeValueError):
    """Raised when a simple type value does not satisfy a facet constraint.

    This extends L{SimpleTypeValueError} with the L{facet} field which
    can be used to determine why the value is unacceptable."""

    type = None
    """The L{pyxb.binding.basis.simpleTypeDefinition} that constrains values."""
    
    value = None
    """The value that violates the constraints of L{type}.  In some
    cases this is a tuple of arguments passed to a constructor that
    failed with a built-in exception likeC{ValueError} or
    C{OverflowError}."""

    facet = None
    """The specific facet that is violated by the value."""

    def __init__ (self, type, value, facet):
        """@param type: the value for the L{type} attribute.
        @param value: the value for the L{value} attribute.
        """
        self.type = type
        self.value = value
        self.facet = facet
        # Bypass immediate parent
        super(SimpleTypeValueError, self).__init__(type, value, facet)

class SimplePluralValueError (SimpleTypeValueError):
    """Raised when context requires a plural value.

    Unlike L{SimpleListValueError}, in this case the plurality is
    external to C{type}, for example when an element has simple
    content and allows multiple occurrences."""
    pass

class AttributeValidationError (ValidationError):
    """Raised when an attribute requirement is not satisfied."""

    type = None
    """The L{pyxb.binding.basis.complexTypeDefinition} subclass of the instance."""

    tag = None
    """The name of the attribute."""
    
    instance = None
    """The binding instance, if available."""

    def __init__ (self, type, tag, instance=None):
        """@param type: the value for the L{type} attribute.
        @param tag: the value for the L{tag} attribute.
        @param instance: the value for the L{instance} attribute.
        """
        self.type = type
        self.tag = tag
        self.instance = instance
        super(AttributeValidationError, self).__init__(type, tag, instance)

class UnrecognizedAttributeError (AttributeValidationError):
    """Attempt to reference an attribute not sanctioned by content model."""
    pass

class ProhibitedAttributeError (AttributeValidationError):
    """Raised when an attribute that is prohibited is provided in an element."""
    pass

class MissingAttributeError (AttributeValidationError):
    """Raised when an attribute that is required is missing in an element."""
    pass

class AttributeChangeError (AttributeValidationError):
    """Attempt to change an attribute that has a fixed value constraint."""
    pass

class AttributeValueError (AttributeValidationError):
    """The value of an attribute does not satisfy its content constraints."""
    pass
    
class NoNillableSupportError (PyXBException):
    """Raised when checking _isNil on a type that does not support nillable."""

    instance = None
    """The binding instance on which an inappropriate operation was invoked."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(NoNillableSupportError, self).__init__(instance)

class ContentInNilInstanceError (PyXBException):
    """Raised when an element that is marked to be nil is assigned content."""

    instance = None
    """The binding instance which is xsi:nil"""

    content = None
    """The content that was to be assigned to the instance."""

    def __init__ (self, instance, content):
        """@param instance: the binding instance that is marked nil.
        This will be available in the L{instance} attribute.

        @param content: the content found to be in violation of the nil requirement.
        This will be available in the L{content} attribute.

        """
        self.instance = instance
        self.content = content
        super(ContentInNilInstanceError, self).__init__(instance, content)

class BindingError (PyXBException):
    """Raised when the bindings are mis-used.

    These are not validation errors, but rather structural errors.
    For example, attempts to extract complex content from a type that
    requires simple content, or vice versa.  """

class NotSimpleContentError (BindingError):
    """An operation that requires simple content was invoked on a
    complex type instance that does not have simple content."""

    instance = None
    """The binding instance which should have had simple content."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(BindingError, self).__init__(instance)
    pass

class SimpleContentAbsentError (BindingError):
    """An instance with simple content was not provided with a value."""

    instance = None
    """The binding instance for which simple content is missing."""

    def __init__ (self, instance):
        """@param instance: the binding instance that is missing
        content.  This will be available in the L{instance}
        attribute."""
        self.instance = instance
        super(SimpleContentAbsentError, self).__init__(instance)

class NotComplexContentError (BindingError):
    """An operation that requires a content model was invoked on a
    complex type instance that has empty or simple content."""

    instance = None
    """The binding instance which should have had a content model."""

    def __init__ (self, instance):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        super(BindingError, self).__init__(instance)

class AbstractElementError (BindingError):
    """Attempt to create an instance of an abstract element.

    Raised when an element is created and the identified binding is
    abstract.  Such elements cannot be created directly; instead the
    creation must derive from an instance of the abstract element's
    substitution group."""

    element = None
    """The abstract L{pyxb.binding.basis.element} in question"""

    value = None
    """The value proposed for the L{element}.  This is usually going
    to be a C{xml.dom.Node} used in the attempt to create the element,
    C{None} if the abstract element was invoked without a node, or
    another type if
    L{pyxb.binding.content.ElementDeclaration.toDOM} is
    mis-used."""

    def __init__ (self, element, value=None):
        """@param element: the value for the L{element} attribute.
        @param value: the value for the L{value} attribute."""
        self.element = element
        self.value = value
        super(AbstractElementError, self).__init__(element, value)

class AbstractInstantiationError (BindingError):
    """Attempt to create an instance of an abstract complex type.

    These types are analogous to abstract base classes, and cannot be
    created directly.  A type should be used that extends the abstract
    class."""

    type = None
    """The abstract L{pyxb.binding.basis.complexTypeDefinition} subclass used"""

    def __init__ (self, type):
        """@param type: the value for the L{type} attribute."""
        self.type = type
        super(AbstractInstantiationError, self).__init__(type)


class ReservedNameError (BindingError):
    """Reserved name set in binding instance."""

    name = None
    """The name that was caught being assigned"""

    def __init__ (self, instance, name):
        """@param instance: the binding instance that was mis-used.
        This will be available in the L{instance} attribute."""
        self.instance = instance
        self.name = name
        # Jump over BindingError in parent invocation
        super(BindingError, self).__init__(instance, name)

class PyXBError (exceptions.Exception):
    """Base class for exceptions that indicate a problem that the user probably can't fix."""
    pass
    
class UsageError (PyXBError):
    """Raised when the code detects user violation of an API."""

class LogicError (PyXBError):
    """Raised when the code detects an implementation problem."""

class IncompleteImplementationError (LogicError):
    """Raised when required capability has not been implemented.

    This is only used where it is reasonable to expect the capability
    to be present, such as a feature of XML schema that is not
    supported (e.g., the redefine directive)."""
