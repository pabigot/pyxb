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

class ContentStatePushed (Exception):
    """Raised to avoid loops in content steps."""
    pass

class ContentState_mixin (pyxb.cscRoot):
    def model (self): return self.__model
    
    def __init__ (self, model, **kw):
        self.__model = model
        super(ContentState_mixin, self).__init__(**kw)
        
    def accepts (self, state_stack, ctd, value, element_use):
        """Test whether the given value/element_use passes the state checks.

        Return C{True} if the value is valid within the state at the top of
        the stack.  In this situation, the value is stored into its
        appropriate element.

        Return C{False} if the value does not satisfy the requirements of the
        top of the state stack.

        Raises L{ContentStatePushed} if the top of the stack is a group model
        for which validation requires a new state be created."""
        raise Exception('ContentState_mixin.accepts not implemented in %s' % (type(self),))

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

class ElementUse (ContentState_mixin):
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

    def accepts (self, state_stack, ctd, value, element_use):
        if element_use == self:
            self.setOrAppend(ctd, value)
            return True
        if element_use is not None:
            print 'WARNING: Non-null EU does not match'
            return False
        assert not isinstance(value, xml.dom.Node)
        try:
            self.setOrAppend(ctd, self.__elementBinding.compatibleValue(value, _convert_string_values=False))
            return True
        except pyxb.BadTypeValueError, e:
            pass
        #print '%s %s %s in %s' % (ctd, value, element_use, self)
        return False

    def _validate (self, symbol_set, output_sequence):
        values = symbol_set.get(self)
        #print 'values %s' % (values,)
        if values is None:
            return False
        used = values.pop(0)
        output_sequence.append( (self, used) )
        if 0 == len(values):
            del symbol_set[self]
        return True

    def __str__ (self):
        return 'EU.%s@%x' % (self.__name, id(self))

