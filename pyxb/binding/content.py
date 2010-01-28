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

"""Helper classes that maintain the content model of XMLSchema in the binding
classes.

L{AttributeUse} and L{ElementUse} record information associated with a binding
class, for example the types of values, the original XML QName or NCName, and
the Python field in which the values are stored.  They also provide the
low-level interface to set and get the corresponding values in a binding
instance.

L{ContentModelTransition}, L{ContentModelState}, and L{ContentModel} are used
to store a deterministic finite automaton which is used to translate between
binding instances and other representations (e.g., DOM nodes)

L{ModelGroupAllAlternative} and L{ModelGroupAll} represent special nodes in
the DFA that support a model group with compositor "all" in a way that does
not result in an exponential state explosion in the DFA.

L{DFAStack} and its related internal classes are used in stream-based
processing of content.

L{Wildcard} holds content-related information used in the content model.
"""

import pyxb
import pyxb.namespace
import basis

import xml.dom

class AttributeUse (pyxb.cscRoot):
    """A helper class that encapsulates everything we need to know
    about the way an attribute is used within a binding class.

    Attributes are stored internally as pairs C{(provided, value)}, where
    C{provided} is a boolean indicating whether a value for the attribute was
    provided externally, and C{value} is an instance of the attribute
    datatype.  The C{provided} flag is used to determine whether an XML
    attribute should be added to a created DOM node when generating the XML
    corresponding to a binding instance.
    """

    __name = None       # ExpandedName of the attribute
    __id = None         # Identifier used for this attribute within the owning class
    __key = None        # Private attribute used in instances to hold the attribute value
    __dataType = None  # PST datatype
    __unicodeDefault = None     # Default value as a unicode string, or None
    __defaultValue = None       # Default value as an instance of datatype, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, name, id, key, data_type, unicode_default=None, fixed=False, required=False, prohibited=False):
        """Create an AttributeUse instance.

        @param name: The name by which the attribute is referenced in the XML
        @type name: L{pyxb.namespace.ExpandedName}

        @param id: The Python identifier for the attribute within the
        containing L{pyxb.basis.binding.complexTypeDefinition}.  This is a
        public identifier, derived from the local part of the attribute name
        and modified to be unique, and is usually used as the name of the
        attribute's inspector method.
        @type id: C{str}

        @param key: The string used to store the attribute
        value in the dictionary of the containing
        L{pyxb.basis.binding.complexTypeDefinition}.  This is mangled so
        that it is unique among and is treated as a Python private member.
        @type key: C{str}

        @param data_type: The class reference to the subclass of
        L{pyxb.binding.basis.simpleTypeDefinition} of which the attribute
        values must be instances.
        @type data_type: C{type}

        @keyword unicode_default: The default value of the attribute as
        specified in the schema, or None if there is no default attribute
        value.  The default value (of the keyword) is C{None}.
        @type unicode_default: C{unicode}

        @keyword fixed: If C{True}, indicates that the attribute, if present,
        must have the value that was given via C{unicode_default}.  The
        default value is C{False}.
        @type fixed: C{bool}

        @keyword required: If C{True}, indicates that the attribute must appear
        in the DOM node used to create an instance of the corresponding
        L{pyxb.binding.basis.complexTypeDefinition}.  The default value is
        C{False}.  No more that one of L{required} and L{prohibited} should be
        assigned C{True}.
        @type required: C{bool}

        @keyword prohibited: If C{True}, indicates that the attribute must
        B{not} appear in the DOM node used to create an instance of the
        corresponding L{pyxb.binding.basis.complexTypeDefinition}.  The
        default value is C{False}.  No more that one of L{required} and
        L{prohibited} should be assigned C{True}.
        @type prohibited: C{bool}

        @raise pyxb.BadTypeValueError: the L{unicode_default} cannot be used
        to initialize an instance of L{data_type}
        """
        
        self.__name = name
        self.__id = id
        self.__key = key
        self.__dataType = data_type
        self.__unicodeDefault = unicode_default
        if self.__unicodeDefault is not None:
            self.__defaultValue = self.__dataType.Factory(self.__unicodeDefault)
        self.__fixed = fixed
        self.__required = required
        self.__prohibited = prohibited

    def name (self):
        """The expanded name of the element.

        @rtype: L{pyxb.namespace.ExpandedName}
        """
        return self.__name
    
    def defaultValue (self):
        """The default value of the attribute."""
        return self.__defaultValue

    def fixed (self):
        """C{True} iff the value of the attribute cannot be changed."""
        return self.__fixed

    def required (self):
        """Return True iff the attribute must be assigned a value."""
        return self.__required

    def prohibited (self):
        """Return True iff the attribute must not be assigned a value."""
        return self.__prohibited

    def provided (self, ctd_instance):
        """Return True iff the given instance has been explicitly given a
        value for the attribute.

        This is used for things like only generating an XML attribute
        assignment when a value was originally given (even if that value
        happens to be the default).
        """
        return self.__getProvided(ctd_instance)

    def id (self):
        """Tag used within Python code for the attribute.

        This is not used directly in the default code generation template."""
        return self.__id

    def key (self):
        """String used as key within object dictionary when storing attribute value."""
        return self.__key

    def dataType (self):
        """The subclass of L{pyxb.binding.basis.simpleTypeDefinition} of which any attribute value must be an instance."""
        return self.__dataType

    def __getValue (self, ctd_instance):
        """Retrieve the value information for this attribute in a binding instance.

        @param ctd_instance: The instance object from which the attribute is to be retrieved.
        @type ctd_instance: subclass of L{pyxb.binding.basis.complexTypeDefinition}
        @return: C{(provided, value)} where C{provided} is a C{bool} and
        C{value} is C{None} or an instance of the attribute's datatype.

        """
        return getattr(ctd_instance, self.__key, (False, None))

    def __getProvided (self, ctd_instance):
        return self.__getValue(ctd_instance)[0]

    def value (self, ctd_instance):
        """Get the value of the attribute from the instance."""
        return self.__getValue(ctd_instance)[1]

    def __setValue (self, ctd_instance, new_value, provided):
        return setattr(ctd_instance, self.__key, (provided, new_value))

    def reset (self, ctd_instance):
        """Set the value of the attribute in the given instance to be its
        default value, and mark that it has not been provided."""
        self.__setValue(ctd_instance, self.__defaultValue, False)

    def addDOMAttribute (self, dom_support, ctd_instance, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        ( provided, value ) = self.__getValue(ctd_instance)
        if provided:
            assert value is not None
            dom_support.addAttribute(element, self.__name, value.xsdLiteral())
        return self

    def validate (self, ctd_instance):
        (provided, value) = self.__getValue(ctd_instance)
        if value is not None:
            if self.__prohibited:
                raise pyxb.ProhibitedAttributeError('Value given for prohibited attribute %s' % (self.__name,))
            if self.__required and not provided:
                assert self.__fixed
                raise pyxb.MissingAttributeError('Fixed required attribute %s was never set' % (self.__name,))
            if not self.__dataType._IsValidValue(value):
                raise pyxb.BindingValidationError('Attribute %s value type %s not %s' % (self.__name, type(value), self.__dataType))
            self.__dataType.XsdConstraintsOK(value)
        else:
            if self.__required:
                raise pyxb.MissingAttributeError('Required attribute %s does not have a value' % (self.__name,))
        return True

    def set (self, ctd_instance, new_value):
        """Set the value of the attribute.

        This validates the value against the data type, creating a new instance if necessary.

        @param ctd_instance: The binding instance for which the attribute
        value is to be set
        @type ctd_instance: subclass of L{pyxb.binding.basis.complexTypeDefinition}
        @param new_value: The value for the attribute
        @type new_value: An C{xml.dom.Node} instance, or any value that is
        permitted as the input parameter to the C{Factory} method of the
        attribute's datatype.
        """
        provided = True
        if isinstance(new_value, xml.dom.Node):
            unicode_value = self.__name.getAttribute(new_value)
            if unicode_value is None:
                if self.__required:
                    raise pyxb.MissingAttributeError('Required attribute %s from %s not found' % (self.__name, ctd_instance._ExpandedName or type(ctd_instance)))
                provided = False
                unicode_value = self.__unicodeDefault
            if unicode_value is None:
                # Must be optional and absent
                provided = False
                new_value = None
            else:
                new_value = unicode_value
        else:
            assert new_value is not None
        if self.__prohibited:
            raise pyxb.ProhibitedAttributeError('Value given for prohibited attribute %s' % (self.__name,))
        if (new_value is not None) and (not isinstance(new_value, self.__dataType)):
            new_value = self.__dataType.Factory(new_value)
        if self.__fixed and (new_value != self.__defaultValue):
            raise pyxb.AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__name,))
        self.__setValue(ctd_instance, new_value, provided)
        return new_value

    def _description (self, name_only=False, user_documentation=True):
        if name_only:
            return str(self.__name)
        assert issubclass(self.__dataType, basis._TypeBinding_mixin)
        desc = [ str(self.__id), ': ', str(self.__name), ' (', self.__dataType._description(name_only=True, user_documentation=False), '), ' ]
        if self.__required:
            desc.append('required')
        elif self.__prohibited:
            desc.append('prohibited')
        else:
            desc.append('optional')
        if self.__defaultValue is not None:
            desc.append(', ')
            if self.__fixed:
                desc.append('fixed')
            else:
                desc.append('default')
            desc.extend(['=', self.__unicodeDefault ])
        return ''.join(desc)

