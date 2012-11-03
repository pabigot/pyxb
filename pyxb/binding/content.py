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

"""Helper classes that maintain the content model of XMLSchema in the binding
classes.

L{AttributeUse} and L{ElementDeclaration} record information associated with a binding
class, for example the types of values, the original XML QName or NCName, and
the Python field in which the values are stored.  They also provide the
low-level interface to set and get the corresponding values in a binding
instance.

L{Wildcard} holds content-related information used in the content model.
"""

import pyxb
import pyxb.namespace
import pyxb.utils.fac
from pyxb.binding import basis

import xml.dom
import logging

_log = logging.getLogger(__name__)

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

        @raise pyxb.SimpleTypeValueError: the L{unicode_default} cannot be used
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
        super(AttributeUse, self).__init__()

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
                raise pyxb.ProhibitedAttributeError(type(ctd_instance), self.__name, ctd_instance)
            if self.__required and not provided:
                assert self.__fixed
                raise pyxb.MissingAttributeError(type(ctd_instance), self.__name, ctd_instance)
            if not self.__dataType._IsValidValue(value):
                raise pyxb.AttributeValueError(type(ctd_instance), self.__name, ctd_instance)
            self.__dataType.XsdConstraintsOK(value)
        else:
            if self.__required:
                raise pyxb.MissingAttributeError(type(ctd_instance), self.__name, ctd_instance)

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
                    raise pyxb.MissingAttributeError(type(ctd_instance), self.__name, ctd_instance)
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
                raise pyxb.MissingAttributeError(type(ctd_instance), self.__name, ctd_instance)
            provided = False
        if provided and self.__prohibited:
            raise pyxb.ProhibitedAttributeError(type(ctd_instance), self.__name, ctd_instance)
        if (new_value is not None) and (not isinstance(new_value, self.__dataType)):
            new_value = self.__dataType.Factory(new_value, _from_xml=from_xml)
        if self.__fixed and (new_value != self.__defaultValue):
            raise pyxb.AttributeChangeError(type(ctd_instance), self.__name, ctd_instance)
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

