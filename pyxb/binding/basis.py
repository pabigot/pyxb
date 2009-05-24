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
import pyxb.Namespace

class _Binding_mixin (pyxb.cscRoot):
    """Mix-in used to identify classes that are bindings to some XML schema
    object.

    @todo: Hide (or remove) domNode, leaving only namespaceContext visible.
    Define the process for providing a namespace context when creating
    documents from instances that were not created by CreateFromDOM.

    """

    _Namespace = None
    """The namespace to which the component belongs."""

    _XsdName = None
    """The name of the component within its namespace category."""

    def _domNode (self):
        """The DOM node from which the object was initialized."""
        return self.__domNode
    __domNode = None

    def _namespaceContext (self):
        """The namespace context applicable to the object."""
        return pyxb.Namespace.NamespaceContext.GetNodeContext(self.__domNode)
    
    def _instanceRoot (self):
        return self.__instanceRoot

    def _setBindingContext (self, node, instance_root):
        self.__domNode = node
        self.__instanceRoot = instance_root

    @classmethod
    def _IsSimpleTypeContent (cls):
        """Return True iff the content of this binding object is a simple type.

        This is true only for descendents of simpleTypeDefinition, instances
        of complexTypeDefinition that have simple type content, and elements
        with a type that is either one of those."""
        return False

    def toxml (self):
        """Shorthand to get the object as an XML document."""
        bds = domutils.BindingDOMSupport()
        self.toDOM(bds)
        bds.finalize()
        return bds.document().toxml()

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
    def _SupersedingClass (cls):
        """Return the class stored in the class reference attribute."""
        return getattr(cls, cls.__SupersedingClassAttribute(), cls)

    @classmethod
    def _SetSupersedingClass (cls, superseding):
        """Set the class reference attribute.

        @param superseding: A Python class that is a subclass of this class.
        """
        assert (superseding is None) or issubclass(superseding, cls)
        if superseding is None:
            self.__dict__.pop(cls.__SupersedingClassAttribute(), None)
        else:
            setattr(cls, cls.__SupersedingClassAttribute(), superseding)
        return superseding

    @classmethod
    def _DynamicCreate (cls, *args, **kw):
        """Invoke the constructor for the class that supersedes this one."""
        return cls._SupersedingClass()(*args, **kw)