class ElementUse (pyxb.cscRoot):
    """Aggregate the information relevant to an element of a complex type.

    This includes the L{original tag name<name>}, the spelling of L{the
    corresponding object in Python <id>}, an L{indicator<isPlural>} of whether
    multiple instances might be associated with the field, and other relevant
    information..
    """

    def name (self):
        """The expanded name of the element.

        @rtype: L{pyxb.namespace.ExpandedName}
        """
        return self.__name
    __name = None

    def id (self):
        """The string name of the binding class field used to hold the element
        values.

        This is the user-visible name, and excepting disambiguation will be
        equal to the local name of the element."""
        return self.__id
    __id = None

    # The dictionary key used to identify the value of the element.  The value
    # is the same as that used for private member variables in the binding
    # class within which the element declaration occurred.
    __key = None

    def elementBinding (self):
        """The L{basis.element} instance identifying the information
        associated with the element declaration.
        """
        return self.__elementBinding
    def _setElementBinding (self, element_binding):
        # Set the element binding for this use.  Only visible at all because
        # we have to define the uses before the element instances have been
        # created.
        self.__elementBinding = element_binding
        return self
    __elementBinding = None

    def isPlural (self):
        """True iff the content model indicates that more than one element
        can legitimately belong to this use.

        This includes elements in particles with maxOccurs greater than one,
        and when multiple elements with the same NCName are declared in the
        same type.
        """
        return self.__isPlural
    __isPlural = False

    def __init__ (self, name, id, key, is_plural, element_binding=None):
        """Create an ElementUse instance.

        @param name: The name by which the element is referenced in the XML
        @type name: L{pyxb.namespace.ExpandedName}

        @param id: The Python name for the element within the containing
        L{pyxb.basis.binding.complexTypeDefinition}.  This is a public
        identifier, albeit modified to be unique, and is usually used as the
        name of the element's inspector method or property.
        @type id: C{str}

        @param key: The string used to store the element
        value in the dictionary of the containing
        L{pyxb.basis.binding.complexTypeDefinition}.  This is mangled so
        that it is unique among and is treated as a Python private member.
        @type key: C{str}

        @param is_plural: If C{True}, documents for the corresponding type may
        have multiple instances of this element.  As a consequence, the value
        of the element will be a list.  If C{False}, the value will be C{None}
        if the element is absent, and a reference to an instance of the type
        identified by L{pyxb.binding.basis.element.typeDefinition} if present.
        @type is_plural: C{bool}

        @param element_binding: Reference to the class that serves as the
        binding for the element.
        """
        self.__name = name
        self.__id = id
        self.__key = key
        self.__isPlural = is_plural
        self.__elementBinding = element_binding

    def defaultValue (self):
        """Return the default value for this element.

        @todo: Right now, this returns C{None} for non-plural and an empty
        list for plural elements.  Need to support schema-specified default
        values for simple-type content.
        """
        if self.isPlural():
            return []
        return None

    def value (self, ctd_instance):
        """Return the value for this use within the given instance."""
        return getattr(ctd_instance, self.__key, self.defaultValue())

    def reset (self, ctd_instance):
        """Set the value for this use in the given element to its default."""
        setattr(ctd_instance, self.__key, self.defaultValue())
        return self

    def set (self, ctd_instance, value):
        """Set the value of this element in the given instance."""
        if value is None:
            return self.reset(ctd_instance)
        assert self.__elementBinding is not None
        if basis._TypeBinding_mixin._PerformValidation:
            value = self.__elementBinding.compatibleValue(value, is_plural=self.isPlural())
        setattr(ctd_instance, self.__key, value)
        ctd_instance._addContent(value, self.__elementBinding)
        return self

    def setOrAppend (self, ctd_instance, value):
        """Invoke either L{set} or L{append}, depending on whether the element
        use is plural."""
        if self.isPlural():
            return self.append(ctd_instance, value)
        return self.set(ctd_instance, value)

    def append (self, ctd_instance, value):
        """Add the given value as another instance of this element within the binding instance.
        @raise pyxb.StructuralBadDocumentError: invoked on an element use that is not plural
        """
        if not self.isPlural():
            raise pyxb.StructuralBadDocumentError('Cannot append to element with non-plural multiplicity')
        values = self.value(ctd_instance)
        if basis._TypeBinding_mixin._PerformValidation:
            value = self.__elementBinding.compatibleValue(value)
        values.append(value)
        ctd_instance._addContent(value, self.__elementBinding)
        return values

    def toDOM (self, dom_support, parent, value):
        """Convert the given value to DOM as an instance of this element.

        @param dom_support: Helper for managing DOM properties
        @type dom_support: L{pyxb.utils.domutils.BindingDOMSupport}
        @param parent: The DOM node within which this element should be generated.
        @type parent: C{xml.dom.Element}
        @param value: The content for this element.  May be text (if the
        element allows mixed content), or an instance of
        L{basis._TypeBinding_mixin}.
        """
        if isinstance(value, basis._TypeBinding_mixin):
            element_binding = self.__elementBinding
            if value._substitutesFor(element_binding):
                element_binding = value._element()
            assert element_binding is not None
            if element_binding.abstract():
                raise pyxb.DOMGenerationError('Element %s is abstract but content %s not associated with substitution group member' % (self.name(), value))
            element = dom_support.createChildElement(element_binding.name(), parent)
            elt_type = element_binding.typeDefinition()
            val_type = type(value)
            if isinstance(value, basis.complexTypeDefinition):
                assert isinstance(value, elt_type)
            else:
                if isinstance(value, basis.STD_union) and isinstance(value, elt_type._MemberTypes):
                    val_type = elt_type
            if dom_support.requireXSIType() or elt_type._RequireXSIType(val_type):
                val_type_qname = value._ExpandedName.localName()
                tns_prefix = dom_support.namespacePrefix(value._ExpandedName.namespace())
                if tns_prefix is not None:
                    val_type_qname = '%s:%s' % (tns_prefix, val_type_qname)
                dom_support.addAttribute(element, pyxb.namespace.XMLSchema_instance.createExpandedName('type'), val_type_qname)
            value._toDOM_csc(dom_support, element)
        elif isinstance(value, (str, unicode)):
            element = dom_support.createChildElement(self.name(), parent)
            element.appendChild(dom_support.document().createTextNode(value))
        else:
            raise pyxb.LogicError('toDOM with unrecognized value type %s: %s' % (type(value), value))

    def _description (self, name_only=False, user_documentation=True):
        if name_only:
            return str(self.__name)
        desc = [ str(self.__id), ': ']
        if self.isPlural():
            desc.append('MULTIPLE ')
        desc.append(self.elementBinding()._description(user_documentation=user_documentation))
        return ''.join(desc)

