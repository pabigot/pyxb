# Copyright 2009-2011, Peter A. Bigot
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



L{Wildcard} holds content-related information used in the content model.
"""

import pyxb
import pyxb.namespace
import basis

import xml.dom

class ContentState_mixin (pyxb.cscRoot):
    """Declares methods used by classes that hold state while validating a
    content model component."""

    def accepts (self, particle_state, instance, value, element_use):
        """Determine whether the provided value can be added to the instance
        without violating state validation.

        This method must not throw any non-catastrophic exceptions; general
        failures should be transformed to a C{False} return value.

        @param particle_state: The L{ParticleState} instance serving as the
        parent to this state.  The implementation must inform that state when
        the proposed value completes the content model.

        @param instance: An instance of a subclass of
        {basis.complexTypeDefinition}, into which the provided value will be
        stored if it is consistent with the current model state.

        @param value: The value that is being validated against the state.

        @param element_use: An optional L{ElementUse} instance that specifies
        the element to which the value corresponds.  This will be available
        when the value is extracted by parsing a document, but will be absent
        if the value was passed as a constructor positional parameter.

        @return: C{True} if the value was successfully matched against the
        state.  C{False} if the value did not match against the state."""
        raise Exception('ContentState_mixin.accepts not implemented in %s' % (type(self),))

    def notifyFailure (self, sub_state, particle_ok):
        """Invoked by a sub-state to indicate that validation cannot proceed
        in the current state.

        Normally this is used when an intermediate content model must reset
        itself to permit alternative models to be evaluated.

        @param sub_state: the state that was unable to accept a value

        @param particle_ok: C{True} if the particle that rejected the value is
        in an accepting terminal state

        """
        raise Exception('ContentState_mixin.notifyFailure not implemented in %s' % (type(self),))
        
    def _verifyComplete (self, parent_particle_state):
        """Determine whether the deep state is complete without further elements.

        No-op for non-aggregate state.  For aggregate state, all contained
        particles should be checked to see whether the overall model can be
        satisfied if no additional elements are provided.

        This method does not have a meaningful return value; violations of the
        content model should produce the corresponding exception (generally,
        L{MissingContentError}).

        @param parent_particle_state: the L{ParticleState} for which this state
        is the term.
        """
        pass

class ContentModel_mixin (pyxb.cscRoot):
    """Declares methods used by classes representing content model components."""

    def newState (self, parent_particle_state):
        """Return a L{ContentState_mixin} instance that will validate the
        state of this model component.

        @param parent_particle_state: The L{ParticleState} instance for which
        this instance is a term.  C{None} for the top content model of a
        complex data type.
        """
        raise Exception('ContentModel_mixin.newState not implemented in %s' % (type(self),))

    def _validateCloneSymbolSet (self, symbol_set_im):
        """Create a mutable copy of the symbol set.

        The top-level map is copied, as are the lists of values to which the
        symbols map.  The values within the lists are unchanged, as validation
        does not affect them."""
        rv = symbol_set_im.copy()
        for (k, v) in rv.items():
            rv[k] = v[:]
        return rv

    def _validateCloneOutputSequence (self, output_sequence_im):
        """Create a mutable copy of the output sequence."""
        return output_sequence_im[:]

    def _validateReplaceResults (self, symbol_set_out, symbol_set_new, output_sequence_out, output_sequence_new):
        """In-place update of symbol set and output sequence structures.

        Use this to copy from temporary mutable structures updated by local
        validation into the structures that were passed in once the validation
        has succeeded."""
        symbol_set_out.clear()
        symbol_set_out.update(symbol_set_new)
        output_sequence_out[:] = output_sequence_new

    def _validate (self, symbol_set, output_sequence):
        """Determine whether an output sequence created from the symbols can
        be made consistent with the model.

        The symbol set represents letters in an alphabet; the output sequence
        orders those letters in a way that satisfies the regular expression
        expressed in the model.  Both are changed as a result of a successful
        validation; both remain unchanged if the validation failed.  In
        recursing, implementers may assume that C{output_sequence} is
        monotonic: its length remains unchanged after an invocation iff the
        symbol set also remains unchanged.  The L{_validateCloneSymbolSet},
        L{_validateCloneOutputSequence}, and L{_validateReplaceResults}
        methods are available to help preserve this behavior.

        @param symbol_set: A map from L{ElementUse} instances to a list of
        values.  The order of the values corresponds to the order in which
        they should appear.  A key of C{None} identifies values that are
        stored as wildcard elements.  Values are removed from the lists as
        they are used; when the last value of a list is removed, its key is
        removed from the map.  Thus an empty dictionary is the indicator that
        no more symbols are available.

        @param output_sequence: A mutable list to which should be appended
        tuples C{( eu, val )} where C{eu} is an L{ElementUse} from the set of
        symbol keys, and C{val} is a value from the corresponding list.  A
        document generated by producing the elements in the given order is
        expected to validate.

        @return: C{True} iff the model validates.  C{symbol_set} and
        C{output_path} will be unchanged if this returns C{False}.
        """
        raise Exception('ContentState_mixin._validate not implemented in %s' % (type(self),))


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

    __name = None
    """ExpandedName of the attribute"""

    __id = None
    """Identifier used for this attribute within the owning class"""
    
    __key = None
    """Private Python attribute used in instances to hold the attribute value"""

    __dataType = None
    """The L{pyxb.binding.basis.simpleTypeDefinition} for values of the attribute"""

    __unicodeDefault = None
    """The default attribute value as a unicode string, or C{None}"""
     
    __defaultValue = None
    """The default value as an instance of L{__dataType}, or C{None}"""
    
    __fixed = False
    """C{True} if the attribute value cannot be changed"""
    
    __required = False
    """C{True} if the attribute must appear in every instance of the type"""
    
    __prohibited = False
    """C{True} if the attribute must not appear in any instance of the type"""

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
            self.__defaultValue = self.__dataType.Factory(self.__unicodeDefault, _from_xml=True)
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
        """C{True} iff the attribute must be assigned a value."""
        return self.__required

    def prohibited (self):
        """C{True} iff the attribute must not be assigned a value."""
        return self.__prohibited

    def provided (self, ctd_instance):
        """C{True} iff the given instance has been explicitly given a value
        for the attribute.

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
        """Validate the instance against the requirements imposed by this
        attribute use.

        There is no return value; calls raise an exception if the content does
        not validate.

        @param ctd_instance : An instance of a complex type definition.

        @raise pyxb.ProhibitedAttributeError: when instance has attribute but must not
        @raise pyxb.MissingAttributeError: when instance lacks attribute but
        must have it (including when a required fixed-value attribute is
        missing).
        @raise pyxb.BindingValidationError: when instance has attribute but its value is not acceptable
        """
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
        from_xml = False
        if isinstance(new_value, xml.dom.Node):
            from_xml = True
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
        elif new_value is None:
            if self.__required:
                raise pyxb.MissingAttributeError('Required attribute %s in %s may not be set to None' % (self.__name, ctd_instance._ExpandedName or type(ctd_instance)))
            provided = False
        if provided and self.__prohibited:
            raise pyxb.ProhibitedAttributeError('Value given for prohibited attribute %s' % (self.__name,))
        if (new_value is not None) and (not isinstance(new_value, self.__dataType)):
            new_value = self.__dataType.Factory(new_value, _from_xml=from_xml)
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

