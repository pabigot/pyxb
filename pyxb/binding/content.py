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

AttributeUse and ElementUse record information associated with a binding
class, for example the types of values, the original XML QName or NCName, and
the Python field in which the values are stored.

ContentModelTransition, ContentModelState, and ContentModel are used to store
a deterministic finite automaton which is used to translate DOM nodes into
values stored in an instance corresponding to a complex type definition.

ModelGroupAllAlternative and ModelGroupAll represent special nodes in the DFA
that support a model group with compositor "all" in a way that does not result
in an exponential state explosion in the DFA.

Particle, ModelGroup, and Wildcard are used to encode an earlier
representation of the content model, now used only for generating DOM
instances from bindings (as opposed to the other direction handled by
ContentModel).  Wildcard is also used in the DFA-based content model.
"""

import pyxb
import pyxb.namespace
import basis

import xml.dom

class AttributeUse (pyxb.cscRoot):
    """A helper class that encapsulates everything we need to know
    about the way an attribute is used within a binding class.

    Attributes are stored as pairs C{(provided, value)}, where C{provided} is a
    boolean indicating whether a value for the attribute was provided by the
    DOM node, and C{value} is an instance of the attribute datatype.  The
    provided flag is used to determine whether an XML attribute should be
    added to a created DOM node when generating the XML corresponding to a
    binding instance.

    @todo: Store the extended namespace name of the attribute.
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
        @type name: C{unicode}

        @param id: The Python identifier for the attribute within the
        containing L{pyxb.basis.binding.complexTypeDefinition}.  This is a
        public identifier, albeit modified to be unique, and is usually used
        as the name of the attribute's inspector method.
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
        """Expanded name of the attribute in its element"""
        return self.__name
    
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

    def addDOMAttribute (self, ctd_instance, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        ( provided, value ) = self.__getValue(ctd_instance)
        if provided:
            assert value is not None
            element.setAttributeNS(self.__name.namespaceURI(), self.__name.localName(), value.xsdLiteral())
        return self

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
            if unicode_value is not None:
                if self.__prohibited:
                    raise pyxb.ProhibitedAttributeError('Prohibited attribute %s found' % (self.__name,))
            else:
                if self.__required:
                    raise pyxb.MissingAttributeError('Required attribute %s not found' % (self.__name,))
                provided = False
                unicode_value = self.__unicodeDefault
            if unicode_value is None:
                # Must be optional and absent
                provided = False
                new_value = None
            else:
                new_value = self.__dataType(unicode_value)
        else:
            assert new_value is not None
            if not isinstance(new_value, self.__dataType):
                new_value = self.__dataType.Factory(new_value)
        if self.__fixed and (new_value != self.__defaultValue):
            raise pyxb.AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__name,))
        self.__setValue(ctd_instance, new_value, provided)
        return new_value