class _DFAState (object):
    """Base class for a suspended DFA interpretation."""
    __contentModel = None
    __state = None

    def __init__ (self, content_model, state=1):
        self.__contentModel = content_model
        self.__state = state

    def state (self):
        """The current state of the automaton, represented as an integer."""
        return self.__state
    def contentModel (self):
        """The L{ContentModel} to which the state belongs."""
        return self.__contentModel
    def updateState (self, state):
        """Change the automaton state recorded in this DFA state."""
        self.__state = state
        return self

    def step (self, dfa_stack, ctd_instance, value, element_use):
        """Execute a step within the content model.

        This determines whether the current state in the content model allows
        a transition on the given value.  If a transition can be performed,
        the instance element use corresponding to the value is used to record
        the value.

        The input value should be an instance of L{basis._TypeBinding_mixin},
        or a value that can be uniquely converted into such a instance using
        the transitions from the current state as clues.

        @param dfa_stack: The current state of the parse.  Upon return, this may have been augmented with suspended content models.
        @type dfa_stack: L{DFAStack}
        @param value: A value upon which transition should occur.
        @type value: C{xml.dom.Node} or L{basis._TypeBinding_mixin} or other value
        @return: C{True} iff a transition successfully consumed the value
        """

        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        self.__state = self.contentModel().step(ctd_instance, self.state(), value, element_use, dfa_stack)
        return self.__state is not None

    def isFinal (self):
        """Return C{True} iff the current state of the content model is a final state."""
        return self.contentModel().isFinal(self.state())