class ElementUse (ContentState_mixin, ContentModel_mixin):
    """Aggregate the information relevant to an element of a complex type.

    This includes the L{original tag name<name>}, the spelling of L{the
    corresponding object in Python <id>}, an L{indicator<isPlural>} of whether
    multiple instances might be associated with the field, and other relevant
    information.
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

    # CM.newState:ElementUse
    def newState (self, parent_particle_state):
        """Implement parent class method."""
        return self

    # CS.accepts:ElementUse
    def accepts (self, particle_state, instance, value, element_use):
        ## Implement ContentState_mixin.accepts
        rv = self._accepts(instance, value, element_use)
        if rv:
            particle_state.incrementCount()
        return rv

    def _accepts (self, instance, value, element_use):
        if element_use == self:
            self.setOrAppend(instance, value)
            return True
        if element_use is not None:
            # If there's a known element, and it's not this one, the content
            # does not match.  This assumes we handled xsi:type and
            # substitution groups earlier, which may be true.
            return False
        if isinstance(value, xml.dom.Node):
            # If we haven't been able to identify an element for this before,
            # then we don't recognize it, and will have to treat it as a
            # wildcard.
            return False
        # See if we can accept the value by converting it to something
        # compatible.
        try:
            self.setOrAppend(instance, self.__elementBinding.compatibleValue(value, _convert_string_values=False))
            return True
        except pyxb.BadTypeValueError, e:
            pass
        #print '%s %s %s in %s' % (instance, value, element_use, self)
        return False

    # CM._validate:ElementUse
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


class Wildcard (ContentState_mixin, ContentModel_mixin):
    """Placeholder for wildcard objects."""

    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace' #<<< A flag identifying the target namespace
    NC_local = '##local'        #<<< A flag indicating the namespace must be absent

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:

         - L{Wildcard.NC_any}
         - A tuple ( L{Wildcard.NC_not}, a L{namespace<pyxb.namespace.Namespace>} instance )
         - set(of L{namespace<pyxb.namespace.Namespace>} instances)

        Namespaces are represented by their URIs.  Absence is
        represented by C{None}, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    PC_skip = 'skip'
    """No namespace constraint is applied to the wildcard."""
    
    PC_lax = 'lax'
    """Validate against available uniquely determined declaration."""

    PC_strict = 'strict'
    """Validate against declaration or xsi:type, which must be available."""

    __processContents = None
    """One of L{PC_skip}, L{PC_lax}, L{PC_strict}."""
    def processContents (self):
        """Indicate how this wildcard's contents should be processed."""
        return self.__processContents

    def __normalizeNamespace (self, nsv):
        if nsv is None:
            return None
        if isinstance(nsv, basestring):
            nsv = pyxb.namespace.NamespaceForURI(nsv, create_if_missing=True)
        assert isinstance(nsv, pyxb.namespace.Namespace), 'unexpected non-namespace %s' % (nsv,)
        return nsv

    def __init__ (self, *args, **kw):
        """
        @keyword namespace_constraint: Required namespace constraint(s)
        @keyword process_contents: Required"""
        
        # Namespace constraint and process contents are required parameters.
        nsc = kw['namespace_constraint']
        if isinstance(nsc, tuple):
            nsc = (nsc[0], self.__normalizeNamespace(nsc[1]))
        elif isinstance(nsc, set):
            nsc = set([ self.__normalizeNamespace(_uri) for _uri in nsc ])
        self.__namespaceConstraint = nsc
        self.__processContents = kw['process_contents']

    def matches (self, instance, value):
        """Return True iff the value is a valid match against this wildcard.

        Validation per U{Wildcard allows Namespace Name<http://www.w3.org/TR/xmlschema-1/#cvc-wildcard-namespace>}.
        """

        ns = None
        if isinstance(value, xml.dom.Node):
            if value.namespaceURI is not None:
                ns = pyxb.namespace.NamespaceForURI(value.namespaceURI)
        elif isinstance(value, basis._TypeBinding_mixin):
            elt = value._element()
            if elt is not None:
                ns = elt.name().namespace()
            else:
                ns = value._ExpandedName.namespace()
        else:
            # Assume that somebody will handle the conversion to xs:anyType
            pass
        if isinstance(ns, pyxb.namespace.Namespace) and ns.isAbsentNamespace():
            ns = None
        if self.NC_any == self.__namespaceConstraint:
            return True
        if isinstance(self.__namespaceConstraint, tuple):
            (_, constrained_ns) = self.__namespaceConstraint
            assert self.NC_not == _
            if ns is None:
                return False
            if constrained_ns == ns:
                return False
            return True
        return ns in self.__namespaceConstraint

    # CM.newState:Wildcard
    def newState (self, parent_particle_state):
        return self

    # CS.accepts:Wildcard
    def accepts (self, particle_state, instance, value, element_use):
        ## Implement ContentState_mixin.accepts
        if isinstance(value, xml.dom.Node):
            value_desc = 'value in %s' % (value.nodeName,)
        else:
            value_desc = 'value of type %s' % (type(value),)
        if not self.matches(instance, value):
            return False
        if not isinstance(value, basis._TypeBinding_mixin):
            print 'NOTE: Created unbound wildcard element from %s' % (value_desc,)
        assert isinstance(instance.wildcardElements(), list), 'Uninitialized wildcard list in %s' % (instance._ExpandedName,)
        instance._appendWildcardElement(value)
        particle_state.incrementCount()
        return True

    # CM._validate:Wildcard
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

