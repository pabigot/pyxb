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

"""This module contains support classes from which schema-specific bindings
inherit, and that describe the content models of those schema."""

import pyxb
import xml.dom as dom
import pyxb.utils.domutils as domutils
import pyxb.utils.utility as utility
import types
import pyxb.namespace

class _Binding_mixin (pyxb.cscRoot):
    """Mix-in used to identify classes that are bindings to some XML schema
    object.

    @todo: Define the process for providing a namespace context when creating
    documents from instances that were not created by CreateFromDOM.

    """

    _NamespaceCategory = None

    _ExpandedName = None
    """The expanded name of the component."""

    @classmethod
    def _IsSimpleTypeContent (cls):
        """Return True iff the content of this binding object is a simple type.

        This is true only for descendents of simpleTypeDefinition, instances
        of complexTypeDefinition that have simple type content, and elements
        with a type that is either one of those."""
        return False

    def _toDOM_vx (self, bds, parent):
        raise pyxb.LogicError('Class %s did not override _toDOM_vx' % (type(self),))

    def toDOM (self, bds=None):
        if bds is None:
            bds = domutils.BindingDOMSupport()
        if self._element() is not None:
            parent = bds.createChild(self._element().name().localName(), self._element().name().namespace())
        else:
            parent = bds.createChild(self._ExpandedName.localName(), self._ExpandedName.namespace())
        self._toDOM_vx(bds, parent)
        bds.finalize()
        return bds.document()

    def toxml (self, bds=None):
        """Shorthand to get the object as an XML document.

        If you want to set the default namespace, pass in a pre-configured
        C{bds}.

        @param bds: Optional L{pyxb.utils.domutils.BindingDOMSupport} instance
        to use for creation. If not provided (default), a new generic one is
        created.
        """
        return self.toDOM(bds).toxml()

    def _validateBinding_vx (self):
        raise pyxb.IncompleteImplementationError('%s did not override _validateBinding_vx' % (type(self),))

    def validateBinding (self):
        return self._validateBinding_vx()

class _TypeBinding_mixin (_Binding_mixin):

    # While simple type definitions cannot be abstract, they can appear in
    # many places where complex types can, so we want it to be legal to test
    # for abstractness without checking whether the object is a complex type.
    _Abstract = False

    def _namespaceContext (self):
        return self.__namespaceContext
    def _setNamespaceContext (self, namespace_context):
        self.__namespaceContext = namespace_context
        return self
    __namespaceContext = None

    @classmethod
    def _IsCompatibleValue (cls, instance):
        return isinstance(instance, cls) or issubclass(cls, type(instance))

    def _setElement (self, element):
        self.__element = element
        return self
    def _element (self):
        return self.__element
    __element = None

    @classmethod
    def _PreFactory_vx (cls, args, kw):
        """Method invoked upon entry to the Factory method.

        This method is entitled to modify the keywords array.  It can also
        return a state value which is passed to _postFactory_vx."""
        return None

    def _postFactory_vx (cls, state):
        """Method invoked prior to leaving the Factory method.

        This is an instance method, and is given the state that was returned
        by _PreFactory_vx."""
        return None

    @classmethod
    def Factory (cls, *args, **kw):
        """Provide a common mechanism to create new instances of this type.

        The class constructor won't do, because you can't create
        instances of union types.

        This method may be overridden in subclasses (like STD_union).

        @keyword _dom_node: If provided, the value must be a DOM node, the
        content of which will be used to set the value of the instance.

        @keyword _apply_whitespace_facet: If set to C{True} and this is a
        simpleTypeDefinition with a whiteSpace facet, the first argument will
        be normalized in accordance with that facet prior to invoking the
        parent constructor.

        """
        # Invoke _PreFactory_vx for the superseding class, which is where
        # customizations will be found.
        used_cls = cls._SupersedingClass()
        state = used_cls._PreFactory_vx(args, kw)
        rv = cls._DynamicCreate(*args, **kw)
        rv._postFactory_vx(state)
        return rv