class _MGAllState (object):
    """The state of a suspended interpretation of a L{ModelGroupAll}
    transition.  This state comprises a set of alternatives, and optionally a
    L{DFAStack} corresponding to the current position within one of the
    alternatives.
    """

    __modelGroup = None
    __alternatives = None
    __currentStack = None
    __isFinal = None
    
    def __init__ (self, model_group):
        self.__modelGroup = model_group
        self.__alternatives = self.__modelGroup.alternatives()

    def step (self, dfa_stack, ctd_instance, value, element_use):
        """Execute a step within the model group.

        If an automaton stack is currently being executed, the step defers to
        that automaton.  If a step is succesfully taken, the invocation
        returns; otherwise, the automaton stack is discarded.

        If no automaton stack is active, a step is attempted on each automaton
        remaining in the alternatives.  If the step is successful, that
        automaton is recorded as being the current one for execution, and the
        invocation returns.

        If no automaton can be found within which progress can be made, the
        step fails.

        @param dfa_stack: The current state of the parse.  Upon return, this
        may have been augmented with suspended content models.
        @type dfa_stack: L{DFAStack}
        @param value: A value upon which transition should occur.
        @type value: C{xml.dom.Node} or L{basis._TypeBinding_mixin} or other value
        @return: C{True} iff a transition was found that consumed the value.
        """

        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        if self.__currentStack is not None:
            if self.__currentStack.step(ctd_instance, value, element_use):
                return True
            if not self.__currentStack.isTerminal():
                # I think this is probably a problem, but don't have an
                # example yet to use to analyze it.  The issue is that we've
                # already committed to executing the automaton; if we end up
                # in a non-final state, then that execution failed, and
                # probably the whole validation should just abort.
                print '******** Non-terminal state reached in all group parsing; please contact support'
            self.__currentStack = None
        found_match = True
        for alt in self.__alternatives:
            try:
                new_stack = alt.contentModel().initialDFAStack()
                if new_stack.step(ctd_instance, value, element_use):
                    self.__currentStack = new_stack
                    self.__alternatives.remove(alt)
                    return True
            except pyxb.BadDocumentError, e:
                #print 'Failed with alternative %s: %s' % (alt, type(e))
                pass
        return False

    def isFinal (self):
        """Return C{True} iff no required alternatives remain."""
        for alt in self.__alternatives:
            # Any required alternative that must consume a symbol prevents
            # this from being an acceptable final state for the model group.
            if alt.required() and not alt.contentModel().allowsEpsilonTransitionToFinal():
                #print "\n\n***Required alternative %s still present\n\n" % (alt,)
                return False
        return True