class SequenceState (ContentState_mixin):
    """Represent the state of validation against a sequence of particles."""
    
    __sequence = None           #<<< A L{GroupSequence} instance
    __particleState = None      #<<< The state corresponding to model within the sequence model
    __parentParticleState = None #<<< The state corresponding to the model containing the sequence

    __index = -1                #<<< Index in __sequence at which validation is proceeding

    __failed = False
    """C{True} iff the content provided is in conflict with the sequence
    requirements.

    Specifically, the model requires content that has not been provided.  Set
    within L{accepts}.  This state is sticky."""

    __satisfied = False
    """C{True} iff the content provided is consistent with the sequence
    requirements.

    Specifically, nothing has been presented with conflicts with the model.
    Set within L{notifyFailure}."""
    
    def __init__ (self, group, parent_particle_state):
        super(SequenceState, self).__init__(group)
        self.__sequence = group
        self.__parentParticleState = parent_particle_state
        self.__particles = group.particles()
        self.__index = -1
        self.__satisfied = False
        self.__failed = False
        # Kick this into the first element of the sequence
        self.notifyFailure(None, False)
        #print 'SS.CTOR %s: %d elts' % (self, len(self.__particles))

    # CS.accepts:SequenceState
    def accepts (self, particle_state, instance, value, element_use):
        ## Implement ContentState_mixin.accepts
        assert self.__parentParticleState == particle_state
        assert not self.__failed
        #print 'SS.ACC %s: %s %s %s' % (self, instance, value, element_use)
        while self.__particleState is not None:
            (consume, underflow_exc) = self.__particleState.step(instance, value, element_use)
            if consume:
                return True
            if underflow_exc is not None:
                self.__failed = True
                raise underflow_exc
        return False

    # CS._verifyComplete:SequenceState
    def _verifyComplete (self, parent_particle_state):
        while self.__particleState is not None:
            self.__particleState.verifyComplete()

    # CS.notifyFailure:SequenceState
    def notifyFailure (self, sub_state, particle_ok):
        self.__index += 1
        self.__particleState = None
        if self.__index < len(self.__particles):
            self.__particleState = ParticleState(self.__particles[self.__index], self)
        else:
            self.__satisfied = particle_ok
            if particle_ok:
                self.__parentParticleState.incrementCount()
        #print 'SS.NF %s: %d %s %s' % (self, self.__index, particle_ok, self.__particleState)