class ElementUse (pyxb.cscRoot):
    """Aggregate the information relevant to an element of a complex type.

    This includes the original tag name, the spelling of the corresponding
    object in Python, an indicator of whether multiple instances might be
    associated with the field, and a list of types for legal values of the
    field.

    @todo: Store the extended namespace name of the element.
    """

    def name (self):
        """The Unicode XML NCName of the element."""
        return self.__name
    __name = None

    def id (self):
        """The string name of the binding class field used to hold the element
        values.

        This is the user-visible name, and excepting namespace disambiguation
        will be equal to the name."""
        return self.__id
    __id = None

    # The dictionary key used to identify the value of the element.  The value
    # is the same as that used for private member variables in the binding
    # class within which the element declaration occurred.
    __key = None

    def elementBinding (self):
        """A list of binding classes that express the permissible types of
        element instances for this use."""
        return self.__elementBinding
    def _setElementBinding (self, element_binding):
        self.__elementBinding = element_binding
        return self
    __elementBinding = None

    def isPlural (self):
        """True iff the content model indicates that more than one element
        can legitimately belong to this use.

        This includes elements in particles with maxOccurs greater than one,
        and when multiple elements with the same NCName are declared in the
        same type.

        @todo Fix this: if a type has a reference to ns1:foo and a different
        one to ns2:foo, the two should not end up in the same python field.

        """
        return self.__isPlural
    __isPlural = False

    # If not None, this specifies an ElementUse in a binding class for
    # which this element use is a restriction.  That element use is
    # what is used to store the corresponding values, after validating
    # them against elementBinding at this level.
    __parentUse = None

    def __init__ (self, name, id, key, is_plural, element_binding=None):
        """Create an ElementUse instance.

        @param name: The name by which the attribute is referenced in the XML
        @type name: C{unicode}

        @param id: The Python name for the element within the
        containing L{pyxb.basis.binding.complexTypeDefinition}.  This is a
        public identifier, albeit modified to be unique, and is usually
        used as the name of the element's inspector method.
        @type id: C{str}

        @param key: The string used to store the element
        value in the dictionary of the containing
        L{pyxb.basis.binding.complexTypeDefinition}.  This is mangled so
        that it is unique among and is treated as a Python private member.
        @type key: C{str}

        @param is_plural: If C{True}, documents for the corresponding type may
        have multiple instances of this element.  As a consequence, the value
        of the element will be a list.  If C{False}, the value will be C{None}
        if the element is absent, and a reference to an instance of
        L{pyxb.binding.basis.element._TypeDefinition} if present.
        @type is_plural: C{bool}

        @param element_binding: Reference to the class that serves as the
        binding for the element.

        @todo: Ensure that an element referenced from multiple complex types
        uses the correct name in each context.

        """
        self.__name = name
        self.__id = id
        self.__key = key
        self.__isPlural = is_plural
        self.__elementBinding = element_binding

    def defaultValue (self):
        if self.isPlural():
            return []
        return None

    def value (self, ctd_instance):
        return getattr(ctd_instance, self.__key, self.defaultValue())

    def reset (self, ctd_instance):
        setattr(ctd_instance, self.__key, self.defaultValue())
        return self

    def __setValue (self, ctd_instance, value):
        #print 'Set value of %s to %s' % (self.name(), value)
        if self.isPlural():
            return values
        return 

    # @todo Distinguish based on plurality
    def set (self, ctd_instance, value):
        """Set the value of this element in the given instance."""
        if value is None:
            return self.reset(ctd_instance)
        assert self.__elementBinding is not None
        elt_type = self.__elementBinding.typeDefinition()
        if not isinstance(value, elt_type):
            value = elt_type.Factory(value)
        setattr(ctd_instance, self.__key, value)
        if isinstance(value, list):
            [ ctd_instance._addContent(_elt) for _elt in value ]
        else:
            ctd_instance._addContent(value)
        return self

    def append (self, ctd_instance, value):
        if not self.isPlural():
            raise pyxb.StructuralBadDocumentError('Cannot append to element with non-plural multiplicity')
        values = self.value(ctd_instance)
        values.append(value)
        ctd_instance._addContent(value)
        return values

    def toDOM (self, dom_support, parent, value):
        element = dom_support.createChild(self.name().localName(), self.name().namespace(), parent)
        if isinstance(value, basis._Binding_mixin):
            elt_type = self.__elementBinding.typeDefinition()
            val_type = type(value)
            if isinstance(value, basis.complexTypeDefinition):
                assert isinstance(value, elt_type)
            else:
                if isinstance(value, basis.STD_union) and isinstance(value, elt_type._MemberTypes):
                    val_type = elt_type
            if (val_type != elt_type._SupersedingClass()) and elt_type._Abstract:
                val_type_qname = value._ExpandedName.localName()
                tns_prefix = dom_support.namespacePrefix(value._ExpandedName.namespace())
                if tns_prefix is not None:
                    val_type_qname = '%s:%s' % (tns_prefix, val_type_qname)
                dom_support.addAttribute(element, pyxb.namespace.XMLSchema_instance.createExpandedName('type'), val_type_qname)
            value._toDOM_vx(dom_support, element)
        elif isinstance(value, (str, unicode)):
            element.appendChild(dom_support.document().createTextNode(value))
        else:
            raise pyxb.LogicError('toDOM with unrecognized value type %s: %s' % (type(value), value))