class DFAStack (object):
    """A stack of states and content models representing the current status of
    an interpretation of a content model, including invocations of nested
    content models reached through L{ModelGroupAll} instances."""

    __stack = None
    def __init__ (self, content_model):
        self.__stack = []
        self.pushModelState(_DFAState(content_model))

    def pushModelState (self, model_state):
        """Add the given model state as the new top (actively executing) model ."""
        self.__stack.append(model_state)
        return model_state

    def isTerminal (self):
        """Return C{True} iff the stack is in a state where the top-level
        model execution has reached a final state."""
        return (0 == len(self.__stack)) or self.topModelState().isFinal()

    def popModelState (self):
        """Remove and return the model state currently being executed."""
        if 0 == len(self.__stack):
            raise pyxb.LogicError('Attempt to underflow content model stack')
        return self.__stack.pop()

    def topModelState (self):
        """Return a reference to the model state currently being executed.

        The state is not removed from the stack."""
        if 0 == len(self.__stack):
            raise pyxb.LogicError('Attempt to underflow content model stack')
        return self.__stack[-1]

    def step (self, ctd_instance, value, element_use):
        """Take a step using the value and the current model state.

        Execution of the step may add a new model state to the stack.

        @return: C{True} iff the value was consumed by a transition."""
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        if 0 == len(self.__stack):
            return False
        ok = self.topModelState().step(self, ctd_instance, value, element_use)
        if not ok:
            self.popModelState()
        return ok