class ChoiceState (ContentState_mixin):
    def __init__ (self, group, parent_particle_state):
        self.__parentParticleState = parent_particle_state
        super(ChoiceState, self).__init__(group)
        self.__choices = [ ParticleState(_p, self) for _p in group.particles() ]
        self.__activeChoice = None
        #print 'CS.CTOR %s: %d choices' % (self, len(self.__choices))

    # CS.accepts:ChoiceState
    def accepts (self, particle_state, instance, value, element_use):
        ## Implement ContentState_mixin.accepts
        #print 'CS.ACC %s %s: %s %s %s' % (self, self.__activeChoice, instance, value, element_use)
        if self.__activeChoice is None:
            for choice in self.__choices:
                #print 'CS.ACC %s candidate %s' % (self, choice)
                try:
                    (consume, underflow_exc) = choice.step(instance, value, element_use)
                except Exception, e:
                    consume = False
                    underflow_exc = e
                #print 'CS.ACC %s: candidate %s : %s' % (self, choice, consume)
                if consume:
                    self.__activeChoice = choice
                    self.__choices = None
                    return True
            return False
        (consume, underflow_exc) = self.__activeChoice.step(instance, value, element_use)
        #print 'CS.ACC %s : active choice %s %s %s' % (self, self.__activeChoice, consume, underflow_exc)
        if consume:
            return True
        if underflow_exc is not None:
            self.__failed = True
            raise underflow_exc
        return False

    # CS._verifyComplete:ChoiceState
    def _verifyComplete (self, parent_particle_state):
        rv = True
        #print 'CS.VC %s: %s' % (self, self.__activeChoice)
        if self.__activeChoice is None:
            # Use self.__activeChoice as the iteration value so that it's
            # non-None when notifyFailure is invoked.
            for self.__activeChoice in self.__choices:
                try:
                    #print 'CS.VC: try %s' % (self.__activeChoice,)
                    self.__activeChoice.verifyComplete()
                    return
                except Exception, e:
                    pass
            #print 'Missing components %s' % ("\n".join([ "\n  ".join([str(_p2.term()) for _p2 in _p.particle().term().particles()]) for _p in self.__choices ]),)
            raise pyxb.MissingContentError('choice')
        self.__activeChoice.verifyComplete()

    # CS.notifyFailure:ChoiceState
    def notifyFailure (self, sub_state, particle_ok):
        #print 'CS.NF %s %s' % (self, particle_ok)
        if particle_ok and (self.__activeChoice is not None):
            self.__parentParticleState.incrementCount()
        pass