class _DynamicCreate_mixin (pyxb.cscRoot):
    """Helper to allow overriding the implementation class.

    Generally we'll want to augment the generated bindings by subclassing
    them, and adding functionality to the subclass.  This mix-in provides a
    way to communicate the existence of the superseding subclass back to the
    binding infrastructure, so that when it creates an instance it uses the
    subclass rather than the unaugmented binding class.

    When a raw generated binding is subclassed, L{_SetSupersedingClass} should be
    invoked on the raw class passing in the superseding subclass.  E.g.::

      class mywsdl (raw.wsdl):
        pass
      raw.wsdl._SetSupersedingClass(mywsdl)

    """
    
    @classmethod
    def __SupersedingClassAttribute (cls):
        return '_%s__SupersedingClass' % (cls.__name__,)

    @classmethod
    def __AlternativeConstructorAttribute (cls):
        return '_%s__AlternativeConstructor' % (cls.__name__,)

    @classmethod
    def _SupersedingClass (cls):
        """Return the class stored in the class reference attribute."""
        return getattr(cls, cls.__SupersedingClassAttribute(), cls)

    @classmethod
    def _AlternativeConstructor (cls):
        """Return the class stored in the class reference attribute."""
        rv = getattr(cls, cls.__AlternativeConstructorAttribute(), None)
        if isinstance(rv, tuple):
            rv = rv[0]
        return rv

    @classmethod
    def _SetSupersedingClass (cls, superseding):
        """Set the class reference attribute.

        @param superseding: A Python class that is a subclass of this class.
        """
        assert (superseding is None) or issubclass(superseding, cls)
        if superseding is None:
            cls.__dict__.pop(cls.__SupersedingClassAttribute(), None)
        else:
            setattr(cls, cls.__SupersedingClassAttribute(), superseding)
        return superseding

    @classmethod
    def _SetAlternativeConstructor (cls, alternative_constructor):
        attr = cls.__AlternativeConstructorAttribute()
        if alternative_constructor is None:
            cls.__dict__.pop(attr, None)
        else:
            # Need to use a tuple as the value: if you use an invokable, this
            # ends up converting it from a function to an unbound method,
            # which is not what we want.
            setattr(cls, attr, (alternative_constructor,))
        assert cls._AlternativeConstructor() == alternative_constructor
        return alternative_constructor

    @classmethod
    def _DynamicCreate (cls, *args, **kw):
        """Invoke the constructor for this class or the one that supersedes it."""
        ctor = cls._AlternativeConstructor()
        if ctor is None:
            ctor = cls._SupersedingClass()
        return ctor(*args, **kw)