class ContentModelTransition (pyxb.cscRoot):
    """Represents a transition in the content model DFA.

    If the next object in the DOM model conforms to the specified term, it is
    consumed and the specified next state is entered."""

    def term (self):
        """The matching term for this transition to succeed."""
        if self.__term is None:
            self.__term = self.__elementUse.elementBinding()
            assert self.__term is not None
        return self.__term
    __term = None

    def currentStateRef (self):
        return self.__currentStateRef
    __currentStateRef = None
    def _currentStateRef (self, current_state_ref):
        self.__currentStateRef = current_state_ref

    def nextState (self):
        """The next state in the DFA"""
        return self.__nextState
    __nextState = None

    # The ElementUse instance used to store a successful match in the
    # complex type definition instance.
    def elementUse (self):
        return self.__elementUse
    __elementUse = None

    # Types of transition that can be taken, in order of preferred match
    TT_element = 0x01           #<<< The transition is on an element
    TT_modelGroupAll = 0x02     #<<< The transition is on an ALL model group
    TT_wildcard = 0x03          #<<< The transition is on a wildcard

    # What type of term this transition covers
    __termType = None
    def termType (self):
        return self.__termType

    def __init__ (self, next_state, element_use=None, term=None):
        """Create a transition to a new state upon receipt of a term,
        storing the successful match using the provided ElementUse."""
        self.__nextState = next_state
        assert self.__nextState is not None
        self.__elementUse = element_use
        if self.__elementUse is not None:
            self.__term = None
            self.__termType = self.TT_element
        else:
            self.__term = term
            assert self.__term is not None
            if isinstance(self.__term, ModelGroupAll):            
                self.__termType = self.TT_modelGroupAll
            elif isinstance(self.__term, Wildcard):
                self.__termType = self.TT_wildcard
            else:
                raise pyxb.LogicError('Unexpected transition term %s' % (self.__term,))

    def __cmp__ (self, other):
        """Sort transitions so elements precede model groups precede
        wildcards.  Also sort within each subsequence."""
        rv = cmp(self.__termType, other.__termType)
        if 0 == rv:
            # In a vain attempt at determinism, sort the element transitions
            # by name
            if (self.TT_element == self.__termType):
                rv = cmp(self.__elementUse.name(), other.__elementUse.name())
            else:
                rv = cmp(self.__term, other.__term)
        return rv

    def __processElementTransition (self, value, element_use):
        # First, identify the element
        if isinstance(value, xml.dom.Node):
            # If we got here, it's because we couldn't figure out what element
            # the node conformed to and had to try the element transitions in
            # hopes of matching a wildcard.  If we couldn't find an element
            # before, we can't do it now, so just fail.
            return None
        try:
            # The _convert_string_values=False setting prevents string
            # arguments to element/type constructors from being automatically
            # converted to another type (like int) if they just happen to be
            # convertible.  Without this, it's too easy to accept a
            # sub-optimal transition (e.g., match a float when an alternative
            # string is available).
            return self.term().compatibleValue(value, _convert_string_values=False)
        except pyxb.BadTypeValueError, e:
            # Silently fail the transition
            pass
        return None

    def __validateConsume (self, key, available_symbols_im, output_sequence_im, candidates):
        # Update candidates to incorporate the path abstraction associated
        # with the element that is this term.

        # Create a mutable copy of the available symbols
        next_symbols = available_symbols_im.copy()

        # If the transition is a loop back to the current state, or if the
        # transition is a simple type definition with variety list, we can
        # consume multiple instances.  Might as well consume all of them.
        # When we do consume, we can do either one transition, or one
        # transition for each element in a list/vector.
        key_type = type(None)
        elt_plural = False
        if key is not None:
            key_type = key.elementBinding().typeDefinition()
            elt_plural = key.isPlural()
        multiple_values = False
        try:
            iter(next_symbols[key][0])
            multiple_values = True
        except TypeError:
            pass

        if (self.__nextState == self.__currentStateRef.state()):
            consume_all = True
            consume_singles = True
        else:
            consume_all = False
            consume_singles = True
        if consume_all:
            consumed = next_symbols[key]
            del next_symbols[key]
        else:
            # Make sure we pop from a copy of the available_symbols_im entry value.
            next_left = next_symbols[key][:]
            consumed = [ next_left.pop(0) ]
            if 0 == len(next_left):
                del next_symbols[key]
            else:
                next_symbols[key] = next_left
        if consume_singles:
            output_sequence = output_sequence_im + [ (key, _c) for _c in consumed ]
        else:
            output_sequence = output_sequence_im + [ (key, key_type(consumed)) ]
        assert (not (key in next_symbols)) or (0 < len(next_symbols[key]))
        candidate = (self.__nextState, next_symbols, output_sequence)
        candidates.append(candidate)
        return True

    def validate (self, available_symbols_im, output_sequence_im, candidates):
        """Determine whether it is possible to take this transition using the
        available symbols.

        @param available_symbols_im: As with L{ContentModel.validate}.  The
        map will not be modified by this method.
        
        @param output_sequence_im: As with the return value of
        L{ContentModel.validate}.  The sequence will not be modified by this
        event (it is used as a prefix for new candidates).

        @param candidates: A list of candidate validation paths.

        @return: C{True} iff the transition could be made."""
        if self.TT_element == self.__termType:
            if not (self.__elementUse in available_symbols_im):
                # No symbol available for this transition
                return False
            assert 0 < len(available_symbols_im[self.__elementUse])
            return self.__validateConsume(self.__elementUse, available_symbols_im, output_sequence_im, candidates)
        elif self.TT_modelGroupAll == self.__termType:
            return self.term().validate(available_symbols_im, output_sequence_im, self.__nextState, candidates)
        elif self.TT_wildcard == self.__termType:
            if not (None in available_symbols_im):
                return False
            assert 0 < len(available_symbols_im[None])
            return self.__validateConsume(None, available_symbols_im, output_sequence_im, candidates)
        return False

    def allowsEpsilonTransition (self):
        """Determine whether it is possible to take this transition without
        consuming any symbols.

        This is only possible if this is a transition to a final state using
        an "all" model group for which every alternative is effectively
        optional.
        """
        if self.TT_modelGroupAll != self.__termType:
            return False
        dfa_state = _MGAllState(self.__term)
        return dfa_state.isFinal()

    def attemptTransition (self, ctd_instance, value, element_use, dfa_stack):
        """Attempt to make the appropriate transition.

        @param ctd_instance: The binding instance for which we are attempting
        to set values by walking the content model.
        @type ctd_instance: L{basis.complexTypeDefinition}

        @param value: The potential value that would be consumed if this
        transition can be made.
        @type value: C{xml.dom.Node} or L{basis._TypeBinding_mixin}

        @param dfa_stack: The current state of processing this and enclosing
        content models.
        @type dfa_stack: L{DFAStack}

        @return: C{True} iff C{value} is acceptable for this transition

        """

        if self.TT_element == self.__termType:
            element = None
            # If the element use matched one of the terms in its state, we
            # would never have gotten here, so don't even try.  We're only
            # walking the terms to see if an ALL or Wildcard is allowed.
            if (element_use is not None):
                return None
            element = self.__processElementTransition(value, element_use)
            if element is None:
                return False
            self.__elementUse.setOrAppend(ctd_instance, element)
            return True
        if self.TT_modelGroupAll == self.__termType:
            return dfa_stack.pushModelState(_MGAllState(self.__term)).step(dfa_stack, ctd_instance, value, element_use)
        if self.TT_wildcard == self.__termType:
            value_desc = 'value of type %s' % (type(value),)
            if isinstance(value, xml.dom.Node):
                value_desc = 'DOM node %s' % (pyxb.namespace.ExpandedName(value),)
            elif not isinstance(value, basis._TypeBinding_mixin):
                return False
            if not self.__term.matches(ctd_instance, value):
                raise pyxb.UnexpectedContentError(value)
            if not isinstance(value, basis._TypeBinding_mixin):
                print 'NOTE: Created unbound wildcard element from %s' % (value_desc,)
            assert isinstance(ctd_instance.wildcardElements(), list), 'Uninitialized wildcard list in %s' % (ctd_instance._ExpandedName,)
            ctd_instance._appendWildcardElement(value)
            return True
        raise pyxb.LogicError('Unexpected transition term %s' % (self.__term,))