class AllState (ContentState_mixin):
    __activeChoice = None
    __needRetry = False
    def __init__ (self, group, parent_particle_state):
        self.__parentParticleState = parent_particle_state
        super(AllState, self).__init__(group)
        self.__choices = set([ ParticleState(_p, self) for _p in group.particles() ])
        #print 'AS.CTOR %s: %d choices' % (self, len(self.__choices))

    # CS.accepts:AllState
    def accepts (self, particle_state, instance, value, element_use):
        #print 'AS.ACC %s %s: %s %s %s' % (self, self.__activeChoice, instance, value, element_use)
        self.__needRetry = True
        while self.__needRetry:
            self.__needRetry = False
            if self.__activeChoice is None:
                for choice in self.__choices:
                    #print 'AS.ACC %s candidate %s' % (self, choice)
                    try:
                        (consume, underflow_exc) = choice.step(instance, value, element_use)
                    except Exception, e:
                        consume = False
                        underflow_exc = e
                    #print 'AS.ACC %s: candidate %s : %s' % (self, choice, consume)
                    if consume:
                        self.__activeChoice = choice
                        self.__choices.discard(self.__activeChoice)
                        return True
                return False
            (consume, underflow_exc) = self.__activeChoice.step(instance, value, element_use)
            #print 'AS.ACC %s : active choice %s %s %s' % (self, self.__activeChoice, consume, underflow_exc)
            if consume:
                return True
        if underflow_exc is not None:
            self.__failed = True
            raise underflow_exc
        return False

    # CS._verifyComplete:AllState
    def _verifyComplete (self, parent_particle_state):
        #print 'AS.VC %s: %s, %d left' % (self, self.__activeChoice, len(self.__choices))
        if self.__activeChoice is not None:
            self.__activeChoice.verifyComplete()
        while self.__choices:
            self.__activeChoice = self.__choices.pop()
            self.__activeChoice.verifyComplete()

    # CS.notifyFailure:AllState
    def notifyFailure (self, sub_state, particle_ok):
        #print 'AS.NF %s %s' % (self, particle_ok)
        self.__needRetry = True
        self.__activeChoice = None
        if particle_ok and (0 == len(self.__choices)):
            self.__parentParticleState.incrementCount()