class StateStack (object):
    """A stack of states and content models representing the current status of
    an interpretation of a content model, including invocations of nested
    content models reached through L{ModelGroupAll} instances."""

    __stack = None
    def __init__ (self, content_model):
        self.__stack = []
        try:
            self.pushModelState(ParticleState(content_model))
        except ContentStatePushed:
            pass

    def pushModelState (self, model_state):
        """Add the given model state as the new top (actively executing) model ."""
        #print 'SS Push %s' % (model_state,)
        self.__stack.append(model_state)
        raise ContentStatePushed()

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

        Execution of the step may add a new model state to the stack.  When
        this happens, the state that caused a new state to be pushed raises
        L{ContentStatePushed} to return control to this activation record, so we can
        detect loops.

        @return: C{True} iff the value was consumed by a transition."""
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        #print 'SS ENTRY'
        entry_top = self.topModelState()
        have_tried = False
        while 0 < len(self.__stack):
            top = self.topModelState()

            # Stop with a failure if we're looping
            if (top == entry_top) and have_tried:
                return False
            have_tried = True
            #print 'SSTop %s of %d on %s %s' % (top, len(self.__stack), value, element_use)
            try:
                ok = top.accepts(self, ctd_instance, value, element_use)
            except ContentStatePushed:
                #print 'ContentStatePushed'
                continue
            have_looped = True
            if ok:
                #print 'SS CONT %s' % (top,)
                return ok
            state = self.popModelState()
            #print 'SS Pop %s %s' % (state, state.model())
            #print '  Started %s %s' % (top, top.model())
            #top = self.topModelState();
            #print '  Now %s %s' % (top, top.model())
        #print 'SS FALLOFF'
        return False

class ParticleState (ContentState_mixin):
    def __init__ (self, particle, **kw):
        self.__particle = particle
        self.__count = 0
        super(ParticleState, self).__init__(particle, **kw)

    def accepts (self, state_stack, ctd, value, element_use):
        match = self.__particle.term().accepts(state_stack, ctd, value, element_use)
        #print 'CHECK %s %s on %s for %s' % (self, match, value, element_use)
        if match:
            self.__count += 1
            if self.__particle.isOverLimit(self.__count):
                raise pyxb.UnrecognizedContentError(value)
        return match

    def __str__ (self):
        particle = self.__particle
        return 'ParticleState(%d:%d,%s:%s)@%x' % (self.__count, particle.minOccurs(), particle.maxOccurs(), particle.term(), id(self))

class _GroupState (ContentState_mixin):
    def __init__ (self, group, **kw):
        self.__group = group
        super(_GroupState, self).__init__(group, **kw)

    def group (self): return self.__group

class SequenceState (_GroupState):
    def __init__ (self, *args, **kw):
        super(SequenceState, self).__init__(*args, **kw)
        self.__particles = self.group().particles()
        self.__particleIndex = 0

    def accepts (self, state_stack, ctd, value, element_use):
        if self.__particleIndex >= len(self.__particles):
            return False
        particle = self.__particles[self.__particleIndex]
        #print '%s push for %s' % (self, particle)
        self.__particleIndex += 1
        state_stack.pushModelState(ParticleState(particle))
        #NOTREACHED

    def __str__ (self):
        return 'SequenceState(%d/%d)@%x' % (self.__particleIndex, len(self.__particles), id(self))

class ParticleModel (pyxb.cscRoot):
    def minOccurs (self): return self.__minOccurs
    def maxOccurs (self): return self.__maxOccurs
    def term (self): return self.__term

    def isOverLimit (self, count):
        return (self.__maxOccurs is not None) and (count > self.__maxOccurs)

    def __init__ (self, term, min_occurs=1, max_occurs=1):
        self.__term = term
        self.__minOccurs = min_occurs
        self.__maxOccurs = max_occurs

    def stateStack (self):
        return StateStack(self)

    def validate (self, symbol_set):
        output_sequence = []
        #print 'Start: %d %s %s : %s' % (self.__minOccurs, self.__maxOccurs, self.__term, symbol_set)
        result = self._validate(symbol_set, output_sequence)
        #print 'End: %s %s %s' % (result, symbol_set, output_sequence)
        if result:
            return (symbol_set, output_sequence)
        return None

    def _validate (self, symbol_set, output_sequence):
        count = 0
        #print 'Validate %d %s PRT %s' % (self.__minOccurs, self.__maxOccurs, self.__term)
        last_size = len(output_sequence)
        while (not self.isOverLimit(count)) and self.__term._validate(symbol_set, output_sequence):
            #print 'PRT validated, cnt %d, left %s' % (count, symbol_set)
            this_size = len(output_sequence)
            if this_size == last_size:
                # Validated without consuming anithing
                if count < self.__minOccurs:
                    count = self.__minOccurs
                break
            count += 1
            last_size = this_size
        result = (count >= self.__minOccurs) and not self.isOverLimit(count)
        #print 'END PRT %s validate %s: %s %s %s' % (self.__term, result, self.__minOccurs, count, self.__maxOccurs)
        return result

class _Group (ContentState_mixin):
    def particles (self): return self.__particles

    def __init__ (self, *particles):
        self.__particles = particles

class GroupChoice (_Group):
    def __init__ (self, *args, **kw):
        super(GroupChoice, self).__init__(*args, **kw)

class GroupAll (_Group):
    def __init__ (self, *args, **kw):
        super(GroupAll, self).__init__(*args, **kw)

class GroupSequence (_Group):
    def __init__ (self, *args, **kw):
        super(GroupSequence, self).__init__(*args, **kw)

    def accepts (self, state_stack, ctd, value, element_use):
        if 0 == len(self.particles()):
            return False
        state_stack.pushModelState(SequenceState(self))
        #NOTREACHED

    def _validate (self, symbol_set, output_sequence):
        for p in self.particles():
            if not p._validate(symbol_set, output_sequence):
                return False
        return True

class Wildcard (ContentState_mixin):
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
        return True

    def accepts (self, state_stack, ctd, value, element_use):
        value_desc = 'value of type %s' % (type(value),)
        if not self.matches(ctd, value):
            raise pyxb.UnexpectedContentError(value)
        if not isinstance(value, basis._TypeBinding_mixin):
            print 'NOTE: Created unbound wildcard element from %s' % (value_desc,)
        assert isinstance(ctd.wildcardElements(), list), 'Uninitialized wildcard list in %s' % (ctd._ExpandedName,)
        ctd._appendWildcardElement(value)
        return True

    def _validate (self, symbol_set, output_sequence):
        # @todo check node against namespace constraint and process contents
        #print 'WARNING: Accepting node as wildcard match without validating.'
        wc_values = symbol_set.get(None)
        if wc_values is None:
            return False
        used = wc_values.pop(0)
        output_sequence.append( (None, used) )
        if 0 == len(wc_values):
            del symbol_set[None]
        return True
        
## Local Variables:
## fill-column:78
## End:
    