class ContentModelStack (object):
    """A stack of states and content models."""

    __stack = None
    def __init__ (self, content_model, state=1):
        self.__stack = []
        self.pushModelState(content_model, state)

    def pushModelState (self, content_model, state):
        self.__stack.append( (content_model, state) )
        return self

    def isTerminal (self):
        return 0 == len(self.__stack)

    def popModelState (self):
        if self.isTerminal():
            raise pyxb.LogicError('Attempt to underflow content model stack')
        return self.__stack.pop()

    def step (self, ctd_instance, value):
        (content_model, state) = self.popModelState()
        state = content_model.step(ctd_instance, state, value, model_stack)
        if state is not None:
            self.pushModelState(content_model, state)
        return self.isTerminal()

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
    __elementUse = None

    # Types of transition that can be taken, in order of preferred match
    TT_element = 0x01           #<<< The transition is on an element
    TT_modelGroupAll = 0x02     #<<< The transition is on an ALL model group
    TT_wildcard = 0x03          #<<< The transition is on a wildcard

    # What type of term this transition covers
    __termType = None

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
            # by name.
            if (self.TT_element == self.__termType):
                rv = cmp(self.__elementUse.name(), other.__elementUse.name())
            else:
                rv = cmp(self.__term, other.__term)
        return rv

    def __processElementTransition (self, node):
        # First, identify the element
        if not self.term().name().nodeMatches(node):
            return None
        elt_name = pyxb.namespace.ExpandedName(node)
        element = self.term().createFromDOM(node)
        return element

    def __validateConsume (self, key, available_symbols_im, output_sequence_im, candidates):
        next_symbols = available_symbols_im.copy()
        # If the transition is a loop back to the current state, or if the
        # transition is a simple type definition with variety list, we can
        # consume multiple instances.  Might as well consume all of them.
        key_type = type(None)
        if key is not None:
            key_type = key.elementBinding().typeDefinition()
        if issubclass(key_type, basis.STD_list):
            consume_all = True
            consume_singles = isinstance(next_symbols[key][0], (list, tuple))
        elif (self.__nextState == self.__currentStateRef.state()):
            consume_all = True
            consume_singles = True
        else:
            consume_all = False
            consume_singles = True
        if consume_all:
            consumed = next_symbols[key]
            del next_symbols[key]
        else:
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
        """Make the best transition from this node.

        Updates candidates.
        Return True iff a transition could be made."""
        if self.TT_element == self.__termType:
            if not (self.__elementUse in available_symbols_im):
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

    def attemptTransition (self, ctd_instance, node):
        """Attempt to make the appropriate transition.

        If something goes wrong, a BadDocumentError will be propagated through
        this call, and node_list will remain unchanged.  If everything works,
        the prefix of the node_list that matches the transition will have been
        stripped away, and if the store parameter is True, the resulting
        binding instances will be stored in the proper location of
        ctd_instance.
        """

        if self.TT_element == self.__termType:
            element = self.__processElementTransition(node)
            if element is None:
                return False
            if self.__elementUse.isPlural():
                self.__elementUse.append(ctd_instance, element)
            else:
                self.__elementUse.set(ctd_instance, element)
        elif self.TT_modelGroupAll == self.__termType:
            self.__term.matchAlternatives(ctd_instance, node_list)
        elif self.TT_wildcard == self.__termType:
            if not self.__term.matchesNode(ctd_instance, node):
                raise pyxb.UnexpectedContentError(node)
            # See if we can convert from DOM into a Python instance.
            # If not, we'll go ahead and store the DOM node.
            try:
                ns = pyxb.namespace.NamespaceForURI(node.namespaceURI, create_if_missing=True)
                if ns.module() is not None:
                    node = ns.module().CreateFromDOM(node)
                elif ns.modulePath() is not None:
                    print 'Importing %s' % (ns.modulePath(),)
                    mod = __import__(ns.modulePath())
                    for c in ns.modulePath().split('.')[1:]:
                        mod = getattr(mod, c)
                    node = mod.CreateFromDOM(node)
                elif pyxb.namespace.XMLSchema == ns:
                    print 'Need to dynamically create schema'
            except Exception, e:
                print 'WARNING: Unable to convert wildcard %s %s to Python instance: %s' % (node.namespaceURI, node.localName, e)
            ctd_instance.wildcardElements().append(node)
        else:
            raise pyxb.LogicError('Unexpected transition term %s' % (self.__term,))
        return True

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

    def transitions (self):
        return self.__transitions
    
    def evaluateContent (self, ctd_instance, node, model_stack=None):
        """Determine where to go from this state.

        If a transition matches, the consumed prefix of node_list has been
        stripped, the resulting data stored in ctd_instance if store is True,
        and the next state is returned.

        If no transition can be made, and this state is a final state for the
        DFA, the value None is returned.

        @param ctd_instance: The binding instance holding the content
        @param node_list: in/out list of DOM nodes that comprise instance content
        @param store: whether this actually consumes or just tests
        @raise pyxb.UnrecognizedContentError: trailing material that does not match content model
        @raise pyxb.MissingContentError: content model requires additional data
        """

        for transition in self.__transitions:
            # @todo check nodeName against element
            if transition.attemptTransition(ctd_instance, node):
                return transition.nextState()
        if self.isFinal():
            return None
        raise pyxb.UnrecognizedContentError(node)