class ParticleState (pyxb.cscRoot):

    __parentState = None
    """The L{ContentState_mixin} which contains the mode for which this is state."""
    
    __termState = None
    """A L{ContentState_mixin} instance for one occurrence of this particle's term."""
    
    __tryAccept = None
    """A flag indicating whether a proposed value should be applied to the
    state by L{step}."""

    def __init__ (self, particle, parent_state=None):
        self.__particle = particle
        self.__parentState = parent_state
        self.__count = -1
        #print 'PS.CTOR %s: particle %s' % (self, particle)
        self.incrementCount()

    __particle = None
    """The L{ParticleModel} for which this represents state."""

    def particle (self):
        """The L{ParticleModel} for which this represents state."""
        return self.__particle

    __count = None
    """The number of times this particle's term has been matched."""

    def incrementCount (self):
        """Reset for a new occurrence of the particle's term."""
        #print 'PS.IC %s' % (self,)
        self.__count += 1
        self.__termState = self.__particle.term().newState(self)
        self.__tryAccept = True

    def verifyComplete (self):
        """Check whether the particle's occurrence constraints are satisfied.

        @raise pyxb.MissingContentError: Particle requires additional content to be satisfied."""

        # @TODO@ Set a flag so we can make verifyComplete safe to call
        # multiple times?
        #print 'PS.VC %s entry' % (self,)

        # If we're not satisfied, check the term: that might do it.
        if not self.__particle.satisfiesOccurrences(self.__count):
            self.__termState._verifyComplete(self)

        # If we're still not satisfied, raise an error
        if not self.__particle.satisfiesOccurrences(self.__count):
            #print 'PS.VC %s incomplete' % (self,)
            raise pyxb.MissingContentError('incomplete')

        # If we are satisfied, tell the parent
        if self.__parentState is not None:
            self.__parentState.notifyFailure(self, True)

    def step (self, instance, value, element_use):
        """Attempt to apply the value as a new instance of the particle's term.

        The L{ContentState_mixin} created for the particle's term is consulted
        to determine whether the instance can accept the given value.  If so,
        the particle's maximum occurrence limit is checked; if not, and the
        particle has a parent state, it is informed of the failure.

        @param instance: An instance of a subclass of
        {basis.complexTypeDefinition}, into which the provided value will be
        stored if it is consistent with the current model state.

        @param value: The value that is being validated against the state.

        @param element_use: An optional L{ElementUse} instance that specifies
        the element to which the value corresponds.  This will be available
        when the value is extracted by parsing a document, but will be absent
        if the value was passed as a constructor positional parameter.

        @return: C{( consumed, underflow_exc )} A tuple where the first element
        is C{True} iff the provided value was accepted in the current state.
        When this first element is C{False}, the second element will be
        C{None} if the particle's occurrence requirements have been met, and
        is an instance of C{MissingElementError} if the observed number of
        terms is less than the minimum occurrence count.  Depending on
        context, the caller may raise this exception, or may try an
        alternative content model.

        @raise pyxb.UnexpectedElementError: if the value satisfies the particle,
        but having done so exceeded the allowable number of instances of the
        term.
        """

        #print 'PS.STEP %s: %s %s %s' % (self, instance, value, element_use)

        # Only try if we're not already at the upper limit on occurrences
        consumed = False
        underflow_exc = None

        # We can try the value against the term if we aren't at the maximum
        # count for the term.  Also, if we fail to consume, but as a side
        # effect of the test the term may have reset itself, we can try again.
        self.__tryAccept = True
        while self.__tryAccept and (self.__count != self.__particle.maxOccurs()):
            self.__tryAccept = False
            consumed = self.__termState.accepts(self, instance, value, element_use)
            #print 'PS.STEP %s: ta %s %s' % (self, self.__tryAccept, consumed)
            self.__tryAccept = self.__tryAccept and (not consumed)
        #print 'PS.STEP %s: %s' % (self, consumed)
        if consumed:
            if not self.__particle.meetsMaximum(self.__count):
                raise pyxb.UnexpectedElementError('too many')
        else:
            if self.__parentState is not None:
                self.__parentState.notifyFailure(self, self.__particle.satisfiesOccurrences(self.__count))
            if not self.__particle.meetsMinimum(self.__count):
                # @TODO@ Use better exception; changing this will require
                # changing some unit tests.
                underflow_exc = pyxb.MissingElementError(content=value, container=instance)
        return (consumed, underflow_exc)

    def __str__ (self):
        particle = self.__particle
        return 'ParticleState(%d:%d,%s:%s)@%x' % (self.__count, particle.minOccurs(), particle.maxOccurs(), particle.term(), id(self))