class simpleTypeDefinition (_TypeBinding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """L{simpleTypeDefinition} is a base class that is part of the
    hierarchy of any class that represents the Python datatype for a
    L{SimpleTypeDefinition<pyxb.xmlschema.structures.SimpleTypeDefinition>}.

    @note: This class, or a descendent of it, must be the first class
    in the method resolution order when a subclass has multiple
    parents.  Otherwise, constructor keyword arguments may not be
    removed before passing them on to Python classes that do not
    accept them.
    """

    _NamespaceCategory = 'typeBinding'

    # A map from leaf classes in the facets module to instance of
    # those classes that constrain or otherwise affect the datatype.
    # Note that each descendent of simpleTypeDefinition has its own map.
    __FacetMap = {}

    _ReservedSymbols = set([ 'Factory', 'XsdLiteral', 'xsdLiteral',
                            'XsdSuperType', 'XsdPythonType', 'XsdConstraintsOK',
                            'xsdConstraintsOK', 'XsdValueLength', 'xsdValueLength',
                            'PythonLiteral', 'pythonLiteral', 'toDOM' ])
    """Symbols that remain the responsibility of this class.  Any
    public symbols in generated binding subclasses are deconflicted
    by providing an alternative name in the subclass.  (There
    currently are no public symbols in generated SimpleTypeDefinion
    bindings."""


    # Determine the name of the class-private facet map.  For the base class
    # this should produce the same attribute name as Python's privatization
    # scheme.
    @classmethod
    def __FacetMapAttributeName (cls):
        if cls == simpleTypeDefinition:
            return '_%s__FacetMap' % (cls.__name__.strip('_'),)

        # It is not uncommon for a class in one namespace to extend a class of
        # the same name in a different namespace, so encode the namespace URI
        # in the attribute name (if it is part of a namespace).
        ns_uri = ''
        try:
            ns_uri = cls._ExpandedName.namespaceURI()
        except Exception, e:
            pass
        nm = '_' + utility.MakeIdentifier('%s_%s_FacetMap' % (ns_uri, cls.__name__.strip('_')))
        return nm
        

    @classmethod
    def _FacetMap (cls):
        """Return a reference to the facet map for this datatype.

        The facet map is a map from leaf facet classes to instances of those
        classes that constrain or otherwise apply to the lexical or value
        space of the datatype.  Classes may inherit their facet map from their
        superclass, or may create a new class instance if the class adds a new
        constraint type.

        :raise AttributeError: if the facet map has not been defined"""
        return getattr(cls, cls.__FacetMapAttributeName())
    
    @classmethod
    def _InitializeFacetMap (cls, *args):
        """Initialize the facet map for this datatype.

        This must be called exactly once, after all facets belonging to the
        datatype have been created.

        :raise pyxb.LogicError: if called multiple times (on the same class)
        :raise pyxb.LogicError: if called when a parent class facet map has not been initialized
        :return: the facet map"""
        fm = None
        try:
            fm = cls._FacetMap()
        except AttributeError:
            pass
        if fm is not None:
            raise pyxb.LogicError('%s facet map initialized multiple times: %s' % (cls.__name__,cls.__FacetMapAttributeName()))

        # Search up the type hierarchy to find the nearest ancestor that has a
        # facet map.  This gets a bit tricky: if we hit the ceiling early
        # because the PSTD hierarchy re-based itself on a new Python type, we
        # have to jump to the XsdSuperType.
        source_class = cls
        while fm is None:
            # Assume we're staying in this hierarchy.  Include source_class in
            # the candidates, since we might have jumped to it.
            for super_class in source_class.mro():
                #print 'Superclass for %s is %s' % (source_class, super_class)
                assert super_class is not None
                if (super_class == simpleTypeDefinition): # and (source_class.XsdSuperType() is not None):
                    break
                if issubclass(super_class, simpleTypeDefinition):
                    try:
                        fm = super_class._FacetMap()
                        #print 'Selected facet map for %s from %s: %s' % (cls, super_class, fm)
                        break
                    except AttributeError:
                        pass
            if fm is None:
                try:
                    source_class = source_class.XsdSuperType()
                except AttributeError:
                    source_class = None
                #print 'Nothing acceptable found, jumped to %s' % (source_class,)
                if source_class is None:
                    fm = { }
        #print 'Done with set'
        if fm is None:
            raise pyxb.LogicError('%s is not a child of simpleTypeDefinition' % (cls.__name__,))
        fm = fm.copy()
        #print 'Augmenting %s map had %d elts with %d from args' % (cls, len(fm), len(args))
        for facet in args:
            fm[type(facet)] = facet
        #for (fc, fi) in fm.items():
        #    print ' %s : %s' % (fc, fi)
        setattr(cls, cls.__FacetMapAttributeName(), fm)
        return fm

    @classmethod
    def __ApplyWhitespaceToFirstArgument (cls, args):
        """If the first argument is a string, and this class has a whitespace
        facet, replace the first argument with the results of applying
        whitespace normalization.

        We need to do this for both __new__ and __init__, because in some
        cases (e.g., str/unicode) the value is assigned during __new__ not
        __init__."""
        if (0 < len(args)) and isinstance(args[0], types.StringTypes):
            cf_whitespace = getattr(cls, '_CF_whiteSpace', None)
            if cf_whitespace is not None:
                norm_str = unicode(cf_whitespace.normalizeString(args[0]))
                args = (norm_str,) + args[1:]
        return args

    @classmethod
    def _ConvertArguments (cls, args, kw):
        """Pre-process the arguments.

        This is used before invoking the parent constructor.  One application
        is to apply the whitespace facet processing; if such a request is in
        the keywords, it is removed so it does not propagate to the
        superclass.  Another application is to convert the arguments from a
        string to a list."""
        dom_node = kw.pop('_dom_node', None)
        if dom_node is not None:
            args = (domutils.ExtractTextContent(dom_node),) + args
            kw['_apply_whitespace_facet'] = True
        apply_whitespace_facet = kw.pop('_apply_whitespace_facet', False)
        if apply_whitespace_facet:
            args = cls.__ApplyWhitespaceToFirstArgument(args)
        if issubclass(cls, STD_list):
            # If the first argument is a string, split it on spaces
            # and use the resulting list of tokens.
            if 0 < len(args):
                arg1 = args[0]
                if isinstance(arg1, types.StringTypes):
                    args = (arg1.split(),) + args[1:]
        return args

    # Must override new, because new gets invoked before init, and
    # usually doesn't accept keywords.  In case it does, only remove
    # the ones that are interpreted by this class.  Do the same
    # argument conversion as is done in init.  Trap errors and convert
    # them to BadTypeValue errors.
    #
    # Note: We explicitly do not validate constraints here.  That's
    # done in the normal constructor; here, we might be in the process
    # of building a value that eventually will be legal, but isn't
    # yet.
    def __new__ (cls, *args, **kw):
        kw.pop('_validate_constraints', None)
        args = cls._ConvertArguments(args, kw)
        try:
            return super(simpleTypeDefinition, cls).__new__(cls, *args, **kw)
        except ValueError, e:
            raise pyxb.BadTypeValueError(e)
        except OverflowError, e:
            raise pyxb.BadTypeValueError(e)

    # Validate the constraints after invoking the parent constructor,
    # unless told not to.
    def __init__ (self, *args, **kw):
        """Initialize a newly created STD instance.
        
        Usually there is one positional argument, which is a value that can be
        converted to the underlying Python type.

        Keyword arguments:
        _validate_constraints -- Validate the datatype constraints after initialization (default True)
        """
        validate_constraints = kw.pop('_validate_constraints', True)
        args = self._ConvertArguments(args, kw)
        try:
            super(simpleTypeDefinition, self).__init__(*args, **kw)
        except OverflowError, e:
            raise pyxb.BadTypeValueError(e)
        if validate_constraints:
            self.xsdConstraintsOK()

    # The class attribute name used to store the reference to the STD
    # component instance must be unique to the class, not to this base class.
    # Otherwise we mistakenly believe we've already associated a STD instance
    # with a class (e.g., xsd:normalizedString) when in fact it's associated
    # with the superclass (e.g., xsd:string)
    @classmethod
    def __STDAttrName (cls):
        return '_%s__SimpleTypeDefinition' % (cls.__name__,)

    @classmethod
    def _SimpleTypeDefinition (cls, std):
        attr_name = cls.__STDAttrName()
        if hasattr(cls, attr_name):
            old_value = getattr(cls, attr_name)
            if old_value != std:
                raise pyxb.LogicError('%s: Attempt to override existing STD %s with %s' % (cls, old_value.name(), std.name()))
        setattr(cls, attr_name, std)

    @classmethod
    def SimpleTypeDefinition (cls):
        """Return the SimpleTypeDefinition instance for the given
        class.

        This should only be invoked when generating bindings.  Raise
        pyxb.IncompleteImplementationError if no STD instance has been
        associated with the class."""
        attr_name = cls.__STDAttrName()
        if hasattr(cls, attr_name):
            return getattr(cls, attr_name)
        raise pyxb.IncompleteImplementationError('%s: No STD available' % (cls,))

    @classmethod
    def XsdLiteral (cls, value):
        """Convert from a python value to a string usable in an XML
        document.

        This should be implemented in the subclass."""
        raise pyxb.LogicError('%s does not implement XsdLiteral' % (cls,))

    def xsdLiteral (self):
        """Return text suitable for representing the value of this
        instance in an XML document.

        The base class implementation delegates to the object class's
        XsdLiteral method."""
        return self.XsdLiteral(self)

    @classmethod
    def XsdSuperType (cls):
        """Find the nearest parent class in the PST hierarchy.

        The value for anySimpleType is None; for all others, it's a
        primitive or derived PST descendent (including anySimpleType)."""
        for sc in cls.mro():
            if sc == cls:
                continue
            if simpleTypeDefinition == sc:
                # If we hit the PST base, this is a primitive type or
                # otherwise directly descends from a Python type; return
                # the recorded XSD supertype.
                return cls._XsdBaseType
            if issubclass(sc, simpleTypeDefinition):
                return sc
        raise pyxb.LogicError('No supertype found for %s' % (cls,))

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Pre-extended class method to verify other things before
        checking constraints.

        This is used for list types, to verify that the values in the
        list are acceptable, and for token descendents, to check the
        lexical/value space conformance of the input.
        """
        super_fn = getattr(super(simpleTypeDefinition, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: value)
        return super_fn(value)

    @classmethod
    def XsdConstraintsOK (cls, value):
        """Validate the given value against the constraints on this class.

        Throws pyxb.BadTypeValueError if any constraint is violated.
        """

        value = cls._XsdConstraintsPreCheck_vb(value)

        facet_values = None

        # When setting up the datatypes, if we attempt to validate
        # something before the facets have been initialized (e.g., a
        # nonNegativeInteger used as a length facet for the parent
        # integer datatype), just ignore that.
        try:
            facet_values = cls._FacetMap().values()
        except AttributeError:
            return value
        for f in facet_values:
            if not f.validateConstraint(value):
                raise pyxb.BadTypeValueError('%s violation for %s in %s' % (f.Name(), value, cls.__name__))
            #print '%s ok for %s' % (f, value)
        return None

    def xsdConstraintsOK (self):
        """Validate the value of this instance against its constraints."""
        return self.XsdConstraintsOK(self)

    def _validateBinding_vx (self):
        self.xsdConstraintsOK()

    @classmethod
    def XsdValueLength (cls, value):
        """Return the length of the given value.

        The length is calculated by a subclass implementation of
        _XsdValueLength_vx in accordance with
        http://www.w3.org/TR/xmlschema-2/#rf-length.

        The return value is a non-negative integer, or None if length
        constraints should be considered trivially satisfied (as with
        QName and NOTATION).

        :raise pyxb.LogicError: the provided value is not an instance of cls.
        :raise pyxb.LogicError: an attempt is made to calculate a length for
        an instance of a type that does not support length calculations.
        """
        assert isinstance(value, cls)
        if not hasattr(cls, '_XsdValueLength_vx'):
            raise pyxb.LogicError('Class %s does not support length validation' % (cls.__name__,))
        return cls._XsdValueLength_vx(value)

    def xsdValueLength (self):
        """Return the length of this instance within its value space.

        See XsdValueLength."""
        return self.XsdValueLength(self)

    @classmethod
    def PythonLiteral (cls, value):
        """Return a string which can be embedded into Python source to
        represent the given value as an instance of this class."""
        class_name = cls.__name__
        return '%s(%s)' % (class_name, repr(value))

    def pythonLiteral (self):
        """Return a string which can be embedded into Python source to
        represent the value of this instance."""
        return self.PythonLiteral(self)

    def _toDOM_vx (self, dom_support, parent):
        assert parent is not None
        parent.appendChild(dom_support.document().createTextNode(self.xsdLiteral()))
        return dom_support

    @classmethod
    def _IsSimpleTypeContent (cls):
        """STDs have simple type content."""
        return True

class STD_union (simpleTypeDefinition):
    """Base class for union datatypes.

    This class descends only from simpleTypeDefinition.  A pyxb.LogicError is
    raised if an attempt is made to construct an instance of a subclass of
    STD_union.  Values consistent with the member types are constructed using
    the Factory class method.  Values are validated using the _ValidateMember
    class method.

    Subclasses must provide a class variable _MemberTypes which is a
    tuple of legal members of the union."""

    _MemberTypes = None
    """A list of classes which are permitted as values of the union."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from simpleTypeDefinition.
    # @todo Ensure that pattern and enumeration are valid constraints
    __FacetMap = {}

    # Filter arguments out from call to new to avoid deprecation
    # warning in Python 2.6.
    def __new__ (cls, *args, **kw):
        return super(STD_union, cls).__new__(cls)

    @classmethod
    def Factory (cls, *args, **kw):
        """Given a value, attempt to create an instance of some member of this
        union.  The first instance which can be legally created is returned.

        @keyword _validate_constraints: If True (default), any constructed
        value is checked against constraints applied to the union as well as
        the member type.

        @raise pyxb.BadTypeValueError: no member type will permit creation of
        an instance from the parameters in C{args} and C{kw}.
        """
        rv = None
        # NB: get, not pop: preserve it for the member type invocations
        validate_constraints = kw.get('_validate_constraints', True)
        for mt in cls._MemberTypes:
            try:
                rv = mt.Factory(*args, **kw)
                break
            except pyxb.BadTypeValueError:
                pass
            except ValueError:
                pass
            except:
                pass
        if rv is not None:
            if validate_constraints:
                cls.XsdConstraintsOK(rv)
            return rv
        raise pyxb.BadTypeValueError('%s cannot construct union member from args %s' % (cls.__name__, args))

    @classmethod
    def _ValidateMember (cls, value):
        """Validate the given value as a potential union member.

        Raises pyxb.BadTypeValueError if the value is not an instance of a
        member type."""
        if not isinstance(value, cls._MemberTypes):
            for mt in cls._MemberTypes:
                try:
                    value = mt(value)
                    return value
                except pyxb.BadTypeValueError:
                    pass
            raise pyxb.BadTypeValueError('%s cannot hold a member of type %s' % (cls.__name__, value.__class__.__name__))
        return value

    def __init__ (self, *args, **kw):
        raise pyxb.LogicError('%s: cannot construct instances of union' % (self.__class__.__name__,))

class STD_list (simpleTypeDefinition, types.ListType):
    """Base class for collection datatypes.

    This class descends from the Python list type, and incorporates
    simpleTypeDefinition.  Subclasses must define a class variable _ItemType
    which is a reference to the class of which members must be instances."""

    _ItemType = None
    """A reference to the binding class for items within this list."""

    # Ick: If we don't declare this here, this class's map doesn't get
    # initialized.  Alternative is to not descend from simpleTypeDefinition.
    __FacetMap = {}

    @classmethod
    def _ValidateItem (cls, value):
        """Verify that the given value is permitted as an item of this list.

        This may convert the value to the proper type, if it is
        compatible but not an instance of the item type.  Returns the
        value that should be used as the item, or raises an exception
        if the value cannot be converted."""
        if isinstance(value, cls):
            pass
        elif issubclass(cls._ItemType, STD_union):
            value = cls._ItemType._ValidateMember(value)
        else:
            if not isinstance(value, cls._ItemType):
                try:
                    value = cls._ItemType(value)
                except pyxb.BadTypeValueError:
                    raise pyxb.BadTypeValueError('Type %s has member of type %s, must be %s' % (cls.__name__, type(value).__name__, cls._ItemType.__name__))
        return value

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        """Verify that the items in the list are acceptable members."""
        assert isinstance(value, cls)
        for i in range(len(value)):
            value[i] = cls._ValidateItem(value[i])
        super_fn = getattr(super(STD_list, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: value)
        return super_fn(value)

    @classmethod
    def _XsdValueLength_vx (cls, value):
        return len(value)

    @classmethod
    def XsdLiteral (cls, value):
        """Convert from a binding value to a string usable in an XML document."""
        return ' '.join([ _v.xsdLiteral() for _v in value ])

class element (_Binding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """Class that represents a schema element.

    Both global and local elements are represented by an instance of this
    class.
    """

    _NamespaceCategory = 'elementBinding'

    # Reference to the simple or complex type binding that serves as
    # the content of this element.
    # MUST BE SET IN SUBCLASS
    _typeDefinition = None
    """The subclass of complexTypeDefinition that is used to represent content in this element."""

    def name (self):
        return self.__name
    __name = None

    def typeDefinition (self):
        return self.__typeDefinition
    __typeDefinition = None

    def scope (self):
        return self.__scope
    __scope = None

    def nillable (self):
        return self.__nillable
    __nillable = False

    def abstract (self):
        return self.__abstract
    __abstract = False

    def defaultValue (self):
        return self.__defaultValue
    __defaultValue = None

    def substitutionGroup (self):
        return self.__substitutionGroup
    __substitutionGroup = None

    def memberElement (self, name):
        """Return a reference to the element instance used for the given name
        within this element.

        The type for this element must be a complex type definition."""
        return self.typeDefinition()._UseForTag(name).elementBinding()

    def __create (self, use_type=None, *args, **kw):
        if use_type is None:
            use_type = self.typeDefinition()
        return use_type.Factory(*args, **kw)

    def __init__ (self, name, type_definition, scope=None, nillable=False, abstract=False, default_value=None, substitution_group=None):
        """Create a new element binding.
        """
        assert isinstance(name, pyxb.namespace.ExpandedName)
        self.__name = name
        self.__typeDefinition = type_definition
        self.__scope = scope
        self.__nillable = nillable
        self.__abstract = abstract
        self.__defaultValue = default_value
        self.__substitutionGroup = substitution_group
        
    def __call__ (self, *args, **kw):
        dom_node = kw.pop('_dom_node', None)
        if dom_node is not None:
            return self.createFromDOM(dom_node, **kw)
        return self.typeDefinition().Factory(*args,**kw)._setElement(self)

    def valueIfCompatible (self, value):
        if value is None:
            return None
        if isinstance(value, self.typeDefinition()):
            return value
        value_type = type(value)
        if str == value_type:
            value_type = unicode
        if issubclass(self.typeDefinition(), value_type):
            #print 'Compatibility OK for %s as %s for %s' % (value, value_type, self.typeDefinition())
            try:
                return self(value)
            except pyxb.BadTypeValueError, e:
                pass
        #print 'Compatibility failed with %s as %s for %s' % (value, value_type, self.typeDefinition())
        return None

    # element
    @classmethod
    def AnyCreateFromDOM (cls, node, fallback_namespace):
        expanded_name = pyxb.namespace.ExpandedName(node, fallback_namespace=fallback_namespace)
        elt = expanded_name.elementBinding()
        if elt is None:
            raise pyxb.UnrecognizedElementError('No element binding available for %s' % (expanded_name,))
        assert isinstance(elt, pyxb.binding.basis.element)
        return elt.createFromDOM(node)
        
    def createFromDOM (self, node, **kw):
        """Create an instance of this element from the given DOM node.

        :raise pyxb.LogicError: the name of the node is not consistent with
        the _ExpandedName of this class."""

        # Identify the element binding to be used for the given node.  In the
        # case of substitution groups, it may not be what we expect.
        elt_ns = self.__name.namespace()
        if self.scope() is None:
            node_elt = pyxb.namespace.ExpandedName(node, fallback_namespace=elt_ns).elementBinding()
            assert self == node_elt, 'Node %s self %s node_elt %s' % (node, self, node_elt)

        # Now determine the type binding for the content.  If xsi:type is
        # used, it won't be the one built into the element binding.
        type_class = self.typeDefinition()
        xsi_type = pyxb.namespace.ExpandedName(pyxb.namespace.XMLSchema_instance, 'type')
        type_name = xsi_type.getAttribute(node)
        ns_ctx = pyxb.namespace.NamespaceContext.GetNodeContext(node, target_namespace=elt_ns, default_namespace=elt_ns)
        if type_name is not None:
            # xsi:type should only be provided when using an abstract class
            if not (issubclass(type_class, complexTypeDefinition) and type_class._Abstract):
                raise pyxb.BadDocumentError('%s attribute on element with non-abstract type' % (xsi_type,))
            # Get the node context.  In case none has been assigned, create
            # it, using the element namespace as the default environment
            # (since we only need this in order to resolve the xsi:type qname,
            # that should be okay, right?)  @todo: verify this
            assert ns_ctx
            type_name = ns_ctx.interpretQName(type_name)
            alternative_type_class = type_name.typeBinding()
            if not issubclass(alternative_type_class, type_class):
                raise pyxb.BadDocumentError('%s value %s is not subclass of element type %s' % (xsi_type, type_name, type_class._ExpandedName))
            type_class = alternative_type_class
            
        rv = type_class.Factory(_dom_node=node, **kw)
        rv._setElement(self)
        rv._setNamespaceContext(ns_ctx)
        return rv

    def _toDOM_vx (self, dom_support, parent):
        """Add a DOM representation of this element as a child of
        parent, which should be a DOM Node instance."""
        assert isinstance(dom_support, domutils.BindingDOMSupport)
        element = dom_support.createChild(self._ExpandedName.localName(), self._ExpandedName.namespace(), parent)
        self.__realContent._toDOM_vx(dom_support, parent=element)
        return dom_support

    def __str__ (self):
        return 'Element %s' % (self.name(),)

class enumeration_mixin (pyxb.cscRoot):
    """Marker in case we need to know that a PST has an enumeration constraint facet."""
    pass

class complexTypeDefinition (_TypeBinding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType.

    Subclasses should define a class-level _AttributeMap variable which maps
    from the unicode tag of an attribute to the AttributeUse instance that
    defines it.  Similarly, subclasses should define an _ElementMap variable.
    """

    _NamespaceCategory = 'typeBinding'

    _CT_EMPTY = 'EMPTY'                 #<<< No content
    _CT_SIMPLE = 'SIMPLE'               #<<< Simple (character) content
    _CT_MIXED = 'MIXED'                 #<<< Children may be elements or other (e.g., character) content
    _CT_ELEMENT_ONLY = 'ELEMENT_ONLY'   #<<< Expect only element content.

    _ContentType = None

    _TypeDefinition = None
    """Subclass of simpleTypeDefinition that corresponds to the type content.
    Only valid if _ContentType is _CT_SIMPLE"""

    # If the type supports wildcard attributes, this describes their
    # constraints.  (If it doesn't, this should remain None.)  Supporting
    # classes should override this value.
    _AttributeWildcard = None

    _AttributeMap = { }
    """Map from expanded names to AttributeUse instances."""

    # A value that indicates whether the content model for this type supports
    # wildcard elements.  Supporting classes should override this value.
    _HasWildcardElement = False

    # Map from expanded names to ElementUse instances
    _ElementMap = { }
    """Map from expanded names to ElementUse instances."""

    # Per-instance map from tags to attribute values for wildcard attributes.
    # Value is None if the type does not support wildcard attributes.
    __wildcardAttributeMap = None

    def wildcardAttributeMap (self):
        """Obtain access to wildcard attributes.

        The return value is None if this type does not support wildcard
        attributes.  If wildcard attributes are allowed, the return value is a
        map from QNames to the unicode string value of the corresponding
        attribute.

        @todo: The map keys should be namespace extended names rather than
        QNames, as the in-scope namespace may not be readily available to the
        user.
        """
        return self.__wildcardAttributeMap

    # Per-instance list of DOM nodes interpreted as wildcard elements.
    # Value is None if the type does not support wildcard elements.
    __wildcardElements = None

    def wildcardElements (self):
        """Obtain access to wildcard elements.

        The return value is None if the content model for this type does not
        support wildcard elements.  If wildcard elements are allowed, the
        return value is a list of DOM Element nodes corresponding to
        conformant unrecognized elements, in the order in which they were
        encountered."""
        return self.__wildcardElements

    def __init__ (self, *args, **kw):
        dom_node = kw.pop('_dom_node', None)
        if dom_node is not None:
            kw['_validate_constraints'] = False
        if self._AttributeWildcard is not None:
            self.__wildcardAttributeMap = { }
        if self._HasWildcardElement:
            self.__wildcardElements = []
        if self._Abstract:
            raise pyxb.AbstractInstantiationError(type(self))
        super(complexTypeDefinition, self).__init__(**kw)
        self.reset()
        if self._CT_SIMPLE == self._ContentTypeTag:
            self.__setContent(self._TypeDefinition.Factory(_dom_node=dom_node, *args, **kw))
        # Extract keywords that match field names
        attribute_settings = { }
        if dom_node is not None:
            attribute_settings.update(self.__AttributesFromDOM(dom_node))
        for fu in self._AttributeMap.values():
            iv = kw.get(fu.id())
            if iv is not None:
                attribute_settings[fu.name()] = iv
        self.__setAttributes(attribute_settings, dom_node)
        for fu in self._ElementMap.values():
            iv = kw.get(fu.id())
            if iv is not None:
                if isinstance(iv, list):
                    assert fu.isPlural()
                    [ fu.append(self, _elt) for _elt in iv ]
                else:
                    fu.set(self, iv)
        if dom_node is not None:
            self._setContentFromDOM(dom_node)
        elif 0 < len(args):
            self.extend(args)

    # Specify the symbols to be reserved for all CTDs.
    _ReservedSymbols = set([ 'Factory', 'toDOM', 'wildcardElements', 'wildcardAttributeMap',
                             'xsdConstraintsOK', 'content' ])

    # None, or a reference to a ContentModel instance that defines how to
    # reduce a DOM node list to the body of this element.
    _ContentModel = None

    @classmethod
    def _AddElement (cls, element):
        return cls._UseForTag(element.name())._setElementBinding(element)

    @classmethod
    def _UseForTag (cls, tag):
        """Return the ElementUse object corresponding to the element name.

        :param tag: The L{ExpandedName} of an element in the class."""
        rv = cls._ElementMap.get(tag)
        if rv is None:
            raise pyxb.LogicError('Unable to locate element %s in type %s' % (tag, cls._ExpandedName))
        return rv

    def __childrenForDOM (self):
        """Generate a list of children in the order in which they should be
        added to the parent when creating a DOM representation of this
        object."""
        order = []
        for eu in self._ElementMap.values():
            value = eu.value(self)
            if value is None:
                continue
            if isinstance(value, list):
                order.extend([ (eu, _v) for _v in value ])
                continue
            order.append( (eu, value) )
        return order

    def _validatedChildren (self):
        assert self._ContentModel is not None
        matches = self._ContentModel.validate(self._symbolSet())
        if 0 < len(matches):
            ( symbols, sequence ) = matches[0]
            if 0 == len(symbols):
                return sequence
            raise pyxb.BindingValidationError('Ungenerated symbols: %s' % (symbols,) )
        return None

    def _symbolSet (self):
        rv = { }
        for eu in self._ElementMap.values():
            value = eu.value(self)
            if value is None:
                continue
            if not isinstance(value, list):
                rv[eu] = [ value ]
            elif 0 < len(value):
                rv[eu] = value[:]
        wce = self.wildcardElements()
        if (wce is not None) and (0 < len(wce)):
            rv[None] = wce
        return rv

    def _validateBinding_vx (self):
        order = self._validatedChildren()
        if order is None:
            raise pyxb.BindingValidationError('No match from content to binding model')
        for (eu, value) in order:
            if isinstance(value, _Binding_mixin):
                value.validateBinding()
            else:
                print 'WARNING: Cannot validate value %s in field %s' % (value, eu.id())

    @classmethod
    def __AttributesFromDOM (cls, node):
        attribute_settings = { }
        for ai in range(0, node.attributes.length):
            attr = node.attributes.item(ai)
            attr_en = pyxb.namespace.ExpandedName(attr)

            # Ignore xmlns and xsi attributes; we've already handled those
            if attr_en.namespace() in ( pyxb.namespace.XMLNamespaces, pyxb.namespace.XMLSchema_instance ):
                continue

            value = attr.value
            au = cls._AttributeMap.get(attr_en)
            if au is None:
                if cls._AttributeWildcard is None:
                    raise pyxb.UnrecognizedAttributeError('Attribute %s is not permitted in type %s' % (attr_en, cls._ExpandedName))
            attribute_settings[attr_en] = value
        return attribute_settings

    def __setAttributes (self, attribute_settings, dom_node):
        """Initialize the attributes of this element from those of the DOM node.

        Raises pyxb.UnrecognizedAttributeError if the DOM node has attributes
        that are not allowed in this type.  May raise other errors if
        prohibited or required attributes are or are not present."""
        
        # Handle all the attributes that are present in the node
        attrs_available = set(self._AttributeMap.values())
        for (attr_en, value) in attribute_settings.items():
            au = self._AttributeMap.get(attr_en, None)
            if au is None:
                if self._AttributeWildcard is None:
                    raise pyxb.UnrecognizedAttributeError('Attribute %s is not permitted in type %s' % (attr_en, self._ExpandedName))
                self.__wildcardAttributeMap[attr_en] = value
                continue
            au.set(self, value)
            attrs_available.remove(au)

        # Handle all the ones that aren't present.  NB: Don't just reset the
        # attribute; we need to check for missing ones, which is done by
        # au.set.
        if dom_node is not None:
            for au in attrs_available:
                au.set(self, dom_node)
        return self

    def xsdConstraintsOK (self):
        # @todo: type check
        return self.content().xsdConstraintsOK()

    __content = None
    def content (self):
        if self._CT_EMPTY == self._ContentTypeTag:
            # @todo: raise exception
            pass
        return self.__content

    __dfaStack = None
    def reset (self):
        if self._ContentTypeTag in (self._CT_MIXED, self._CT_ELEMENT_ONLY):
            self.__setContent([])
        for au in self._AttributeMap.values():
            au.reset(self)
        for eu in self._ElementMap.values():
            eu.reset(self)
        if self._ContentModel is not None:
            self.__dfaStack = self._ContentModel.initialDFAStack(self)
        return self

    def append (self, value):
        if isinstance(value, dom.Node):
            if dom.Node.COMMENT_NODE == value.nodeType:
                return self
            if value.nodeType in (dom.Node.TEXT_NODE, dom.Node.CDATA_SECTION_NODE):
                if self.__isMixed:
                    self._addContent(value.data)
                else:
                    #print 'Ignoring mixed content'
                    pass
                return self
            # Do type conversion here
            value = value
        if self.__dfaStack is not None:
            if not self.__dfaStack.step(self, value):
                raise pyxb.ExtraContentError('Extra content starting with %s' % (value,))
        return self

    def extend (self, value_list):
        [ self.append(_v) for _v in value_list ]
        return self

    def __setContent (self, value):
        self.__content = value

    def _addContent (self, child):
        assert isinstance(child, _Binding_mixin) or isinstance(child, types.StringTypes), 'Unrecognized child %s type %s' % (child, type(child))
        self.__content.append(child)

    __isMixed = False
    def _setContentFromDOM (self, node):
        """Initialize the content of this element from the content of the DOM node."""
        if self._CT_EMPTY == self._ContentTypeTag:
            return
        if self._CT_SIMPLE == self._ContentTypeTag:
            self.__setContent(self._TypeDefinition.Factory(_dom_node=node))
            self.xsdConstraintsOK()
            return
        self.__isMixed = (self._CT_MIXED == self._ContentTypeTag)
        self.extend(node.childNodes[:])
        if (self.__dfaStack is not None) and not self.__dfaStack.isTerminal():
            raise pyxb.MissingContentError()
        return self

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeMap.values():
            au.addDOMAttribute(self, element)
        return element

    def _toDOM_vx (self, dom_support, parent):
        """Create a DOM element with the given tag holding the content of this instance."""
        element = parent
        self._setDOMFromAttributes(element)
        if self._CT_EMPTY == self._ContentTypeTag:
            return
        if self._CT_SIMPLE == self._ContentTypeTag:
            return element.appendChild(dom_support.document().createTextNode(self.content().xsdLiteral()))
        order = self._validatedChildren()
        if order is None:
            raise pyxb.DOMGenerationError('Binding value inconsistent with content model')
        for (eu, v) in order:
            assert v != self
            if eu is None:
                print 'IGNORING wildcard generation'
            else:
                eu.toDOM(dom_support, parent, v)
        mixed_content = self.content()
        for mc in mixed_content:
            #print 'Skipping mixed content %s' % (mc,)
            pass
            #if isinstance(mc, types.StringTypes):
            #    element.appendChild(dom_support.document().createTextNode(mc))
        return dom_support

    @classmethod
    def _IsSimpleTypeContent (cls):
        """CTDs with simple content are simple"""
        return cls._CT_SIMPLE == cls._ContentTypeTag

## Local Variables:
## fill-column:78
## End:
    