class ContentModel (pyxb.cscRoot):
    """The ContentModel is a deterministic finite state automaton which can be
    traversed using a sequence of DOM nodes which are matched on transitions
    against the legal content model of a complex type."""

    # Map from integers to ContentModelState instances
    __stateMap = None

    def __init__ (self, state_map=None):
        self.__stateMap = state_map

    def initialState (self):
        return ContentModelStack(self)

    def _step (self, ctd_instance, state, value, model_stack):
        state = self.__stateMap[state].evaluateContent(ctd_instance, node_list, model_stack)

    def interprete (self, ctd_instance, node_list):
        """Attempt to match the content model against the node_list.

        When a state has been reached from which no transition is possible,
        this method returns (if the end state is a final state), or throws a
        MissingContentError.  There may be material remaining on the
        node_list; it is up to the caller to determine whether this is
        acceptable."""
        state = 1 # self.initialState()
        while state is not None:
            node_list = ctd_instance._stripMixedContent(node_list)
            next_state = None
            if 0 < len(node_list):
                next_state = self.__stateMap[state].evaluateContent(ctd_instance, node_list[0])
                if next_state is not None:
                    node_list.pop(0)
            if next_state is None:
                if not self.__stateMap[state].isFinal():
                    raise pyxb.MissingContentError()
            state = next_state
        node_list = ctd_instance._stripMixedContent(node_list)
        if state is not None:
            raise pyxb.MissingContentError()

    def validate (self, available_symbols, allow_residual=False):
        matches = []
        candidates = []
        candidates.append( (1, available_symbols, []) )
        while 0 < len(candidates):
            (state_id, symbols, sequence) = candidates.pop(0)
            state = self.__stateMap[state_id]
            if 0 == len(symbols):
                if state.isFinal():
                    matches.append( (symbols, sequence) )
                    return matches
                continue
            num_transitions = 0
            for transition in state.transitions():
                num_transitions += transition.validate(symbols, sequence, candidates)
            if (0 == num_transitions) and allow_residual:
                matches.append( (symbols, sequence) )
                return matches
        return matches

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
                matches = alt.contentModel().validate(symbols, allow_residual=True)
                if 0 == len(matches):
                    break
                (new_symbols, new_sequence) = matches[0]
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

    def matchAlternatives (self, ctd_instance, node_list):
        """Match the node_list against the alternatives in this model group.

        This method creates a set holding all the alternatives, then walks the
        node list attempting to match against the content model of each
        alternative in turn.  The store flag is cleared during this process,
        so that the ctd_instance fields are not updated but the node_list
        values are removed.  Upon successful recognition of all required
        alternatives, the node_list is restored and the content model matching
        repeated with store set to update the ctd_instance values.

        @note: The UPA ensures that this can be greedy.
        """

        alternatives = set(self.__alternatives)
        match_order = []
        found_match = True

        # The alternatives can match in arbitrary order, so repeatedly try
        # them until they're all gone or no match can be found.
        while (0 < len(alternatives)) and found_match:
            found_match = False
            for alt in alternatives:
                try:
                    node_count = len(node_list)
                    alt.contentModel().interprete(ctd_instance, node_list)
                    if len(node_list) < node_count:
                        match_order.append(alt)
                        alternatives.remove(alt)
                        found_match = True
                        break
                except pyxb.BadDocumentError, e:
                    print 'Failed with alternative %s: %s' % (alt, type(e))
                    pass
        # If there's a required alternative that wasn't matched, raise
        # an error
        if 0 < len(alternatives):
            for alt in alternatives:
                if alt.required():
                    raise pyxb.MissingContentError(alt)

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

    def matchesNode (self, ctd_instance, node):
        """Return True iff the node is a valid match against this wildcard.

        Not implemented yet: all wildcards are assumed to match all
        nodes.

        """
        # @todo check node against namespace constraint and process contents
        #print 'WARNING: Accepting node as wildcard match without validating.'
        return True

## Local Variables:
## fill-column:78
## End:
    