class ParticleModel (ContentModel_mixin):
    """Content model dealing with particles: terms with occurrence restrictions"""

    __minOccurs = None
    def minOccurs (self):
        """The minimum number of times the term must occur.

        This will be a non-negative integer."""
        return self.__minOccurs

    __maxOccurs = None
    def maxOccurs (self):
        """The maximum number of times the term may occur.  

        This will be a positive integer, or C{None} indicating an unbounded
        number of occurrences."""
        return self.__maxOccurs

    __term = None
    """The L{ContentModel_mixin} for a single occurrence."""
    def term (self):
        """The term for a single occurrence."""
        return self.__term

    def meetsMaximum (self, count):
        """@return: C{True} iff there is no maximum on term occurrence, or the
        provided count does not exceed that maximum"""
        return (self.__maxOccurs is None) or (count <= self.__maxOccurs)

    def meetsMinimum (self, count):
        """@return: C{True} iff the provided count meets the minimum number of
        occurrences"""
        return count >= self.__minOccurs

    def satisfiesOccurrences (self, count):
        """@return: C{True} iff the provided count satisfies the occurrence
        requirements"""
        return self.meetsMinimum(count) and self.meetsMaximum(count)

    def __init__ (self, term, min_occurs=1, max_occurs=1):
        self.__term = term
        self.__minOccurs = min_occurs
        self.__maxOccurs = max_occurs

    # CM.newState:ParticleModel
    def newState (self):
        return ParticleState(self)

    def validate (self, symbol_set):
        """Determine whether the particle requirements are satisfiable by the
        given symbol set.

        The symbol set represents letters in an alphabet.  If those letters
        can be combined in a way that satisfies the regular expression
        expressed in the model, a satisfying sequence is returned and the
        symbol set is reduced by the letters used to form the sequence.  If
        the content model cannot be satisfied, C{None} is returned and the
        symbol set remains unchanged.

        @param symbol_set: A map from L{ElementUse} instances to a list of
        values.  The order of the values corresponds to the order in which
        they should appear.  A key of C{None} identifies values that are
        stored as wildcard elements.  Values are removed from the lists as
        they are used; when the last value of a list is removed, its key is
        removed from the map.  Thus an empty dictionary is the indicator that
        no more symbols are available.

        @return: returns C{None}, or a list of tuples C{( eu, val )} where
        C{eu} is an L{ElementUse} from the set of symbol keys, and C{val} is a
        value from the corresponding list.
        """
        
        output_sequence = []
        #print 'Start: %d %s %s : %s' % (self.__minOccurs, self.__maxOccurs, self.__term, symbol_set)
        result = self._validate(symbol_set, output_sequence)
        #print 'End: %s %s %s' % (result, symbol_set, output_sequence)
        if result:
            return (symbol_set, output_sequence)
        return None

    # CM._validate:ParticleModel
    def _validate (self, symbol_set, output_sequence):
        symbol_set_mut = self._validateCloneSymbolSet(symbol_set)
        output_sequence_mut = self._validateCloneOutputSequence(output_sequence)
        count = 0
        #print 'VAL start %s: %d %s' % (self.__term, self.__minOccurs, self.__maxOccurs)
        last_size = len(output_sequence_mut)
        while (count != self.__maxOccurs) and self.__term._validate(symbol_set_mut, output_sequence_mut):
            #print 'VAL %s old cnt %d, left %s' % (self.__term, count, symbol_set_mut)
            this_size = len(output_sequence_mut)
            if this_size == last_size:
                # Validated without consuming anything.  Assume we can
                # continue to do so, jump to the minimum, and exit.
                if count < self.__minOccurs:
                    count = self.__minOccurs
                break
            count += 1
            last_size = this_size
        result = self.satisfiesOccurrences(count)
        if (result):
            self._validateReplaceResults(symbol_set, symbol_set_mut, output_sequence, output_sequence_mut)
        #print 'VAL end PRT %s res %s: %s %s %s' % (self.__term, result, self.__minOccurs, count, self.__maxOccurs)
        return result