class simpleTypeDefinition (_Binding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """L{simpleTypeDefinition} is a base class that is part of the
    hierarchy of any class that represents the Python datatype for a
    L{SimpleTypeDefinition<pyxb.xmlschema.structures.SimpleTypeDefinition>}.

    @note: This class, or a descendent of it, must be the first class
    in the method resolution order when a subclass has multiple
    parents.  Otherwise, constructor keyword arguments may not be
    removed before passing them on to Python classes that do not
    accept them.
    """

    # A map from leaf classes in the facets module to instance of
    # those classes that constrain or otherwise affect the datatype.
    # Note that each descendent of simpleTypeDefinition has its own map.
    __FacetMap = {}

    _ReservedSymbols = set([ 'Factory', 'CreateFromDOM', 'XsdLiteral', 'xsdLiteral',
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
        ns = ''
        try:
            ns = cls._Namespace.uri()
        except Exception, e:
            pass
        nm = '_' + utility.MakeIdentifier('%s_%s_FacetMap' % (ns, cls.__name__.strip('_')))
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
    def __ConvertArgs (cls, args):
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
        apply_whitespace_facet = kw.pop('apply_whitespace_facet', False)
        if apply_whitespace_facet:
            args = cls.__ConvertArgs(args)
        if issubclass(cls, STD_list):
            # If the first argument is a string, split it on spaces
            # and use the resulting list of tokens.
            if 0 < len(args):
                arg1 = args[0]
                if isinstance(arg1, types.StringTypes):
                    args = (arg1.split(),) +  args[1:]
        return args

    @classmethod
    def Factory (cls, *args, **kw):
        """Provide a common mechanism to create new instances of this type.

        The class constructor won't do, because you can't create
        instances of union types.

        This method may be overridden in subclasses (like STD_union)."""
        try:
            return cls(*args, **kw)
        except TypeError, e:
            print 'ERROR in %s: %s' % (cls, e)
            raise

    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a simple type instance from the given DOM Node instance.

        Any whitespace facet constraint is applied to the extracted text."""
        # @todo error if non-text content?
        # @todo support _DynamicCreate
        instance_root = kw.pop('instance_root', None)
        rv = cls.Factory(domutils.ExtractTextContent(node), apply_whitespace_facet=True)
        rv._setBindingContext(node, instance_root)
        return rv

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
        kw.pop('validate_constraints', None)
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
        validate_constraints -- Validate the datatype constraints after initialization (default True)
        """
        validate_constraints = kw.pop('validate_constraints', True)
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

    def toDOM (self, dom_support, parent=None):
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

        @keyword validate_constraints: If True (default), any constructed
        value is checked against constraints applied to the union as well as
        the member type.

        @raise pyxb.BadTypeValueError: no member type will permit creation of
        an instance from the parameters in C{args} and C{kw}.
        """
        rv = None
        validate_constraints = kw.get('validate_constraints', True)
        for mt in cls._MemberTypes:
            try:
                rv = mt(*args, **kw)
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
        compatible but not an instance of the iitem type.  Returns the
        value that should be used as the item, or raises an exception
        if the value cannot be converted."""
        if issubclass(cls._ItemType, STD_union):
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

class element (_Binding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """Base class for any Python class that serves as the binding to
    an XMLSchema element.

    The subclass must define a class variable _TypeDefinition which is
    a reference to the simpleTypeDefinition or complexTypeDefinition
    subclass that serves as the information holder for the element.

    Most actions on instances of these clases are delegated to the
    underlying content object.
    """

    # Reference to the simple or complex type binding that serves as
    # the content of this element.
    # MUST BE SET IN SUBCLASS
    _TypeDefinition = None
    """The subclass of complexTypeDefinition that is used to represent content in this element."""

    # Reference to the instance of the underlying type
    __realContent = None

    # Reference to the instance of the underlying type, or to that
    # type's content if that is a complex type with simple content.
    __content = None
    
    # Symbols that remain the responsibility of this class.  Any
    # symbols in the type from the content are deconflicted by
    # providing an alternative name in the subclass.  See the
    # _DeconflictSymbols_mixin class.
    _ReservedSymbols = set([ 'content', 'CreateFromDOM', 'toDOM' ])

    # Assign to the content field.  This may manipulate the assigned
    # value if doing so results in a cleaner interface for the user.
    def __setContent (self, content):
        self.__realContent = content
        self.__content = self.__realContent
        if isinstance(content, complexTypeDefinition) and content._IsSimpleTypeContent():
            self.__content = self.__realContent.content()
        return self

    def __init__ (self, *args, **kw):
        """Create a new element.

        This sets the content to be an instance created by invoking
        the Factory method of the element type definition.
        
        If the element is a complex type with simple content, the
        value of the content() is dereferenced once, as a convenience.
        """
        self.__setContent(self._TypeDefinition.Factory(*args, **kw))
        
    # Determine which content should be used to dereference a particular
    # (Python) attribute.  Priority deferral to the real content.
    def __contentForAttribute (self, name):
        content = self.__content
        if self.__content != self.__realContent:
            if hasattr(self.__realContent, name):
                content = self.__realContent
        return content

    # Delegate unrecognized attribute accesses to the nearest content that has
    # the attribute.
    def __getattr__ (self, name):
        return getattr(self.__contentForAttribute(name), name)

    def content (self, dereference_if_simple=True):
        """Return the element content

        The element content is normally an instance of the _TypeDefinition for
        this class.  If that type is a subclass of L{CTD_simple}, then the
        content is the content of that instance, i.e. the underlying simple
        type.  This normally works because by overloading C{__getattr__} here
        all attribute references automaticallly delegate to the appropriate
        content level.

        @keyword dereference_if_simple: If True (default), the contained
        simple data type instance is returned if the type of the element is a
        complex type with simple content.  If False, will always return the
        immediate content node which is an instance of L{_TypeDefinition}.
        @type dereference_if_simple: C{bool}
        """
        if dereference_if_simple:
            return self.__content
        return self.__realContent
    
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an instance of this element from the given DOM node.

        :raise pyxb.LogicError: the name of the node is not consistent with
        the _XsdName of this class."""
        instance_root = kw.pop('instance_root', None)
        node_name = node.nodeName
        if 0 < node_name.find(':'):
            node_name = node_name.split(':')[1]
        if cls._XsdName != node_name:
            raise pyxb.UnrecognizedContentError('Attempting to create element %s from DOM node named %s' % (cls._XsdName, node_name))
        if issubclass(cls._TypeDefinition, simpleTypeDefinition):
            rv = cls._DynamicCreate(cls._TypeDefinition.CreateFromDOM(node))
        else:
            rv = cls._DynamicCreate(validate_constraints=False)
            rv.__setContent(cls._TypeDefinition.CreateFromDOM(node))
        if isinstance(rv, simpleTypeDefinition):
            rv.xsdConstraintsOK()
        rv._setBindingContext(node, instance_root)
        return rv

    def toDOM (self, dom_support, parent=None):
        """Add a DOM representation of this element as a child of
        parent, which should be a DOM Node instance."""
        assert isinstance(dom_support, domutils.BindingDOMSupport)
        element = dom_support.createChild(self._XsdName, self._Namespace, parent)
        self.__realContent.toDOM(dom_support, parent=element)
        return dom_support

    def __str__ (self):
        if isinstance(self.content(), simpleTypeDefinition):
            rv = self.content()
            if isinstance(rv, unicode):
                return rv.encode('utf-8')
            return str(rv)
        #return '%s: %s' % (self._XsdName, str(self.content()))
        return str(self.content())

    @classmethod
    def _IsSimpleTypeContent (cls):
        """Elements with types that are smple are themselves simple"""
        return cls._TypeDefinition._IsSimpleTypeContent()

class enumeration_mixin (pyxb.cscRoot):
    """Marker in case we need to know that a PST has an enumeration constraint facet."""
    pass

class complexTypeDefinition (_Binding_mixin, utility._DeconflictSymbols_mixin, _DynamicCreate_mixin):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType.

    Subclasses should define a class-level _AttributeMap variable which maps
    from the unicode tag of an attribute to the AttributeUse instance that
    defines it.  Similarly, subclasses should define an _ElementMap variable.
    """

    # If the type supports wildcard attributes, this describes their
    # constraints.  (If it doesn't, this should remain None.)  Supporting
    # classes should override this value.
    _AttributeWildcard = None

    # Map from ncNames in the binding namespace to AttributeUse instances
    _AttributeMap = { }

    # A value that indicates whether the content model for this type supports
    # wildcard elements.  Supporting classes should override this value.
    _HasWildcardElement = False

    # Map from ncNames in the binding namespace to ElementUse instances
    _ElementMap = { }

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
        if self._AttributeWildcard is not None:
            self.__wildcardAttributeMap = { }
        if self._HasWildcardElement:
            self.__wildcardElements = []
        super(complexTypeDefinition, self).__init__(*args, **kw)
        that = None
        if 0 < len(args):
            if isinstance(args[0], self.__class__):
                that = args[0]
            else:
                raise pyxb.IncompleteImplementationError('No %s constructor support for argument %s' % (type(self), args[0]))
        if isinstance(self, _CTD_content_mixin):
            self._resetContent()
        # Extract keywords that match field names
        for fu in self._PythonMap().values():
            fu.reset(self)
            iv = None
            if that is not None:
                iv = fu.value(that)
            iv = kw.get(fu.pythonField(), iv)
            if iv is not None:
                fu.setValue(self, iv)
           

    @classmethod
    def Factory (cls, *args, **kw):
        """Create an instance from parameters and keywords."""
        rv = cls(*args, **kw)
        return rv

    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an instance from a DOM node.

        Note that only the node attributes and content are used; the
        node name must have been validated against an owning
        element."""
        instance_root = kw.pop('instance_root', None)
        rv = cls._DynamicCreate(validate_constraints=False)
        rv._setAttributesFromDOM(node)
        rv._setContentFromDOM(node)
        rv._setBindingContext(node, instance_root)
        return rv

    # Specify the symbols to be reserved for all CTDs.
    _ReservedSymbols = set([ 'Factory', 'CreateFromDOM', 'toDOM' ])

    # Class variable which maps complex type attribute names to the name used
    # within the generated binding.  For example, if somebody's gone and
    # decided that the word Factory would make an awesome attribute for some
    # complex type, the binding will rewrite it so the accessor method is
    # Factory_.  This is only overridden in generated bindings where an
    # attribute name conflicted with a reserved symbol.
    _AttributeDeconflictMap = { }

    # Class variable which maps complex type element names to the name used
    # within the generated binding.  See _AttributeDeconflictMap.
    _ElementDeconflictMap = { }

    # None, or a reference to a ContentModel instance that defines how to
    # reduce a DOM node list to the body of this element.
    _ContentModel = None

    @classmethod
    def __PythonMapAttribute (cls):
        return '_%s_PythonMap' % (cls.__name__,)

    @classmethod
    def _PythonMap (cls):
        return getattr(cls, cls.__PythonMapAttribute(), { })

    @classmethod
    def _UpdateElementDatatypes (cls, datatype_map):
        """Sets the _ElementMap contents and pre-calculates maps from Python
        field names to element and attribute uses.

        :param datatype_map: Map from NCNames representing element tags to a
        list of Python classes corresponding to types that are stored in the
        field associated with the element.

        This is invoked at the module level after all binding classes have
        been defined and are available for reference."""
        for (k, v) in datatype_map.items():
            cls._ElementMap[k]._setValidElements(v)
        python_map = { }
        for eu in cls._ElementMap.values():
            python_map[eu.pythonField()] = eu
        for au in cls._AttributeMap.values():
            python_map[au.pythonField()] = au
        assert(len(python_map) == (len(cls._ElementMap) + len(cls._AttributeMap)))
        setattr(cls, cls.__PythonMapAttribute(), python_map)

    @classmethod
    def _UseForElement (cls, element):
        """Return the ElementUse object corresponding to the element type.

        :param element: A Python class corresponding to an element binding.
        """
        for eu in cls._ElementMap.values():
            if element in eu.validElements():
                return eu
        return None

    @classmethod
    def _UseForTag (cls, tag):
        """Return the ElementUse object corresponding to the element name.

        :param tag: The NCName of an element in the class"""
        return cls._ElementMap[tag]

    def _setAttributesFromDOM (self, node):
        """Initialize the attributes of this element from those of the DOM node.

        Raises pyxb.UnrecognizedAttributeError if the DOM node has attributes
        that are not allowed in this type.  May raise other errors if
        prohibited or required attributes are or are not present."""
        
        # Handle all the attributes that are present in the node
        attrs_available = set(self._AttributeMap.values())
        for ai in range(0, node.attributes.length):
            attr = node.attributes.item(ai)
            local_name = attr.localName
            namespace_name = attr.namespaceURI
            # Ignore xmlns attributes; DOM got those
            if pyxb.Namespace.XMLNamespaces.uri() == namespace_name:
                continue

            prefix = attr.prefix
            if not prefix:
                prefix = None
            value = attr.value
            # hack to make some QName attribute tags work
            if (attr.namespaceURI == node.namespaceURI):
                prefix = None

            # @todo handle cross-namespace attributes
            if prefix is not None:
                print 'IGNORING namespace-qualified attribute %s:%s' % (prefix, local_name)
                #raise pyxb.IncompleteImplementationError('No support for namespace-qualified attributes like %s:%s' % (prefix, local_name))
                continue
            au = self._AttributeMap.get(local_name, None)
            if au is None:
                if self._AttributeWildcard is None:
                    raise pyxb.UnrecognizedAttributeError('Attribute %s is not permitted in type' % (local_name,))
                self.__wildcardAttributeMap[local_name] = value
                continue
            au.setFromDOM(self, node)
            attrs_available.remove(au)

        # Handle all the ones that aren't present.  NB: Don't just reset the
        # attribute; we need to check for missing ones, which is done by
        # au.setFromDOM.
        for au in attrs_available:
            au.setFromDOM(self, node)
        return self

    def _setContentFromDOM_vx (self, node):
        """Override this in subclasses that expect to process content."""
        raise pyxb.LogicError('%s did not implement _setContentFromDOM_vx' % (self.__class__.__name__,))

    def _setContentFromDOM (self, node):
        """Initialize the content of this element from the content of the DOM node."""
        return self._setContentFromDOM_vx(node)

    def _setDOMFromAttributes (self, element):
        """Add any appropriate attributes from this instance into the DOM element."""
        for au in self._AttributeMap.values():
            au.addDOMAttribute(self, element)
        return element

    def toDOM (self, dom_support, parent=None, tag=None):
        """Create a DOM element with the given tag holding the content of this instance."""
        if tag is None:
            element = parent
        else:
            element = dom_support.createChild(tag, namespace, parent)
        for eu in self._ElementMap.values():
            eu.clearGenerationMarkers(self)
        self._setDOMFromContent(dom_support, element)
        for eu in self._ElementMap.values():
            if eu.hasUngeneratedValues(self):
                raise pyxb.DOMGenerationError('Values in %s were not converted to DOM' % (eu.pythonField(),))
        self._setDOMFromAttributes(element)
        return dom_support

class CTD_empty (complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with empty content."""

    def _setContentFromDOM_vx (self, node):
        """CTD with empty content does nothing with node content.
        @todo: Schema validation check (make sure node children are contentless)? """
        return self

    def _setDOMFromContent (self, dom_support, element):
        return self

class CTD_simple (complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with simple content."""

    _TypeDefinition = None
    """Subclass of simpleTypeDefinition that corresponds to the type content."""

    __content = None
    def content (self):
        return self.__content

    def __setContent (self, value):
        self.__content = value

    def __init__ (self, *args, **kw):
        assert issubclass(self._TypeDefinition, simpleTypeDefinition)
        super(CTD_simple, self).__init__(**kw)
        self.__setContent(self._TypeDefinition.Factory(*args, **kw))

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    def _setContentFromDOM_vx (self, node):
        """CTD with simple content type creates a PST instance from the node body."""
        self.__setContent(self._TypeDefinition.CreateFromDOM(node))
        self.xsdConstraintsOK()

    def _setDOMFromContent (self, dom_support, element):
        """Create a DOM element with the given tag holding the content of this instance."""

        return element.appendChild(dom_support.document().createTextNode(self.content().xsdLiteral()))

    _ReservedSymbols = complexTypeDefinition._ReservedSymbols.union(set([ 'xsdConstraintsOK', 'content' ]))

    def xsdConstraintsOK (self):
        return self.content().xsdConstraintsOK()

    @classmethod
    def _IsSimpleTypeContent (cls):
        """CTDs with simple content are simple"""
        return True

class _CTD_content_mixin (pyxb.cscRoot):
    """Retain information about element and mixed content in a complex type instance.

    This is used to generate the XML from the binding in the same
    order as it was read in, with mixed content in the right position.
    It can also be used if order is critical to the interpretation of
    interleaved elements.

    Subclasses must define a class variable _Content with a
    bindings.Particle instance as its value.

    Subclasses should define a class-level _ElementMap variable which
    maps from unicode element tags (not including namespace
    qualifiers) to the corresponding ElementUse information
    """

    # A list containing just the content
    __content = None

    def __init__ (self, *args, **kw):
        self._resetContent()
        super(_CTD_content_mixin, self).__init__(*args, **kw)

    def content (self):
        return ''.join([ _x for _x in self.__content if isinstance(_x, types.StringTypes) ])

    def _resetContent (self):
        self.__content = []

    def _addElement (self, element):
        eu = self._ElementMap.get(element._XsdName, None)
        if eu is None:
            raise pyxb.LogicError('Element %s is not registered within CTD %s' % (element._XsdName, self.__class__.__name__))
        eu.setValue(self, element)

    def _addContent (self, child):
        assert isinstance(child, element) or isinstance(child, types.StringTypes)
        self.__content.append(child)

    __isMixed = False
    def _stripMixedContent (self, node_list):
        while 0 < len(node_list):
            if not (node_list[0].nodeType in (dom.Node.TEXT_NODE, dom.Node.CDATA_SECTION_NODE, dom.Node.COMMENT_NODE)):
                break
            cn = node_list.pop(0)
            if dom.Node.COMMENT_NODE == cn.nodeType:
                continue
            if self.__isMixed:
                #print 'Adding mixed content'
                self._addContent(cn.data)
            else:
                #print 'Ignoring mixed content'
                pass
        return node_list

    def _setMixableContentFromDOM (self, node, is_mixed):
        """Set the content of this instance from the content of the given node."""
        #assert isinstance(self._Content, Particle)
        # The child nodes may include text which should be saved as
        # mixed content.  Use _stripMixedContent prior to extracting
        # element data to save them in the correct relative position,
        # while not losing track of where we are in the content model.
        self.__isMixed = is_mixed
        node_list = node.childNodes[:]
        #print 'Setting mixable control of %s from %s' % (self.__class__, node_list)
        self._stripMixedContent(node_list)
        if self._ContentModel is not None:
            self._ContentModel.interprete(self, node_list)
            self._stripMixedContent(node_list)
        if 0 < len(node_list):
            raise pyxb.ExtraContentError('Extra content starting with %s' % (node_list[0],))
        return self

    def _setDOMFromContent (self, dom_support, element):
        self._Content.extendDOMFromContent(dom_support, element, self)
        mixed_content = self.content()
        if 0 < len(mixed_content):
            element.appendChild(dom_support.document().createTextNode(''.join(mixed_content)))
        return self

class CTD_mixed (_CTD_content_mixin, complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with mixed content.
    """

    _ReservedSymbols = complexTypeDefinition._ReservedSymbols.union(set([ 'content' ]))

    def _setContentFromDOM_vx (self, node):
        """Delegate processing to content mixin, with mixed content enabled."""
        return self._setMixableContentFromDOM(node, is_mixed=True)


class CTD_element (_CTD_content_mixin, complexTypeDefinition):
    """Base for any Python class that serves as the binding for an
    XMLSchema complexType with element-only content.
    """

    _ReservedSymbols = complexTypeDefinition._ReservedSymbols.union(set([ 'content' ]))

    def _setContentFromDOM_vx (self, node):
        """Delegate processing to content mixin, with mixed content disabled."""
        return self._setMixableContentFromDOM(node, is_mixed=False)


## Local Variables:
## fill-column:78
## End:
    