class AutomatonConfiguration (object):
    """State for a L{pyxb.utils.fac.Automaton} monitoring content for an
    incrementally constructed complex type binding instance.

    @warning: This is not an implementation of
    L{pyxb.utils.fac.Configuration_ABC} because we need the L{step} function
    to return a different type of value."""

    # The binding instance for which content is being built
    __instance = None

    # The underlying configuration when the state is deterministic.  In this
    # case, all updates to the instance content corresponding to the current
    # state have been applied to the instance.  Note that while steps are
    # occurring this instance, as well as those in __multi, might be
    # references to sub-automata.
    __cfg = None

    # A list of pairs when the state is non-deterministic.  The first member
    # of the pair is the configuration; the second is a tuple of closures that
    # must be applied to the instance in order to store the content that was
    # accepted along the path to that configuration.  This is in order of
    # preference based on the location of path candidate declarations in the
    # defining schema.
    __multi = None

    def __init__ (self, instance):
        self.__instance = instance

    def reset (self):
        """Reset the automaton to its initial state.

        Subsequent transitions are expected based on candidate content to be
        supplied through the L{step} method."""
        self.__cfg = self.__instance._Automaton.newConfiguration()
        self.__multi = None

    def step (self, value, element_decl):
        """Attempt a transition from the current state.

        @param value: the content to be supplied.  For success the value must
        be consistent with the recorded symbol (element or wildcard
        declaration) for a transition from the current automaton state.

        @param element_decl: optional
        L{pyxb.binding.content.ElementDeclaration} that is the preferred
        symbol for the transition.

        @return: the cardinal number of successful transitions from the
        current configuration based on the parameters."""

        sym = (value, element_decl)

        # Start with the current configuration(s), assuming we might see
        # non-determinism.
        new_multi = []
        if self.__multi is None:
            multi = [ (self.__cfg, ()) ]
        else:
            multi = self.__multi[:]
        # Collect the complete set of reachable configurations along with the
        # closures that will update the instance content based on the path.
        for (cfg, pending) in multi:
            cand = cfg.candidateTransitions(sym)
            for transition in cand:
                clone_map = {}
                ccfg = cfg.clone(clone_map)
                new_multi.append( (transition.apply(ccfg, clone_map), pending+(transition.consumedSymbol().consumingClosure(),)) )
        rv = len(new_multi)
        if 0 == rv:
            # No candidate transitions.  Do not change the state.
            return 0
        if 1 == rv:
            # Deterministic transition.  Save the configuration and apply the
            # corresponding updates.
            self.__multi = None
            (self.__cfg, actions) = new_multi[0]
            for fn in actions:
                fn(self.__instance)
        else:
            # Non-deterministic.  Save everything for subsequent resolution.
            self.__cfg = None
            self.__multi = new_multi
        return rv

    def resolveNondeterminism (self, prefer_accepting=True):
        """Resolve any non-determinism in the automaton state.

        If the automaton has reached a single configuration (was
        deterministic), this does nothing.

        If multiple candidate configurations are available, the best one is
        selected and applied, updating the binding instance with the pending
        content.

        "Best" in this case is determined by optionally eliminating
        configurations that are not accepting, then selecting the path where
        the initial transition sorts highest using the binding sort key (based
        on position in the original schema).

        @keyword prefer_accepting: eliminate non-accepting paths if any
        accepting path is present."""
        if self.__multi is None:
            return
        assert self.__cfg is None
        multi = self.__multi
        if prefer_accepting:
            multi = filter(lambda _ts: _ts[0].isAccepting(), self.__multi)
            if 0 == len(multi):
                multi = self.__multi
        # step() will not create an empty multi list, so cannot get here with
        # no configurations available unless nobody even reset the
        # configuration, which would be a usage error.
        assert 0 < len(multi)
        if 1 < len(multi):
            desc = self.__instance._ExpandedName
            if desc is None:
                desc = type(self.__instance)
            _log.warning('Multiple accepting paths for %s', desc)
            '''
            for (cfg, actions) in multi:
                foo = type(self.__instance)()
                for fn in actions:
                    fn(foo)
                print '1: %s ; 2 : %s ; wc: %s' % (foo.first, foo.second, foo.wildcardElements())
            '''
        (self.__cfg, actions) = multi[0]
        self.__multi = None
        for fn in actions:
            fn(self.__instance)

    def isAccepting (self):
        """Return C{True} iff the automaton is in an accepting state.

        If the automaton has unresolved nondeterminism, it is resolved first,
        preferring accepting states."""
        self.resolveNondeterminism(True)
        cfg = self.__cfg
        while cfg.superConfiguration is not None:
            cfg = cfg.superConfiguration
        return cfg.isAccepting()

    def sequencedChildren (self):
        """Implement L{pyxb.binding.basis.complexTypeDefinition._validatedChildren}.

        Go there for the interface.
        """

        # We need a fresh automaton configuration corresponding to the type of
        # the binding instance.
        self.reset()
        cfg = self.__cfg

        # The validated sequence
        symbols = []

        # The available content, in a map from ElementDeclaration to in-order
        # values.  The key None corresponds to the wildcard content.  Keys are
        # removed when their corresponding content is exhausted.
        symbol_set = self.__instance._symbolSet()
        while symbol_set:
            # Find the first acceptable transition without filtering on any
            # symbols
            selected_xit = None
            for xit in cfg.candidateTransitions(None):
                csym = xit.consumedSymbol()
                if isinstance(csym, ElementUse):
                    ed = csym.elementDeclaration()
                elif isinstance(csym, WildcardUse):
                    ed = None
                else:
                    assert False
                # Check whether we have content that matches the symbol
                matches = symbol_set.get(ed)
                if matches is None:
                    continue
                if not csym.match((matches[0], ed)):
                    continue
                # Commit to this transition and consume the selected content
                symbols.append( (ed, csym.retrieveContent()) )
                selected_xit = xit
                matches.pop(0)
                if 0 == len(matches):
                    del symbol_set[ed]
                break
            if selected_xit is None:
                break
            cfg = selected_xit.apply(cfg)
        # Exit out of any sub-configurations (they might be accepting while
        # the superConfiguration is not)
        while cfg.superConfiguration:
            cfg = cfg.superConfiguration
        if not cfg.isAccepting():
            _log.warning('Incomplete content, expect %s' % (' or '.join(map(lambda _xit: str(_xit.consumedSymbol()), cfg.candidateTransitions(None))),))
            raise pyxb.BindingValidationError(cfg, symbol_set)
        if symbol_set:
            raise pyxb.BindingValidationError('Unvalidated symbols: %s' % (symbol_set,) )
        return symbols
                    
class ElementUse (pyxb.utils.fac.SymbolMatch_mixin):
    """Information about a schema element declaration reference.

    This is used by the FAC content model to identify the location
    within a schema at which an element use appears.  The L{ElementDeclaration}
    is not sufficient since multiple uses in various schema, possibly in
    different namespaces, may refer to the same declaration but be independent
    uses.
    """

    __elementDeclaration = None
    __schemaLocation = None

    def elementDeclaration (self):
        return self.__elementDeclaration

    def schemaLocation (self):
        return self.__schemaLocation

    def __init__ (self, element_declaration, schema_location):
        super(ElementUse, self).__init__()
        self.__elementDeclaration = element_declaration
        self.__schemaLocation = schema_location

    # A cached value accepted by the match method.  Subsequently either
    # storeContent or consumingClosure should be invoked to clear it.
    __acceptedValue = None

    def retrieveContent (self):
        """Read back an the content archived by a previous accepting match."""
        rv = self.__acceptedValue
        self.__acceptedValue = None
        return rv

    def storeContent (self, instance):
        """Apply the value accepted by L{match} to the content of the instance."""
        assert self.__acceptedValue is not None
        self.__elementDeclaration.setOrAppend(instance, self.__acceptedValue)
        self.__acceptedValue = None

    def consumingClosure (self):
        """Create a closure that will apply the value accepted by L{match} to a to-be-supplied instance."""
        assert self.__acceptedValue is not None
        rv = lambda _inst,_ed=self.__elementDeclaration,_av=self.__acceptedValue: _ed.setOrAppend(_inst, _av)
        self.__acceptedValue = None
        return rv
        
    def match (self, symbol):
        """Satisfy L{pyxb.utils.fac.SymbolMatch_mixin}.

        Determine whether the proposed content encapsulated in C{symbol} is
        compatible with the element declaration.  If so, the accepted value is
        cached internally and return C{True}; otherwise return C{False}.

        @param symbol: a pair C{(value, element_decl)}.
        L{pyxb.binding.content.ElementDeclaration._matches} is used to
        determine whether the proposed content is compatible with this element
        declaration."""
        (value, element_decl) = symbol
        # NB: this call may change value to be compatible
        (rv, value) = self.__elementDeclaration._matches(value, element_decl)
        if rv:
            self.__acceptedValue = value
        return rv

    def __str__ (self):
        return '%s per %s' % (self.__elementDeclaration.name(), self.__schemaLocation)