class _Group (ContentModel_mixin):
    """Base class for content information pertaining to a U{model
    group<http://www.w3.org/TR/xmlschema-1/#Model_Groups>}.

    There is a specific subclass for each group compositor.
    """

    _StateClass = None
    """A reference to a L{ContentState_mixin} class that maintains state when
    validating an instance of this group."""

    __particles = None
    """List of L{ParticleModel}s comprising the group."""

    def particles (self):
        """The sequence of particles comprising the group"""
        return self.__particles

    def __init__ (self, *particles):
        self.__particles = particles

    # CM.newState:_Group
    # CM.newState:GroupAll CM.newState:GroupSequence CM.newState:GroupChoice
    def newState (self, parent_particle_state):
        return self._StateClass(self, parent_particle_state)

    # All and Sequence share the same validation code, so it's up here.
    # CM._validate:GroupAll CM._validate:GroupSequence
    def _validate (self, symbol_set, output_sequence):
        symbol_set_mut = self._validateCloneSymbolSet(symbol_set)
        output_sequence_mut = self._validateCloneOutputSequence(output_sequence)
        for p in self.particles():
            if not p._validate(symbol_set_mut, output_sequence_mut):
                return False
        self._validateReplaceResults(symbol_set, symbol_set_mut, output_sequence, output_sequence_mut)
        return True


class GroupChoice (_Group):
    _StateClass = ChoiceState

    # CM._validate:GroupChoice
    def _validate (self, symbol_set, output_sequence):
        # Only reset the state variables on partial success (or on entry),
        # when they've been "corrupted" from copies of the input.
        reset_mutables = True
        for p in self.particles():
            if reset_mutables:
                symbol_set_mut = self._validateCloneSymbolSet(symbol_set)
                output_sequence_mut = self._validateCloneOutputSequence(output_sequence)
            if p._validate(symbol_set_mut, output_sequence_mut):
                self._validateReplaceResults(symbol_set, symbol_set_mut, output_sequence, output_sequence_mut)
                return True
            # If we succeeded partially but not completely, reset the state
            # variables
            reset_mutables = len(output_sequence) != len(output_sequence_mut)
        return False

class GroupAll (_Group):
    _StateClass = AllState

class GroupSequence (_Group):
    _StateClass = SequenceState
        
## Local Variables:
## fill-column:78
## End:
    