class ContentModelState (pyxb.cscRoot):
    """Represents a state in a ContentModel DFA.

    The state identifier is an integer.  State 1 is the starting state of the
    DFA.  A flag indicates whether the state is a legitimate final state for
    the DFA.  The transitions are an ordered sequence of
    ContentModelTransition instances."""

    # Integer
    __state = None
    # Sequence of ContentModelTransition instances
    __transitions = None
    
    # Map from ElementUse instances to the term that transitions on that use.
    __elementTermMap = None

    def isFinal (self):
        """If True, this state can successfully complete the element
        reduction."""
        return self.__isFinal
    __isFinal = None

    def state (self):
        return self.__state

    def __init__ (self, state, is_final, transitions):
        self.__state = state
        self.__isFinal = is_final
        self.__transitions = transitions
        [ _t._currentStateRef(self) for _t in self.__transitions ]
        self.__transitions.sort()
        self.__elementTermMap = { }
        for t in self.__transitions:
            if t.TT_element == t.termType():
                assert t.elementUse() is not None
                self.__elementTermMap[t.elementUse()] = t

    def transitions (self):
        return self.__transitions
    
    def allowsEpsilonTransitionToFinal (self, content_model):
        """Determine can reach a final state in the content model without
        consuming anything."""
        if self.isFinal():
            return True
        for transition in self.__transitions:
            if transition.allowsEpsilonTransition() and content_model.isFinal(transition.nextState()):
                return True
        return False

    def evaluateContent (self, ctd_instance, value, element_use, dfa_stack):
        """Try to make a single transition with the given value.

        @param ctd_instance: The binding instance for which we are attempting
        to set values by walking the content model.
        @type ctd_instance: L{basis.complexTypeDefinition}

        @param value: The value that would be consumed if a transition can be
        made.
        @type value: C{xml.dom.Node} or L{basis._TypeBinding_mixin}

        @param element_use: The L{ElementUse<pyxb.binding.content.ElementUse>}
        corresponding to the provided value, if known (for example, because
        the value was parsed from an XML document).

        @param dfa_stack: The current state of processing this and enclosing
        content models.
        @type dfa_stack: L{DFAStack}

        @return: If a transition could be taken, the next state in the content
        model.  C{None} if no transition could be taken and this state is
        final.

        @raise pyxb.UnrecognizedContentError: No transition on C{value} is
        possible, and this is not a final state.
        """

        if element_use is not None:
            transition = self.__elementTermMap.get(element_use)
            if transition is not None:
                element_use.setOrAppend(ctd_instance, value)
                return transition.nextState()
            # Might get here legitimately if we need to descend into ALL, or
            # if this value is a wildcard for which we happen to have a
            # binding class available.
        for transition in self.__transitions:
            if transition.attemptTransition(ctd_instance, value, element_use, dfa_stack):
                return transition.nextState()
        if self.isFinal():
            return None
        raise pyxb.UnrecognizedContentError(value, element_use=element_use)