class WildcardUse (pyxb.utils.fac.SymbolMatch_mixin):
    """Information about a schema wildcard element.

    This is functionally parallel to L{ElementUse}, but references a
    L{Wildcard} that is unique to this instance.  That L{Wildcard} is not
    incorporated into this class is an artifact of the evolution of PyXB."""

    __wildcardDeclaration = None
    __schemaLocation = None

    def wildcardDeclaration (self):
        return self.__wildcardDeclaration

    def schemaLocation (self):
        return self.__schemaLocation

    # A cached value accepted by the match method.  Subsequently either
    # storeContent or consumingClosure should be invoked to clear it.
    __acceptedValue = None
    
    def retrieveContent (self):
        """Read back an the content archived by a previous accepting match."""
        rv = self.__acceptedValue
        self.__acceptedValue = None
        return rv

    def storeContent (self, instance):
        """Apply the value accepted by L{match} to the content of the instance."""
        assert self.__acceptedValue is not None
        instance._appendWildcardElement(self.__acceptedValue)
        self.__acceptedValue = None
        
    def consumingClosure (self):
        """Create a closure that will apply the value accepted by L{match} to a to-be-supplied instance."""
        assert self.__acceptedValue is not None
        rv = lambda _inst,av=self.__acceptedValue: _inst._appendWildcardElement(av)
        self.__acceptedValue = None
        return rv

    def match (self, symbol):
        """Satisfy L{pyxb.utils.fac.SymbolMatch_mixin}.

        Determine whether the proposed content encapsulated in C{symbol} is
        compatible with the wildcard declaration.  If so, the accepted value
        is cached internally and return C{True}; otherwise return C{False}.

        @param symbol: a pair C{(value, element_decl)}.
        L{pyxb.binding.content.Wildcard.matches} is used to determine whether
        the proposed content is compatible with this wildcard.
        """
        (value, element_decl) = symbol
        rv = self.__wildcardDeclaration.matches(None, value)
        if rv:
            self.__acceptedValue = value
        return rv

    def __init__ (self, wildcard_declaration, schema_location):
        super(WildcardUse, self).__init__()
        self.__wildcardDeclaration = wildcard_declaration
        self.__schemaLocation = schema_location


class ElementDeclaration (object):
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
        """Create an ElementDeclaration instance.

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
        super(ElementDeclaration, self).__init__()

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
        if ctd_instance._isNil():
            raise pyxb.ContentInNilInstanceError(ctd_instance, value)
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
        if ctd_instance._isNil():
            raise pyxb.ContentInNilInstanceError(ctd_instance, value)
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

        @raise pyxb.AbstractElementError: the binding to be used is abstract
        """
        if isinstance(value, basis._TypeBinding_mixin):
            element_binding = self.__elementBinding
            if value._substitutesFor(element_binding):
                element_binding = value._element()
            assert element_binding is not None
            if element_binding.abstract():
                raise pyxb.AbstractElementError(self, value)
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

    def _matches (self, value, element_decl):
        accept = False
        if element_decl == self:
            accept = True
        elif element_decl is not None:
            # If there's a known element, and it's not this one, the content
            # does not match.  This assumes we handled xsi:type and
            # substitution groups earlier, which may be true.
            accept = False
        elif isinstance(value, xml.dom.Node):
            # If we haven't been able to identify an element for this before,
            # then we don't recognize it, and will have to treat it as a
            # wildcard.
            accept = False
        else:
            # A foreign value which might be usable if we can convert
            # it to a compatible value trivially.
            try:
                value = self.__elementBinding.compatibleValue(value, _convert_string_values=False)
                accept = True
            except pyxb.SimpleTypeValueError:
                pass
        return (accept, value)

    def __str__ (self):
        return 'ED.%s@%x' % (self.__name, id(self))


class Wildcard (object):
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
        super(Wildcard, self).__init__()

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

## Local Variables:
## fill-column:78
## End:
    