class ContentModel (pyxb.cscRoot):
    """The ContentModel is a deterministic finite state automaton which can be
    traversed using a sequence of DOM nodes which are matched on transitions
    against the legal content model of a complex type."""

    # Map from integers to ContentModelState instances
    __stateMap = None

    # All DFAs begin at this state
    __InitialState = 1

    def __init__ (self, state_map=None):
        self.__stateMap = state_map

    def initialDFAStack (self):
        return DFAStack(self)

    def step (self, ctd_instance, state, value, element_use, dfa_stack):
        """Perform a single step in the content model.  This is a pass-through
        to L{ContentModelState.evaluateContent} for the appropriate state.

        @param state: The starting state in this content model.
        @type state: C{int}
        """

        return self.__stateMap[state].evaluateContent(ctd_instance, value, element_use, dfa_stack)

    def isFinal (self, state):
        return self.__stateMap[state].allowsEpsilonTransitionToFinal(self)

    def allowsEpsilonTransitionToFinal (self):
        return self.__stateMap[self.__InitialState].allowsEpsilonTransitionToFinal(self)

    def validate (self, available_symbols, succeed_at_dead_end=False):
        """Determine whether this content model can be satisfied using the
        provided elements.

        The general idea is to treat the transitions of the DFA as symbols in
        an alphabet.  For each such transition, a sequence of values is
        provided to be associated with the transition.  One transition is
        permitted for each value associated with the symbol.  The symbol (key)
        C{None} represents wildcard values.

        If a path is found that uses every symbol in valid transitions and
        ends in a final state, the return value is a pair consisting of the
        unconsumed symbols and a sequence of term, value pairs that define the
        acceptable path.  If no valid path through the DFA can be taken,
        C{None} is returned.
        
        @param available_symbols: A map from leaf DFA terms to a sequence of
        values associated with the term in a binding instance.  The key
        C{None} is used to represent wildcard elements.  If a key appears in
        this map, it must have at least one value in its sequence.

        @param succeed_at_dead_end: If C{True}, states from which no
        transition can be made are accepted as final states.  This is used
        when processing "all" model groups, where the content model for the
        current alternative must succeed while retaining the symbols that are
        needed for other alternatives.
        """

        candidates = []
        candidates.append( (1, available_symbols, []) )
        while 0 < len(candidates):
            (state_id, symbols, sequence) = candidates.pop(0)
            state = self.__stateMap[state_id]
            if 0 == len(symbols):
                # No symbols available for transitions in this state.  If this
                # places us in a final state, we've got a successful path and
                # should return it.  Otherwise, this path failed, and we go on
                # to the next candidate.
                if state.allowsEpsilonTransitionToFinal(self):
                    return (symbols, sequence)
                continue
            # Collect all the alternatives that are possible by taking
            # transitions from this state.
            num_transitions = 0
            for transition in state.transitions():
                num_transitions += transition.validate(symbols, sequence, candidates)
            if (0 == num_transitions) and succeed_at_dead_end:
                return (symbols, sequence)
        return None

class ModelGroupAllAlternative (pyxb.cscRoot):
    """Represents a single alternative in an "all" model group."""

    def contentModel (self):
        """The content model definition for the alternative."""
        return self.__contentModel
    __contentModel = None

    def required (self):
        """True iff this alternative must be present (min_occurs=1)"""
        return self.__required
    __required = None

    def __init__ (self, content_model, required):
        #print '%s created MGA alternative model %s required %s' % (self, content_model, required)
        self.__contentModel = content_model
        self.__required = required


class ModelGroupAll (pyxb.cscRoot):
    """Content model class that represents a ModelGroup with an "all"
    compositor."""

    __alternatives = None
    def alternatives (self):
        return set(self.__alternatives)

    def __init__ (self, alternatives):
        self.__alternatives = alternatives

    def validate (self, available_symbols_im, output_sequence_im, next_state, candidates):
        num_matches = 0
        alternatives = set(self.__alternatives)
        symbols = available_symbols_im
        output_sequence = output_sequence_im[:]
        found_match = True
        while (0 < len(alternatives)) and found_match:
            found_match = False
            for alt in alternatives:
                path = alt.contentModel().validate(symbols, succeed_at_dead_end=True)
                if path is None:
                    break
                (new_symbols, new_sequence) = path
                found_match = (0 < len(new_sequence))
                if found_match:
                    output_sequence.extend(new_sequence)
                    symbols = new_symbols
                    alternatives.remove(alt)
                    found_match = True
                    break
        for alt in alternatives:
            if alt.required():
                return False
        candidates.append( (next_state, symbols, output_sequence) )
        return True

class Wildcard (pyxb.cscRoot):
    """Placeholder for wildcard objects."""

    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace'
    NC_local = '##local'

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:

         - L{Wildcard.NC_any}
         - A tuple ( L{Wildcard.NC_not}, a L{namespace<pyxb.namespace.Namespace>} instance )
         - set(of L{namespace<pyxb.namespace.Namespace>} instances)

        Namespaces are represented by their URIs.  Absence is
        represented by None, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    PC_skip = 'skip'            #<<< No constraint is applied
    PC_lax = 'lax'              #<<< Validate against available uniquely determined declaration
    PC_strict = 'strict'        #<<< Validate against declaration or xsi:type which must be available

    # One of PC_*
    __processContents = None
    def processContents (self): return self.__processContents

    def __init__ (self, *args, **kw):
        # Namespace constraint and process contents are required parameters.
        self.__namespaceConstraint = kw['namespace_constraint']
        self.__processContents = kw['process_contents']

    def matches (self, ctd_instance, value):
        """Return True iff the value is a valid match against this wildcard.

        Not implemented yet: all wildcards are assumed to match all values.

        """
        # @todo check node against namespace constraint and process contents
        #print 'WARNING: Accepting node as wildcard match without validating.'
        return True

## Local Variables:
## fill-column:78
## End:
    
