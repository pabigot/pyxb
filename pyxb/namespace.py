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

"""Classes and global objects related to U{XML Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}.

Since namespaces hold all referenceable objects, this module also defines the
infrastructure for resolving named object references, such as schema
components.

@group Resolution: _Resolvable_mixin, _NamespaceResolution_mixin
@group Component Management: _ComponentDependency_mixin, _NamespaceComponentAssociation_mixin
@group Schema Specializations: _XML, _XMLSchema, _XMLSchema_instance
@group Named Object Management: _NamespaceCategory_mixin, NamedObjectMap
"""

import pyxb
import os
import fnmatch
import pyxb.utils.utility
import xml.dom

PathEnvironmentVariable = 'PYXB_ARCHIVE_PATH'
"""Environment variable from which default path to pre-loaded namespaces is
read.  The value should be a colon-separated list of absolute paths.  A path
of C{+} will be replaced by the system default path (normally
C{pyxb/standard/bindings/raw})."""

import os.path
DefaultArchivePath = "%s/standard/bindings/raw" % (os.path.dirname(__file__),)
"""Default location for reading C{.wxs} files"""

def GetArchivePath ():
    import os
    rv = os.environ.get(PathEnvironmentVariable)
    if rv is None:
        rv = '+'
    return rv

# Stuff required for pickling
import cPickle as pickle

# A unique identifier for components that are built-in to the PyXB system
BuiltInObjectUID = pyxb.utils.utility.UniqueIdentifier('PyXB-' + pyxb.__version__ + '-Builtin')

class ExpandedName (pyxb.cscRoot):

    """Represent an U{expanded name
    <http://www.w3.org/TR/REC-xml-names/#dt-expname>}, which pairs a
    namespace with a local name.

    Because a large number of local elements, and most attributes, have no
    namespace associated with them, this is optimized for representing names
    with an absent namespace.  The hash and equality test methods are set so
    that a plain string is equivalent to a tuple of C{None} and that string.

    Note that absent namespaces can be represented in two ways: with a
    namespace of C{None} (the name "has no namespace"), and with a namespace
    that is an L{absent namespace <Namespace.CreateAbsentNamespace>} (the name
    "has an absent namespace").  Hash code calculations are done so that the
    two alternatives produce the same hash; however, comparison is done so
    that the two are distinguished.  The latter is the intended behavior; the
    former should not be counted upon.

    This class allows direct lookup of the named object within a category by
    using the category name as an accessor function.  That is, if the
    namespace of the expanded name C{en} has a category 'typeDefinition', then
    the following two expressions are equivalent::
    
      en.typeDefinition()
      en.namespace().categoryMap('typeDefinition').get(en.localName())

    This class descends from C{tuple} so that its values can be used as
    dictionary keys without concern for pointer equivalence.
    """
    def namespace (self):
        """The L{Namespace} part of the expanded name."""
        return self.__namespace
    __namespace = None

    def namespaceURI (self):
        """Return the URI of the namespace, or C{None} if the namespace is absent."""
        return self.__namespaceURI
    __namespaceURI = None

    def localName (self):
        """The local part of the expanded name."""
        return self.__localName
    __localName = None

    # Cached tuple representation
    __expandedName = None

    def validateComponentModel (self):
        """Pass model validation through to namespace part."""
        return self.namespace().validateComponentModel()

    def uriTuple (self):
        """Return a tuple consisting of the namespace URI and the local name.

        This presents the expanded name as base Python types for persistent
        storage.  Be aware, though, that it will lose the association of the
        name with an absent namespace, if that matters to you."""
        return ( self.__namespaceURI, self.__localName )

    # Treat unrecognized attributes as potential accessor functions
    def __getattr__ (self, name):
        # Don't try to recognize private names (like __setstate__)
        if name.startswith('__'):
            return super(ExpandedName, self).__getattr__(name)
        if self.namespace() is None:
            return lambda: None
        # NOTE: This will raise pyxb.NamespaceError if the category does not exist.
        category_value = self.namespace().categoryMap(name).get(self.localName())
        return lambda : category_value

    def createName (self, local_name):
        """Return a new expanded name in the namespace of this name.

        @param local_name: The local name portion of an expanded name.
        @return: An instance of L{ExpandedName}.
        """
        return ExpandedName(self.namespace(), local_name)

    def adoptName (self, name):
        """Return the input name, except if the input name has no namespace,
        return a name that uses the namespace from this name with the local
        name from the input name.

        Use this when the XML document has an unqualified name and we're
        processing using an absent default namespace.

        @warning: Be careful when using a global name to adopt a name from a
        local element: if the local element (with no namespace) has the same
        localName as but is different from the global element (with a
        namespace), this will improperly provide a namespace when one should
        not be present.  See the comments in
        L{pyxb.binding.basis.element.elementForName}.
        """

        if not isinstance(name, ExpandedName):
            name = ExpandedName(name)
        if name.namespace() is None:
            name = self.createName(name.localName())
        return name

    def __init__ (self, *args, **kw):
        """Create an expanded name.

        Expected argument patterns are:

        ( C{str} ) -- the local name in an absent namespace
        ( L{ExpandedName} ) -- a copy of the given expanded name
        ( C{xml.dom.Node} ) -- The name extracted from node.namespaceURI and node.localName
        ( C{str}, C{str} ) -- the namespace URI and the local name
        ( L{Namespace}, C{str} ) -- the namespace and the local name
        ( L{ExpandedName}, C{str}) -- the namespace from the expanded name, and the local name

        Wherever C{str} occurs C{unicode} is also permitted.
        
        @keyword fallback_namespace: Optional Namespace instance to use if the
        namespace would otherwise be None.  This is only used if it is an
        absent namespace.

        """
        fallback_namespace = kw.get('fallback_namespace')
        if 0 == len(args):
            raise pyxb.LogicError('Too few arguments to ExpandedName constructor')
        if 2 < len(args):
            raise pyxb.LogicError('Too many arguments to ExpandedName constructor')
        if 2 == len(args):
            # Namespace(str, unicode, Namespace) and local name (str, unicode)
            ( ns, ln ) = args
        else:
            # Local name (str, unicode) or ExpandedName or Node
            assert 1 == len(args)
            ln = args[0]
            ns = None
            if isinstance(ln, basestring):
                pass
            elif isinstance(ln, tuple) and (2 == len(ln)):
                (ns, ln) = ln
            elif isinstance(ln, ExpandedName):
                ns = ln.namespace()
                ln = ln.localName()
            elif isinstance(ln, xml.dom.Node):
                if not(ln.nodeType in (xml.dom.Node.ELEMENT_NODE, xml.dom.Node.ATTRIBUTE_NODE)):
                    raise pyxb.LogicError('Cannot create expanded name from non-element DOM node %s' % (ln.nodeType,))
                ns = ln.namespaceURI
                ln = ln.localName
            else:
                raise pyxb.LogicError('Unrecognized argument type %s' % (type(ln),))
        if (ns is None) and (fallback_namespace is not None):
            if fallback_namespace.isAbsentNamespace():
                ns = fallback_namespace
        if isinstance(ns, (str, unicode)):
            ns = NamespaceForURI(ns, create_if_missing=True)
        if isinstance(ns, ExpandedName):
            ns = ns.namespace()
        if (ns is not None) and not isinstance(ns, Namespace):
            raise pyxb.LogicError('ExpandedName must include a valid (perhaps absent) namespace, or None.')
        self.__namespace = ns
        if self.__namespace is not None:
            self.__namespaceURI = self.__namespace.uri()
        self.__localName = ln
        assert self.__localName is not None
        self.__expandedName = ( self.__namespace, self.__localName )
        self.__uriTuple = ( self.__namespaceURI, self.__localName )


    def __str__ (self):
        assert self.__localName is not None
        if self.__namespaceURI is not None:
            return '{%s}%s' % (self.__namespaceURI, self.__localName)
        return self.localName()

    def __hash__ (self):
        if self.__namespaceURI is None:
            # Handle both str and unicode hashes
            return type(self.__localName).__hash__(self.__localName)
        return tuple.__hash__(self.__expandedName)

    def __cmp__ (self, other):
        if other is None: # None is below everything else
            return cmp(1, -1)
        if isinstance(other, (str, unicode)):
            other = ( None, other )
        if not isinstance(other, tuple):
            other = other.__uriTuple
        if isinstance(other[0], Namespace):
            other = ( other[0].uri(), other[1] )
        return cmp(self.__uriTuple, other)

    def getAttribute (self, dom_node):
        """Return the value of the attribute identified by this name in the given node.

        @return: An instance of C{xml.dom.Attr}, or C{None} if the node does
        not have an attribute with this name.
        """
        if dom_node.hasAttributeNS(self.__namespaceURI, self.__localName):
            return dom_node.getAttributeNS(self.__namespaceURI, self.__localName)
        return None

    def nodeMatches (self, dom_node):
        """Return C{True} iff the dom node expanded name matches this expanded name."""
        return (dom_node.localName == self.__localName) and (dom_node.namespaceURI == self.__namespaceURI)

class _Resolvable_mixin (pyxb.cscRoot):
    """Mix-in indicating that this object may have references to unseen named components.

    This class is mixed-in to those XMLSchema components that have a reference
    to another component that is identified by a QName.  Resolution of that
    component may need to be delayed if the definition of the component has
    not yet been read.
    """

    #_TraceResolution = True
    _TraceResolution = False

    def isResolved (self):
        """Determine whether this named component is resolved.

        Override this in the child class."""
        raise pyxb.LogicError('Resolved check not implemented in %s' % (self.__class__,))
    
    def _resolve (self):
        """Perform whatever steps are required to resolve this component.

        Resolution is performed in the context of the namespace to which the
        component belongs.  Invoking this method may fail to complete the
        resolution process if the component itself depends on unresolved
        components.  The sole caller of this should be
        L{_NamespaceResolution_mixin.resolveDefinitions}.
        
        This method is permitted (nay, encouraged) to raise an exception if
        resolution requires interpreting a QName and the named component
        cannot be found.

        Override this in the child class.  In the prefix, if L{isResolved} is
        true, return right away.  If something prevents you from completing
        resolution, invoke L{self._queueForResolution()} (so it is retried
        later) and immediately return self.  Prior to leaving after successful
        resolution discard any cached dom node by setting C{self.__domNode=None}.

        @return: C{self}, whether or not resolution succeeds.
        @raise pyxb.SchemaValidationError: if resolution requlres a reference to an unknown component
        """
        raise pyxb.LogicError('Resolution not implemented in %s' % (self.__class__,))

    def _queueForResolution (self, why=None):
        """Short-hand to requeue an object if the class implements _namespaceContext().
        """
        if (why is not None) and self._TraceResolution:
            print 'Resolution delayed for %s: %s' % (self, why)
        self._namespaceContext().queueForResolution(self)

class NamespaceArchive (object):
    """Represent a file from which one or more namespaces can be read."""

    # YYYYMMDDHHMM
    __PickleFormat = '200907190858'

    __AnonymousCategory = '_anonymousTypeDefinition'
    @classmethod
    def _AnonymousCategory (cls):
        """The category name to use when storing references to anonymous type
        definitions.  For example, attribute definitions defined within an
        attribute use in a model group definition.that can be referenced frojm
        ax different namespace."""
        return cls.__AnonymousCategory

    # Class variable recording the namespace that is currently being
    # pickled.  Used to prevent storing components that belong to
    # other namespaces.  Should be None unless within an invocation of
    # SaveToFile.
    __PicklingArchive = None

    @classmethod
    def PicklingArchive (cls):
        """Return a reference to a set specifying the namespace instances that
        are being archived.

        This is needed to determine whether a component must be serialized as
        aa reference."""
        # NB: Use root class explicitly.  If we use cls, when this is invoked
        # by subclasses it gets mangled using the subclass name so the one
        # defined in this class is not found
        return NamespaceArchive.__PicklingArchive

    def archivePath (self):
        """Path to the file in which this namespace archive is stored."""
        return self.__archivePath
    __archivePath = None

    def generationUID (self):
        return self.__generationUID
    __generationUID = None

    def __init__ (self, namespaces=None, archive_path=None, generation_uid=None):
        self.__namespaces = set()
        if namespaces is not None:
            if archive_path:
                raise pyxb.LogicError('NamespaceArchive: cannot define both namespaces and archive_path')
            if generation_uid is None:
                raise pyxb.LogicError('NamespaceArchive: must provide generation_uid with namespaces')
            self.__generationUID = generation_uid
            self.update(namespaces)
        elif archive_path is not None:
            if generation_uid is not None:
                raise pyxb.LogicError('NamespaceArchive: cannot provide generation_uid with archive_path')
            self.__archivePath = archive_path
            self.__readNamespaceSet(self.__createUnpickler(), define_namespaces=True)
        else:
            pass

    def add (self, namespace):
        """Add the given namespace to the set that is to be stored in this archive."""
        if namespace.isAbsentNamespace():
            raise pyxb.NamespaceArchiveError('Cannot archive absent namespace')
        self.__namespaces.add(namespace)

    def update (self, namespace_set):
        """Add the given namespaces to the set that is to be stored in this archive."""
        [ self.add(_ns) for _ns in namespace_set ]

    def namespaces (self):
        """Set of namespaces that can be read from this archive."""
        return self.__namespaces
    __namespaces = None

    def dissociateNamespaces (self):
        """Prevent this archive from being consulted when any of its
        namespaces must be loaded."""
        for ns in self.__namespaces:
            ns._removeArchive(self)
        self.__namespaces.clear()

    def __createUnpickler (self):
        unpickler = pickle.Unpickler(open(self.__archivePath, 'rb'))

        format = unpickler.load()
        if self.__PickleFormat != format:
            raise pyxb.NamespaceArchiveError('Archive format is %s, require %s' % (format, self.__PickleFormat))

        self.__generationUID = unpickler.load()

        return unpickler

    def __createPickler (self, output):
        # @todo: support StringIO instances?
        if not isinstance(output, file):
            output = open(output, 'wb')
        pickler = pickle.Pickler(output, -1)
    
        # The format of the archive
        pickler.dump(NamespaceArchive.__PickleFormat)
    
        # The UID for the set
        assert self.generationUID() is not None
        pickler.dump(self.generationUID())

        return pickler

    __readNamespaces = False
    def readNamespaces (self):
        if self.__readNamespaces:
            raise pyxb.NamespaceArchiveError('Multiple reads of archive %s' % (self.__archivePath,))
        self.__readNamespaces = True

        unpickler = self.__createUnpickler()

        # Read the namespaces and their categories.  This makes sure we won't
        # overwrite something by loading from the archive.
        uri_map = self.__readNamespaceSet(unpickler)

        # Load up the metadata like the module path
        ns_set = unpickler.load()
        assert ns_set == self.namespaces()

        # Now unarchive everything and associate it with its relevant
        # namespace.
        object_maps = unpickler.load()
        for ns in ns_set:
            print 'Read %s from %s - active %s' % (ns, self.__archivePath, ns.isActive())
            ns._loadNamedObjects(object_maps[ns])
            ns._setLoadedFromArchive(self)
        
        self.dissociateNamespaces()

    def writeNamespaces (self, output):
        """Store the namespaces into the archive.

        @param output: An instance substitutable for a writable file, or the
        name of a file to write to.
        """
        import sys
        
        NamespaceArchive.__PicklingArchive = self

        try:
            # See http://bugs.python.org/issue3338
            recursion_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(10 * recursion_limit)
    
            pickler = self.__createPickler(output)

            # The set of URIs defining the namespaces in the archive, along
            # with the categories defined by each one, and the names defined
            # in each category.
            uri_map = {}
            for ns in self.namespaces():
                uri_map[ns.uri()] = cat_map = {}
                for cat in ns.categories():
                    cat_map[cat] = frozenset(ns.categoryMap(cat).keys())
            pickler.dump(uri_map)
    
            # The pickled namespaces.  Note that namespaces have a custom pickling
            # representation which does not include any of the objects they hold.
            pickler.dump(self.namespaces())
    
            # A map from namespace to the category maps of the namespace.
            object_map = { }
            for ns in self.namespaces():
                assert not ns.isAbsentNamespace()
                ns.configureCategories([self._AnonymousCategory()])
                object_map[ns] = ns._categoryMap()
                ns._setWroteToArchive(self)
                for obj in ns._namedObjects().union(ns.components()):
                    obj._prepareForArchive(self, ns)
            pickler.dump(object_map)
        finally:
            sys.setrecursionlimit(recursion_limit)
        NamespaceArchive.__PicklingArchive = None

    def __readNamespaceSet (self, unpickler, define_namespaces=False):
        uri_map = unpickler.load()
        
        for (uri, categories) in uri_map.items():
            cat_map = uri_map[uri]
            ns = NamespaceInstance(uri)
            for cat in cat_map.keys():
                if not (cat in ns.categories()):
                    continue
                cross_objects = frozenset([ _ln for _ln in cat_map[cat].intersection(ns.categoryMap(cat).keys()) if not ns.categoryMap(cat)[_ln]._allowUpdateFromOther(None) ])
                if 0 < len(cross_objects):
                    raise pyxb.NamespaceArchiveError('Namespace %s archive/active conflict on category %s: %s' % (ns, cat, " ".join(cross_objects)))
                # Verify namespace is not available from a different archive
                if (ns.archive() is not None) and (ns.archive() != self):
                    raise pyxb.NamespaceArchiveError('Namespace %s already available from %s' % (uri, ns.archive()))

        if not define_namespaces:
            return

        for uri in uri_map.keys():
            ns = NamespaceForURI(uri, create_if_missing=True)
            ns._addArchive(self)
            self.__namespaces.add(ns)

        return uri_map

    def __str__ (self):
        archive_path = self.__archivePath
        if archive_path is None:
            archive_path = '??'
        return 'NSArchive@%s' % (archive_path,)

class _ObjectArchivable_mixin (pyxb.cscRoot):
    """Mix-in to any object that can be stored in a namespace within an archive."""
    
    # Need to set this per category item
    __objectOriginUID = None
    def _objectOriginUID (self):
        return self.__objectOriginUID
    def _setObjectOriginUID (self, object_origin_uid):
        if self.__objectOriginUID is not None:
            if  self.__objectOriginUID != object_origin_uid:
                raise pyxb.LogicError('Inconsistent origins for object %s' % (self,))
        else:
            self.__objectOriginUID = object_origin_uid
    def _setObjectOriginUIDIfUndefined (self, object_origin_uid):
        if self.__objectOriginUID is None:
            self.__objectOriginUID = object_origin_uid
        return self.__objectOriginUID

    def _prepareForArchive_csc (self, archive, namespace):
        return getattr(super(_ObjectArchivable_mixin, self), '_prepareForArchive_csc', lambda *_args,**_kw: self)(archive, namespace)

    def _prepareForArchive (self, archive, namespace):
        assert self.__objectOriginUID is not None
        return self._prepareForArchive_csc(archive, namespace)

    def _updateFromOther_csc (self, other):
        return getattr(super(_ObjectArchivable_mixin, self), '_updateFromOther_csc', lambda *_args,**_kw: self)(other)

    def _updateFromOther (self, other):
        """Update this instance with additional information provided by the other instance.

        This is used, for example, when a built-in type is already registered
        in the namespace, but we've processed the corresponding schema and
        have obtained more details."""
        assert self != other
        return self._updateFromOther_csc(other)

    def _allowUpdateFromOther (self, other):
        global BuiltInObjectUID
        return BuiltInObjectUID == self._objectOriginUID()

class _NamespaceArchivable_mixin (pyxb.cscRoot):

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles category-related data."""
        getattr(super(_NamespaceArchivable_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__sourceArchives = set()
        self.__loadedFromArchive = None
        self.__wroteToArchive = None
        self.__active = False

    def definedBySchema (self):
        return self.isActive() and not (self._loadedFromArchive() or self.isBuiltinNamespace()) and (self.modulePath() is None) and (0 < len(self.components()))

    def _loadedFromArchive (self):
        return self.__loadedFromArchive
    
    __wroteToArchive = None
    __loadedFromArchive = None

    def isActive (self, empty_inactive=False):
        if self.__isActive and empty_inactive:
            for (ct, cm) in self._categoryMap().items():
                if 0 < len(cm):
                    print '%s: %d %s -- activated' % (self, len(cm), ct)
                    return True
            return False
        return self.__isActive

    def _activate (self):
        #if not self.__isActive:
        #    print 'Activating %s' % (self,)
        self.__isActive = True
    __isActive = None

    def __init__ (self, *args, **kw):
        super(_NamespaceArchivable_mixin, self).__init__(*args, **kw)
        
    def _setLoadedFromArchive (self, archive):
        self.__loadedFromArchive = archive
        self._activate()
    def _setWroteToArchive (self, archive):
        self.__wroteToArchive = archive

    def _addArchive (self, archive):
        self.__sourceArchives.add(archive)

    def _removeArchive (self, archive):
        # Yes, I do want this to raise KeyError if the archive is not present
        self.__sourceArchives.remove(archive)
        
    def archive (self):
        if 0 == len(self.__sourceArchives):
            return None
        if 1 < len(self.__sourceArchives):
            raise pyxb.NamespaceArchiveError('%s available from multiple archives: %s' % (self.uri(), ' '.join([str(_ns) for _ns in self.__sourceArchives])))
        return iter(self.__sourceArchives).next()
    __sourceArchives = None
    
    def isLoadable (self):
        """Return C{True} iff the component model for this namespace can be
        loaded from a namespace archive."""
        return 0 < len(self.__sourceArchives)

    def _setState_csc (self, kw):
        #assert not self.__isActive, 'ERROR: State set for active namespace %s' % (self,)
        return getattr(super(_NamespaceResolution_mixin, self), '_getState_csc', lambda _kw: _kw)(kw)
    
    def markNotLoadable (self):
        """Prevent loading this namespace from an archive.

        This dissociates not just the namespace, but all of its archives,
        which will no longer be available for use in loading other namespaces,
        since they are likely to depend on this one."""
        for archive in self.__sourceArchives:
            aarchive.dissociateNamespaces()

class NamedObjectMap (dict):
    """An extended dictionary intended to assist with QName resolution.

    These dictionaries have an attribute that identifies a category of named
    objects within a Namespace; the specifications for various documents
    require that certain groups of objects must be unique, while uniqueness is
    not required between groups.  The dictionary also retains a pointer to the
    Namespace instance for which it holds objects."""
    def namespace (self):
        """The namespace to which the object map belongs."""
        return self.__namespace
    __namespace = None
    
    def category (self):
        """The category of objects (e.g., typeDefinition, elementDeclaration)."""
        return self.__category
    __category = None

    def __init__ (self, category, namespace, *args, **kw):
        self.__category = category
        self.__namespace = namespace
        super(NamedObjectMap, self).__init__(*args, **kw)

class _NamespaceCategory_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces that hold
    references to categories of named objects.

    Arbitrary groups of named objects, each requiring unique names within
    themselves, can be saved.  Unless configured otherwise, the Namespace
    instance is extended with accessors that provide direct access to
    individual category maps.  The name of the method is the category name
    with a suffix of "s"; e.g., if a category "typeDefinition" exists, it can
    be accessed from the namespace using the syntax C{ns.typeDefinitions()}.

    Note that the returned value from the accessor is a live reference to
    the category map; changes made to the map are reflected in the
    namespace.
    """
    
    # Map from category strings to NamedObjectMap instances that
    # contain the dictionary for that category.
    __categoryMap = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles category-related data."""
        getattr(super(_NamespaceCategory_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__categoryMap = { }

    def categories (self):
        """The list of individual categories held in this namespace."""
        return self.__categoryMap.keys()

    def _categoryMap (self):
        """Return the whole map from categories to named objects."""
        return self.__categoryMap

    def categoryMap (self, category):
        """Map from local names to NamedObjectMap instances for the given category."""
        try:
            return self.__categoryMap[category]
        except KeyError:
            raise pyxb.NamespaceError(self, '%s has no category %s' % (self, category))

    def __defineCategoryAccessors (self):
        """Define public methods on the Namespace which provide access to
        individual NamedObjectMaps based on their category.

        """
        for category in self.categories():
            accessor_name = category + 's'
            setattr(self, accessor_name, lambda _map=self.categoryMap(category): _map)

    def configureCategories (self, categories):
        """Ensure there is a map for each of the given categories.

        Category configuration
        L{activates<_NamespaceArchivable_mixin.isActive>} a namespace.

        Existing maps are not affected."""
                                                     
        self._activate()
        if self.__categoryMap is None:
            self.__categoryMap = { }
        for category in categories:
            if not (category in self.__categoryMap):
                self.__categoryMap[category] = NamedObjectMap(category, self)
        self.__defineCategoryAccessors()
        return self

    def addCategoryObject (self, category, local_name, named_object):
        """Allow access to the named_object by looking up the local_name in
        the given category.

        Raises pyxb.NamespaceUniquenessError if an object with the same name
        already exists in the category."""
        name_map = self.categoryMap(category)
        old_object = name_map.get(local_name)
        if (old_object is not None) and (old_object != named_object):
            raise pyxb.NamespaceUniquenessError(self, '%s: name %s used for multiple values in %s' % (self, local_name, category))
        name_map[local_name] = named_object
        return named_object

    def replaceCategoryObject (self, category, local_name, old_object, new_object):
        """Replace the referenced object in the category.

        The new object will be added only if the old_object matches the
        current entry for local_name in the category."""
        name_map = self.categoryMap(category)
        if old_object == name_map.get(local_name):
            name_map[local_name] = new_object
        return name_map[local_name]

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition where present in the category maps.

        @note: This is a high-cost operation, as every item in every category
        map must be examined to see whether its value field matches
        C{existing_def}."""
        for (cat, registry) in self.__categoryMap.items():
            for (k, v) in registry.items():
                if v == existing_def:
                    print 'Replacing value for %s in %s' % (k, cat)
                    del registry[k]
                    if replacement_def is not None:
                        registry[k] = replacement_def
        return getattr(super(_NamespaceCategory_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    # Verify that the namespace category map has no components recorded.  This
    # is the state that should hold prior to loading a saved namespace; at
    # tthe moment, we do not support aggregating components defined separately
    # into the same namespace.  That should be done at the schema level using
    # the "include" element.
    def __checkCategoriesEmpty (self):
        if self.__categoryMap is None:
            return True
        assert isinstance(self.__categoryMap, dict)
        if 0 == len(self.__categoryMap):
            return True
        for k in self.categories():
            if 0 < len(self.categoryMap(k)):
                return False
        return True

    def _namedObjects (self):
        objects = set()
        for category_map in self.__categoryMap.values():
            objects.update(category_map.values())
        return objects

    def _loadNamedObjects (self, category_map):
        """Add the named objects from the given map into the set held by this namespace.
        It is an error to name something which is already present."""
        self.configureCategories(category_map.keys())
        for category in category_map.keys():
            current_map = self.categoryMap(category)
            new_map = category_map[category]
            for (local_name, component) in new_map.iteritems():
                existing_component = current_map.get(local_name)
                if existing_component is None:
                    current_map[local_name] = component
                elif existing_component._allowUpdateFromOther(component):
                    existing_component._updateFromOther(component)
                else:
                    raise pyxb.NamespaceError(self, 'Load attempted to override %s %s in %s' % (category, ln, self.uri()))
        self.__defineCategoryAccessors()

    def hasSchemaComponents (self):
        """Return C{True} iff schema components have been associated with this namespace.

        Note that this only checks whether the corresponding categories have
        been added, not whether there are any entries in those categories.  It
        is useful for identifying namespaces that were incorporated through a
        declaration but never actually referenced."""
        return 'typeDefinition' in self.__categoryMap


class _NamespaceResolution_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces relevant to
    resolving component references.
    """

    # A set of namespaces which some schema imported while processing with
    # this namespace as target.
    __importedNamespaces = None

    # A set of namespaces which appear in namespace declarations of schema
    # with this namespace as target.
    __referencedNamespaces = None

    # A list of Namespace._Resolvable_mixin instances that have yet to be
    # resolved.
    __unresolvedComponents = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles component-resolution--related data."""
        getattr(super(_NamespaceResolution_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__unresolvedComponents = []
        self.__importedNamespaces = set()
        self.__referencedNamespaces = set()

    def _getState_csc (self, kw):
        kw.update({
                'importedNamespaces': self.__importedNamespaces,
                'referencedNamespaces': self.__referencedNamespaces,
                })
        return getattr(super(_NamespaceResolution_mixin, self), '_getState_csc', lambda _kw: _kw)(kw)

    def _setState_csc (self, kw):
        self.__importedNamespaces = kw['importedNamespaces']
        self.__referencedNamespaces = kw['referencedNamespaces']
        return getattr(super(_NamespaceResolution_mixin, self), '_setState_csc', lambda _kw: self)(kw)

    def importNamespace (self, namespace):
        self.__importedNamespaces.add(namespace)
        return self

    def _referenceNamespace (self, namespace):
        self._activate()
        self.__referencedNamespaces.add(namespace)
        return self

    def importedNamespaces (self):
        """Return the set of namespaces which some schema imported while
        processing with this namespace as target."""
        return frozenset(self.__importedNamespaces)

    def referencedNamespaces (self):
        """Return the set of namespaces which appear in namespace declarations
        of schema with this namespace as target."""
        return frozenset(self.__referencedNamespaces)

    def queueForResolution (self, resolvable):
        """Invoked to note that a component may have references that will need
        to be resolved.

        Newly created named components are often unresolved, as are components
        which, in the course of resolution, are found to depend on another
        unresolved component.

        The provided object must be an instance of _Resolvable_mixin.  This
        method returns the resolvable object.
        """
        assert isinstance(resolvable, _Resolvable_mixin)
        if not resolvable.isResolved():
            self.__unresolvedComponents.append(resolvable)
        return resolvable

    def needsResolution (self):
        """Return C{True} iff this namespace has not been resolved."""
        return self.__unresolvedComponents is not None

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition if present in the list of unresolved components.
        """
        try:
            index = self.__unresolvedComponents.index(existing_def)
            print 'Replacing unresolved %s' % (existing_def,)
            if (replacement_def is None) or (replacement_def in self.__unresolvedComponents):
                del self.__unresolvedComponents[index]
            else:
                assert isinstance(replacement_def, _Resolvable_mixin)
                self.__unresolvedComponents[index] = replacement_def
        except ValueError:
            pass
        return getattr(super(_NamespaceResolution_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    def resolveDefinitions (self, allow_unresolved=False):
        """Loop until all references within the associated resolvable objects
        have been resolved.

        This method iterates through all components on the unresolved list,
        invoking the _resolve method of each.  If the component could not be
        resolved in this pass, it iis placed back on the list for the next
        iteration.  If an iteration completes without resolving any of the
        unresolved components, a pyxb.NotInNamespaceError exception is raised.

        @note: Do not invoke this until all top-level definitions for the
        namespace have been provided.  The resolution routines are entitled to
        raise a validation exception if a reference to an unrecognized
        component is encountered.
        """
        num_loops = 0
        if not self.needsResolution():
            return True
        
        while 0 < len(self.__unresolvedComponents):
            # Save the list of unresolved objects, reset the list to capture
            # any new objects defined during resolution, and attempt the
            # resolution for everything that isn't resolved.
            unresolved = self.__unresolvedComponents
            #print 'Looping for %d unresolved definitions: %s' % (len(unresolved), ' '.join([ str(_r) for _r in unresolved]))
            num_loops += 1
            #assert num_loops < 18
            
            self.__unresolvedComponents = []
            for resolvable in unresolved:
                # Attempt the resolution.
                resolvable._resolve()

                # Either we resolved it, or we queued it to try again later
                assert resolvable.isResolved() or (resolvable in self.__unresolvedComponents), 'Lost resolvable %s' % (resolvable,)

                # We only clone things that have scope None.  We never
                # resolve things that have scope None.  Therefore, we
                # should never have resolved something that has
                # clones.
                if (resolvable.isResolved() and (resolvable._clones() is not None)):
                    assert False
            if self.__unresolvedComponents == unresolved:
                if allow_unresolved:
                    return False
                # This only happens if we didn't code things right, or the
                # there is a circular dependency in some named component
                # (i.e., the schema designer didn't do things right).
                failed_components = []
                import pyxb.xmlschema.structures
                for d in self.__unresolvedComponents:
                    if isinstance(d, pyxb.xmlschema.structures._NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        if isinstance(d, pyxb.xmlschema.structures.AttributeUse):
                            print d.attributeDeclaration()
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise pyxb.NotInNamespaceError('Infinite loop in resolution:\n  %s' % ("\n  ".join(failed_components),))

        # Replace the list of unresolved components with None, so that
        # attempts to subsequently add another component fail.
        self.__unresolvedComponents = None

        # NOTE: Dependencies may require that we keep these around for a while
        # longer.
        #
        # Remove the namespace context from everything, since we won't be
        # resolving anything else.
        self._releaseNamespaceContexts()

        return True
    
    def _unresolvedComponents (self):
        """Returns a reference to the list of unresolved components."""
        return self.__unresolvedComponents

def ResolveSiblingNamespaces (sibling_namespaces, origin_uid):
    for ns in sibling_namespaces:
        ns.configureCategories([NamespaceArchive._AnonymousCategory()])
        ns.validateComponentModel()

    need_resolved = set(sibling_namespaces)
    while need_resolved:
        new_nr = set()
        for ns in need_resolved:
            if not ns.needsResolution():
                continue
            #print 'Attempting resolution %s' % (ns.uri(),)
            if not ns.resolveDefinitions(allow_unresolved=True):
                print 'Holding incomplete resolution %s' % (ns.uri(),)
                new_nr.add(ns)
        if need_resolved == new_nr:
            raise pyxb.LogicError('Unexpected external dependency in sibling namespaces: %s' % ("\n  ".join( [str(_ns) for _ns in need_resolved ]),))
        need_resolved = new_nr

    for ns in sibling_namespaces:
        ns.updateOriginUID(origin_uid)

class _ComponentDependency_mixin (pyxb.cscRoot):
    """Mix-in for components that can depend on other components."""
    # Cached frozenset of components on which this component depends.
    __bindingRequires = None

    def _resetClone_csc (self, **kw):
        """CSC extension to reset fields of a component.  This one clears
        dependency-related data, since the clone will have to revise its
        dependencies.
        @rtype: C{None}"""
        getattr(super(_ComponentDependency_mixin, self), '_resetClone_csc', lambda *_args, **_kw: None)(**kw)
        self.__bindingRequires = None

    def bindingRequires (self, reset=False, include_lax=False):
        """Return a set of components upon whose bindings this component's
        bindings depend.

        For example, bindings that are extensions or restrictions depend on
        their base types.  Complex type definition bindings require that the
        types of their attribute declarations be available at the class
        definition, and the types of their element declarations in the
        postscript.

        @keyword include_lax: if C{False} (default), only the requirements of
        the class itself are returned.  If C{True}, all requirements are
        returned.
        @rtype: C{set(L{pyxb.xmlschema.structures._SchemaComponent_mixin})}
        """
        if reset or (self.__bindingRequires is None):
            if isinstance(self, _Resolvable_mixin) and not (self.isResolved()):
                raise pyxb.LogicError('Unresolved %s in %s: %s' % (self.__class__.__name__, self._namespaceContext().targetNamespace(), self.name()))
            self.__bindingRequires = self._bindingRequires_vx(include_lax)
        return self.__bindingRequires

    def _bindingRequires_vx (self, include_lax):
        """Placeholder for subclass method that identifies the necessary components.

        @note: Override in subclasses.

        @return: The component instances on which this component depends
        @rtype: C{frozenset}
        @raise LogicError: A subclass failed to implement this method
        """
        raise LogicError('%s does not implement _bindingRequires_vx' % (self.__class__,))

class _NamespaceComponentAssociation_mixin (pyxb.cscRoot):
    """Mix-in for managing components defined within this namespace.

    The component set includes not only top-level named components (such as
    those accessible through category maps), but internal anonymous
    components, such as those involved in representing the content model of a
    complex type definition..  We need to be able to get a list of these
    components, sorted in dependency order, so that generated bindings do not
    attempt to refer to a binding that has not yet been generated."""

    # A set containing all components, named or unnamed, that belong to this
    # namespace.
    __components = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles data related to component association with a
        namespace."""
        getattr(super(_NamespaceComponentAssociation_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__components = set()

    def _associateComponent (self, component):
        """Record that the responsibility for the component belongs to this namespace."""
        self._activate()
        assert self.__components is not None
        assert isinstance(component, _ComponentDependency_mixin)
        assert component not in self.__components
        self.__components.add(component)

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition in the set of associated components.

        @raise KeyError: C{existing_def} is not in the set of components."""
        
        self.__components.remove(existing_def)
        if replacement_def is not None:
            self.__components.add(replacement_def)
        return getattr(super(_NamespaceComponentAssociation_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    def components (self):
        """Return a frozenset of all components, named or unnamed, belonging
        to this namespace."""
        return frozenset(self.__components)

    def _releaseNamespaceContexts (self):
        for c in self.__components:
            c._clearNamespaceContext()

    def updateOriginUID (self, origin_uid):
        for c in self.__components:
            c._setObjectOriginUIDIfUndefined(origin_uid)

class Namespace (_NamespaceCategory_mixin, _NamespaceResolution_mixin, _NamespaceComponentAssociation_mixin, _NamespaceArchivable_mixin):
    """Represents an XML namespace (a URI).

    There is at most one L{Namespace} class instance per namespace (URI).  The
    instance also supports associating arbitrary L{maps<NamedObjectMap>} from
    names to objects, in separate categories.  The default categories are
    configured externally; for example, the
    L{Schema<pyxb.xmlschema.structures.Schema>} component defines a category
    for each named component in XMLSchema, and the customizing subclass for
    WSDL definitions adds categories for the service bindings, messages, etc.

    Namespaces can be written to and loaded from pickled files.  See
    L{NamespaceArchive} for information.
    """

    # The URI for the namespace.  If the URI is None, this is an absent
    # namespace.
    __uri = None

    # An identifier, unique within a program using PyXB, used to distinguish
    # absent namespaces.  Currently this value is not accessible to the user,
    # and exists solely to provide a unique identifier when printing the
    # namespace as a string.  The class variable is used as a one-up counter,
    # which is assigned to the instance variable when an absent namespace
    # instance is created.
    __absentNamespaceID = 0

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml and xmlns.
    __boundPrefix = None

    # A prefix set as a preferred prefix, generally by processing a namespace
    # declaration.
    __prefix = None

    # A map from URIs to Namespace instances.  Namespaces instances
    # must be unique for their URI.  See __new__().
    __Registry = { }

    # A set of all absent namespaces created.
    __AbsentNamespaces = set()

    # Optional URI specifying the source for a (primary) schema for this namespace
    __schemaLocation = None

    # Optional description of the namespace
    __description = None

    # Indicates whether this namespace is built-in to the system
    __isBuiltinNamespace = False

    # Indicates whether this namespace is undeclared (available always)
    __isUndeclaredNamespace = False

    # Indicates whether this namespace was loaded from an archive
    __isLoadedNamespace = False

    # Archive from which the namespace can be read, or None if no archive
    # defines this namespace.
    __namespaceArchive = None

    # Indicates whether this namespace has been written to an archive
    __hasBeenArchived = False

    # A string denoting the path by which this namespace is imported into
    # generated Python modules
    __modulePath = None

    # A set of options defining how the Python bindings for this namespace
    # were generated.  Not currently used, since we don't have different
    # binding configurations yet.
    __bindingConfiguration = None
 
    # The namespace to use as the default namespace when constructing the
    # The namespace context used when creating built-in components that belong
    # to this namespace.  This is used to satisfy the low-level requirement
    # that all schema components have a namespace context; normally, that
    # context is built dynamically from the schema element.
    __initialNamespaceContext = None

    # The default_namespace parameter when creating the initial namespace
    # context.  Only used with built-in namespaces.
    __contextDefaultNamespace = None

    # The map from prefixes to namespaces as defined by the schema element for
    # this namespace.  Only used with built-in namespaces.
    __contextInScopeNamespaces = None

    @classmethod
    def _NamespaceForURI (cls, uri):
        """If a Namespace instance for the given URI exists, return it; otherwise return None.

        Note; Absent namespaces are not stored in the registry.  If you use
        one (e.g., for a schema with no target namespace), don't lose hold of
        it."""
        assert uri is not None
        return cls.__Registry.get(uri, None)


    def __getnewargs__ (self):
        """Pickling support.

        To ensure that unpickled Namespace instances are unique per
        URI, we ensure that the routine that creates unpickled
        instances knows what it's supposed to return."""
        return (self.uri(),)

    def __new__ (cls, *args, **kw):
        """Pickling and singleton support.

        This ensures that no more than one Namespace instance exists
        for any given URI.  We could do this up in __init__, but that
        doesn't normally get called when unpickling instances; this
        does.  See also __getnewargs__()."""
        (uri,) = args
        if not (uri in cls.__Registry):
            instance = object.__new__(cls)
            # Do this one step of __init__ so we can do checks during unpickling
            instance.__uri = uri
            instance._reset()
            # Absent namespaces are not stored in the registry.
            if uri is None:
                cls.__AbsentNamespaces.add(instance)
                return instance
            cls.__Registry[uri] = instance
        return cls.__Registry[uri]

    @classmethod
    def AvailableNamespaces (cls):
        """Return a set of all Namespace instances defined so far."""
        return cls.__AbsentNamespaces.union(cls.__Registry.values())

    def __init__ (self, uri,
                  schema_location=None,
                  description=None,
                  builtin_namespace=None,
                  is_undeclared_namespace=False,
                  is_loaded_namespace=False,
                  bound_prefix=None,
                  default_namespace=None,
                  in_scope_namespaces=None):
        """Create a new Namespace.

        The URI must be non-None, and must not already be assigned to
        a Namespace instance.  See NamespaceForURI().
        
        User-created Namespace instances may also provide a
        schemaLocation and a description.

        Users should never provide a builtin_namespace parameter.
        """

        # New-style superclass invocation
        super(Namespace, self).__init__()

        self.__contextDefaultNamespace = default_namespace
        self.__contextInScopeNamespaces = in_scope_namespaces

        # Make sure that we're not trying to do something restricted to
        # built-in namespaces
        is_builtin_namespace = not (builtin_namespace is None)
        if not is_builtin_namespace:
            if bound_prefix is not None:
                raise pyxb.LogicError('Only permanent Namespaces may have bound prefixes')

        # We actually set the uri when this instance was allocated;
        # see __new__().
        assert self.__uri == uri
        self.__boundPrefix = bound_prefix
        self.__schemaLocation = schema_location
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace
        self.__builtinNamespaceVariable = builtin_namespace
        self.__isUndeclaredNamespace = is_undeclared_namespace
        self.__isLoadedNamespace = is_loaded_namespace

        self._reset()

        assert (self.__uri is None) or (self.__Registry[self.__uri] == self)

    def _reset (self):
        assert not self.isActive()
        getattr(super(Namespace, self), '_reset', lambda *args, **kw: None)()
        self.__initialNamespaceContext = None
        self.__schemas = set()
        self.__schemaMap = { }

    def uri (self):
        """Return the URI for the namespace represented by this instance.

        If the URI is None, this is an absent namespace, used to hold
        declarations not associated with a namespace (e.g., from schema with
        no target namespace)."""
        return self.__uri

    def setPrefix (self, prefix):
        if self.__boundPrefix is not None:
            raise pyxb.NamespaceError(self, 'Cannot change the prefix of a bound namespace')
        self.__prefix = prefix
        return self

    def prefix (self):
        if self.__boundPrefix:
            return self.__boundPrefix
        return self.__prefix

    def isAbsentNamespace (self):
        """Return True iff this namespace is an absent namespace.

        Absent namespaces have no namespace URI; they exist only to
        hold components created from schemas with no target
        namespace."""
        return self.__uri is None

    @classmethod
    def CreateAbsentNamespace (cls):
        """Create an absent namespace.

        Use this instead of the standard constructor, in case we need
        to augment it with a uuid or the like."""
        rv = Namespace(None)
        rv.__absentNamespaceID = cls.__absentNamespaceID
        cls.__absentNamespaceID += 1
        return rv

    def _overrideAbsentNamespace (self, uri):
        assert self.isAbsentNamespace()
        self.__uri = uri

    def boundPrefix (self):
        """Return the standard prefix to be used for this namespace.

        Only a few namespace prefixes are bound to namespaces: xml and xmlns
        are two.  In all other cases, this method should return None.  The
        infrastructure attempts to prevent user creation of Namespace
        instances that have bound prefixes."""
        return self.__boundPrefix

    def isBuiltinNamespace (self):
        """Return True iff this namespace was defined by the infrastructure.

        That is the case for all namespaces in the Namespace module."""
        return self.__isBuiltinNamespace

    def builtinNamespaceRepresentation (self):
        assert self.__builtinNamespaceVariable is not None
        return 'pyxb.namespace.%s' % (self.__builtinNamespaceVariable,)

    def isUndeclaredNamespace (self):
        """Return True iff this namespace is always available
        regardless of whether there is a declaration for it.

        This is the case only for the
        xml(http://www.w3.org/XML/1998/namespace) and
        xmlns(http://www.w3.org/2000/xmlns/) namespaces."""
        return self.__isUndeclaredNamespace

    def isLoadedNamespace (self):
        """Return C{True} iff this namespace was loaded from a namespace archive."""
        return self.__isLoadedNamespace

    def hasBeenArchived (self):
        """Return C{True} iff this namespace has been saved to a namespace archive.
        See also L{isLoadedNamespace}."""
        return self.__hasBeenArchived

    def modulePath (self):
        return self.__modulePath

    def setModulePath (self, module_path):
        self.__modulePath = module_path
        return self.modulePath()

    def module (self):
        """Return a reference to the Python module that implements
        bindings for this namespace."""
        return self.__module
    def _setModule (self, module):
        """Set the module to use for Python bindings for this namespace.

        Should only be called by generated code."""
        self.__module = module
        return self
    __module = None

    def addSchema (self, schema):
        sl = schema.schemaLocation()
        if sl is not None:
            assert not (sl in self.__schemaMap), '%s already in schema list for %s' % (sl, self)
            self.__schemaMap[sl] = schema
        self.__schemas.add(schema)
    __schemaMap = None

    def lookupSchemaByLocation (self, schema_location):
        return self.__schemaMap.get(schema_location)

    def schemas (self):
        return self.__schemas
    __schemas = None

    def schemaLocation (self, schema_location=None):
        """Get, or set, a URI that says where the XML document defining the namespace can be found."""
        if schema_location is not None:
            self.__schemaLocation = schema_location
        return self.__schemaLocation

    def description (self, description=None):
        """Get, or set, a textual description of the namespace."""
        if description is not None:
            self.__description = description
        return self.__description

    def nodeIsNamed (self, node, *local_names):
        return (node.namespaceURI == self.uri()) and (node.localName in local_names)

    def createExpandedName (self, local_name):
        return ExpandedName(self, local_name)

    def _getState_csc (self, kw):
        kw.update({
            'schemaLocation': self.__schemaLocation,
            'description': self.__description,
            'prefix': self.__prefix,
            'modulePath' : self.__modulePath,
            'bindingConfiguration': self.__bindingConfiguration,
            })
        return getattr(super(Namespace, self), '_getState_csc', lambda _kw: _kw)(kw)

    def _setState_csc (self, kw):
        self.__isLoadedNamespace = True
        self.__schemaLocation = kw['schemaLocation']
        self.__description = kw['description']
        self.__prefix = kw['prefix']
        assert (self.__modulePath is None) or (self.__modulePath == kw.get('modulePath'))
        self.__modulePath = kw['modulePath']
        self.__bindingConfiguration = kw['bindingConfiguration']
        return getattr(super(Namespace, self), '_setState_csc', lambda _kw: self)(kw)

    def __getstate__ (self):
        """Support pickling.

        Because namespace instances must be unique, we represent them
        as their URI and any associated (non-bound) information.  This
        way allows the unpickler to either identify an existing
        Namespace instance for the URI, or create a new one, depending
        on whether the namespace has already been encountered."""
        if self.uri() is None:
            raise pyxb.LogicError('Illegal to serialize absent namespaces')
        kw = self._getState_csc({ })
        args = ( self.__uri, )
        return ( args, kw )

    def __setstate__ (self, state):
        """Support pickling."""
        ( args, kw ) = state
        ( uri, ) = args
        assert self.__uri == uri
        # If this namespace hasn't been activated, do so now, using the
        # archived information which includes referenced namespaces.
        if not self.isActive(True):
            self._setState_csc(kw)

    def _defineBuiltins_ox (self, structures_module):
        pass

    __definedBuiltins = False
    def _defineBuiltins (self, structures_module):
        if not self.__definedBuiltins:
            global BuiltInObjectUID
            
            self._defineBuiltins_ox(structures_module)
            self.updateOriginUID(BuiltInObjectUID)
            self.__definedBuiltins = True
        return self

    def _defineSchema_overload (self, structures_module):
        """Attempts to load the named objects held in this namespace.

        The base class implementation looks at the set of available archived
        namespaces, and if one contains this namespace unserializes its named
        object maps.

        Sub-classes may choose to look elsewhere, if this version fails or
        before attempting it.

        There is no guarantee that any particular category of named object has
        been located when this returns.  Caller must check.
        """
        if self.archive() is not None:
            self.archive().readNamespaces()
        self._activate()

    __didValidation = False
    __inValidation = False
    def validateComponentModel (self, structures_module=None):
        """Ensure this namespace is ready for use.

        If the namespace does not have a map of named objects, the system will
        attempt to load one.
        """
        if not self.__didValidation:
            assert not self.__inValidation, 'Nested validation of %s' % (self.uri(),)
            if structures_module is None:
                import pyxb.xmlschema.structures as structures_module
            self._defineBuiltins(structures_module)
            try:
                self.__inValidation = True
                self._defineSchema_overload(structures_module)
                self.__didValidation = True
            finally:
                self.__inValidation = False

    def _replaceComponent (self, existing_def, replacement_def):
        """Replace the existing definition with another.

        This is used in a situation where building the component model
        resulted in a new component instance being created and registered, but
        for which an existing component is to be preferred.  An example is
        when parsing the schema for XMLSchema itself: the built-in datatype
        components should be retained instead of the simple type definition
        components dynamically created from the schema.

        By providing the value C{None} as the replacement definition, this can
        also be used to remove components.

        @note: Invoking this requires scans of every item in every category
        map in the namespace.

        @return: C{replacement_def}
        """
        # We need to do replacements in the category map handler, the
        # resolver, and the component associator.
        return self._replaceComponent_csc(existing_def, replacement_def)

    def initialNamespaceContext (self):
        """Obtain the namespace context to be used when creating components in this namespace.

        Usually applies only to built-in namespaces, but is also used in the
        autotests when creating a namespace without a xs:schema element.  .
        Note that we must create the instance dynamically, since the
        information that goes into it has cross-dependencies that can't be
        resolved until this module has been completely loaded."""
        
        if self.__initialNamespaceContext is None:
            isn = { }
            if self.__contextInScopeNamespaces is not None:
                for (k, v) in self.__contextInScopeNamespaces.items():
                    isn[k] = self.__identifyNamespace(v)
            kw = { 'target_namespace' : self
                 , 'default_namespace' : self.__identifyNamespace(self.__contextDefaultNamespace)
                 , 'in_scope_namespaces' : isn }
            self.__initialNamespaceContext = NamespaceContext(None, **kw)
        return self.__initialNamespaceContext


    def __identifyNamespace (self, nsval):
        """Identify the specified namespace, which should be a built-in.

        Normally we can just use a reference to the Namespace module instance,
        but when creating those instances we sometimes need to refer to ones
        for which the instance has not yet been created.  In that case, we use
        the name of the instance, and resolve the namespace when we need to
        create the initial context."""
        if nsval is None:
            return self
        if isinstance(nsval, (str, unicode)):
            nsval = globals().get(nsval)
        if isinstance(nsval, Namespace):
            return nsval
        raise pyxb.LogicError('Cannot identify namespace from %s' % (nsval,))

    def __str__ (self):
        if self.__uri is None:
            return 'AbsentNamespace%d' % (self.__absentNamespaceID,)
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        return rv

def NamespaceInstance (namespace):
    """Get a namespace instance for the given namespace.

    This is used when it is unclear whether the namespace is specified by URI
    or by instance or by any other mechanism we might dream up in the
    future."""
    if isinstance(namespace, Namespace):
        return namespace
    if isinstance(namespace, basestring):
        return NamespaceForURI(namespace, True)
    raise pyxb.LogicError('Cannot identify namespace from value of type %s' % (type(namespace),))

def NamespaceForURI (uri, create_if_missing=False):
    """Given a URI, provide the L{Namespace} instance corresponding to it.

    This can only be used to lookup or create real namespaces.  To create
    absent namespaces, use L{CreateAbsentNamespace}.

    @param uri: The URI that identifies the namespace
    @type uri: A non-empty C{str} or C{unicode} string
    @keyword create_if_missing: If C{True}, a namespace for the given URI is
    created if one has not already been registered.  Default is C{False}.
    @type create_if_missing: C{bool}
    @return: The Namespace corresponding to C{uri}, if available
    @rtype: L{Namespace} or C{None}
    @raise pyxb.LogicError: The uri is not a non-empty string
    """
    if not isinstance(uri, (str, unicode)):
        raise pyxb.LogicError('Cannot lookup absent namespaces')
    if 0 == len(uri):
        raise pyxb.LogicError('Namespace URIs must not be empty strings')
    rv = Namespace._NamespaceForURI(uri)
    if (rv is None) and create_if_missing:
        rv = Namespace(uri)
    return rv

def CreateAbsentNamespace ():
    """Create an absent namespace.

    Use this when you need a namespace for declarations in a schema with no
    target namespace.  Absent namespaces are not stored in the infrastructure;
    it is your responsibility to hold on to the reference you get from this,
    because you won't be able to look it up."""
    return Namespace.CreateAbsentNamespace()

__NamespaceArchives = None
"""A mapping from namespace URIs to names of files which appear to
provide a serialized version of the namespace with schema."""

def LoadableNamespaces ():
    available = set()
    for ns_archive in NamespaceArchives():
        available.update(ns_archive.namespaces())
    return available

def NamespaceArchives (archive_path=None, reset=False):
    """Scan for available archves, and associate them with any namespace that has not already been loaded.

    @keyword archive_path: A colon-separated list of paths in which namespace
    archives can be found; see L{PathEnvironmentVariable}.  Defaults to
    L{GetArchivePath()}.  If not defaulted, C{reset} will be forced to
    C{True}.

    @keyword reset: If C{False} (default), the most recently read set of
    archives is returned; if C{True}, the archive path is re-scanned and the
    namespace associations validated."""
    
    global __NamespaceArchives
    if archive_path is None:
        archive_path = GetArchivePath()
    else:
        reset = True
    if (__NamespaceArchives is None) or reset:
        # Look for pre-existing pickled schema
        __NamespaceArchives = set()
        for bp in archive_path.split(':'):
            if '+' == bp:
                bp = DefaultArchivePath
            files = []
            try:
                files = os.listdir(bp)
            except OSError, e:
                files = []
            for fn in files:
                if fnmatch.fnmatch(fn, '*.wxs'):
                    afn = os.path.join(bp, fn)
                    try:
                        archive = NamespaceArchive(archive_path=afn)
                        __NamespaceArchives.add(archive)
                        #print 'Archive %s has: %s' % (archive, "\n   ".join([ '%s @ %s' % (_ns, _ns.archive()) for _ns in archive.namespaces()]))
                    except pickle.UnpicklingError, e:
                        print 'Cannot use archive %s: %s' % (afn, e)
                    except pyxb.NamespaceArchiveError, e:
                        print 'Cannot use archive %s: %s' % (afn, e)
    return __NamespaceArchives

class _XMLSchema_instance (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema Instance namespace."""

    def _defineBuiltins_ox (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        assert structures_module is not None
        schema = structures_module.Schema(namespace_context=self.initialNamespaceContext(), schema_location="URN:noLocation:xsi")
        type = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('type', self))
        nil = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('nil', self))
        schema_location = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('schemaLocation', self))
        no_namespace_schema_location = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self))
        return self

class _XML (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XML (xml) namespace."""

    def _defineBuiltins_ox (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        assert structures_module is not None
        import pyxb.binding.datatypes as xsd
        import pyxb.binding.facets as xsdf
        schema = structures_module.Schema(namespace_context=self.initialNamespaceContext(), schema_location="URN:noLocation:XML")
        base = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('base', self, std=xsd.anyURI.SimpleTypeDefinition()))
        id = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('id', self, std=xsd.ID.SimpleTypeDefinition()))
        #  std=xsdf._WhiteSpace_enum.SimpleTypeDefinition()))
        space = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('space', self))
        lang = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('lang', self, std=xsd.anySimpleType.SimpleTypeDefinition()))

        specialAttrs = schema._addNamedComponent(structures_module.AttributeGroupDefinition.CreateBaseInstance('specialAttrs', self, [
                    structures_module.AttributeUse.CreateBaseInstance(self, space),
                    structures_module.AttributeUse.CreateBaseInstance(self, base),
                    structures_module.AttributeUse.CreateBaseInstance(self, lang)
                    ]))
        return self

class _XMLSchema (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema namespace.

    The types are defined when L{pyxb.xmlschema.structures} is imported.
    """

    def _defineBuiltins_ox (self, structures_module):
        """Register the built-in types into the XMLSchema namespace."""

        # Defer the definitions to the structures module
        assert structures_module is not None
        structures_module._AddSimpleTypes(self)

        # A little validation here
        assert structures_module.ComplexTypeDefinition.UrTypeDefinition() == self.typeDefinitions()['anyType']
        assert structures_module.SimpleTypeDefinition.SimpleUrTypeDefinition() == self.typeDefinitions()['anySimpleType']

        # Provide access to the binding classes
        self.configureCategories(['typeBinding', 'elementBinding'])
        for ( en, td ) in self.typeDefinitions().items():
            if td.pythonSupport() is not None:
                self.addCategoryObject('typeBinding', en, td.pythonSupport())

def AvailableForLoad ():
    """Return a list of namespace URIs for which we may be able to load the
    namespace contents from a pre-parsed file.  The corresponding L{Namespace}
    can be retrieved using L{NamespaceForURI}, and the declared objects in
    that namespace loaded with L{Namespace.validateComponentModel}.

    Note that success of the load is not guaranteed if the packed file
    is not compatible with the schema class being used."""
    # Invoke this to ensure we have searched for loadable namespaces
    return _LoadableNamespaceMap().keys()

XMLSchema_instance = _XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                         description='XML Schema Instance',
                                         builtin_namespace='XMLSchema_instance')
"""Namespace and URI for the XMLSchema Instance namespace.  This is always
built-in, and does not (cannot) have an associated schema."""

XMLNamespaces = Namespace('http://www.w3.org/2000/xmlns/',
                          description='Namespaces in XML',
                          builtin_namespace='XMLNamespaces',
                          bound_prefix='xmlns')
"""Namespaces in XML.  Not really a namespace, but is always available as C{xmlns}."""

XMLSchema = _XMLSchema('http://www.w3.org/2001/XMLSchema',
                       schema_location='http://www.w3.org/2001/XMLSchema.xsd',
                       description='XML Schema',
                       builtin_namespace='XMLSchema',
                       in_scope_namespaces = { 'xs' : None })
"""Namespace and URI for the XMLSchema namespace (often C{xs}, or C{xsd})"""
XMLSchema.setModulePath('pyxb.binding.datatypes')

XHTML = Namespace('http://www.w3.org/1999/xhtml',
                  description='Family of document types that extend HTML',
                  schema_location='http://www.w3.org/1999/xhtml.xsd',
                  builtin_namespace='XHTML',
                  default_namespace=XMLSchema)
"""There really isn't a schema for this, but it's used as the default
namespace in the XML schema, so define it."""

XML = _XML('http://www.w3.org/XML/1998/namespace',
           description='XML namespace',
           schema_location='http://www.w3.org/2001/xml.xsd',
           builtin_namespace='XML',
           is_undeclared_namespace=True,
           bound_prefix='xml',
           default_namespace=XHTML,
           in_scope_namespaces = { 'xs' : XMLSchema })
"""Namespace and URI for XML itself (always available as C{xml})"""
XML.setModulePath('pyxb.standard.bindings.xml_')

XMLSchema_hfp = Namespace('http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          description='Facets appearing in appinfo section',
                          schema_location='http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          builtin_namespace='XMLSchema_hfp',
                          default_namespace=XMLSchema,
                          in_scope_namespaces = { 'hfp' : None
                                                , 'xhtml' : XHTML })
"""Elements appearing in appinfo elements to support data types."""

# List of built-in namespaces.
BuiltInNamespaces = [
  XMLSchema_instance,
  XMLSchema_hfp,
  XMLSchema,
  XMLNamespaces,
  XML,
  XHTML
]

__InitializedBuiltinNamespaces = False

def _InitializeBuiltinNamespaces (structures_module):
    """Invoked at the end of the L{pyxb.xmlschema.structures} module to
    initialize the component models of the built-in namespaces.

    @param structures_module: The L{pyxb.xmlschema.structures} module may not
    be importable by that name at the time this is invoked (because it is
    still being processed), so it gets passed in as a parameter."""
    global __InitializedBuiltinNamespaces
    if not __InitializedBuiltinNamespaces:
        __InitializedBuiltinNamespaces = True
        [ _ns._defineBuiltins(structures_module) for _ns in BuiltInNamespaces ]

# Set up the prefixes for xml, xmlns, etc.
_UndeclaredNamespaceMap = { }
[ _UndeclaredNamespaceMap.setdefault(_ns.boundPrefix(), _ns) for _ns in BuiltInNamespaces if _ns.isUndeclaredNamespace() ]

class NamespaceContext (object):
    """Records information associated with namespaces at a DOM node.
    """

    # Support for holding onto referenced namespaces until we have a target
    # namespace to give them to.
    __pendingReferencedNamespaces = None
    
    def defaultNamespace (self):
        """The default namespace in effect at this node.  E.g., C{xmlns="URN:default"}."""
        return self.__defaultNamespace
    __defaultNamespace = None

    def targetNamespace (self):
        """The target namespace in effect at this node.  Usually from the
        C{targetNamespace} attribute.  If no namespace is specified for the
        schema, an absent namespace was assigned upon creation and will be
        returned."""
        return self.__targetNamespace
    __targetNamespace = None

    def inScopeNamespaces (self):
        """Map from prefix strings to L{Namespace} instances associated with those
        prefixes.  The prefix C{None} identifies the default namespace."""
        return self.__inScopeNamespaces
    __inScopeNamespaces = None

    def prefixForNamespace (self, namespace):
        """Return a prefix associated with the given namespace in this
        context, or None if the namespace is the default or is not in
        scope."""
        for (pfx, ns) in self.__inScopeNamespaces.items():
            if namespace == ns:
                return pfx
        return None

    def attributeMap (self):
        """Map from L{ExpandedName} instances (for non-absent namespace) or
        C{str} or C{unicode} values (for absent namespace) to the value of the
        named attribute.

        Only defined if the context was built from a DOM node."""
        return self.__attributeMap
    __attributeMap = None

    @classmethod
    def GetNodeContext (cls, node, **kw):
        """Get the L{NamespaceContext} instance that was assigned to the node.

        If none has been assigned and keyword parameters are present, create
        one treating this as the root node and the keyword parameters as
        configuration information (e.g., default_namespace).

        @raise pyxb.LogicError: no context is available and the keywords
        required to create one were not provided
        """
        try:
            return node.__namespaceContext
        except AttributeError:
            return NamespaceContext(node, **kw)

    def processXMLNS (self, prefix, uri):
        if not self.__mutableInScopeNamespaces:
            self.__inScopeNamespaces = self.__inScopeNamespaces.copy()
            self.__mutableInScopeNamespaces = True
        if uri:
            if prefix is None:
                ns = self.__defaultNamespace = NamespaceForURI(uri, create_if_missing=True)
                self.__inScopeNamespaces[None] = self.__defaultNamespace
            else:
                ns = NamespaceForURI(uri, create_if_missing=True)
                self.__inScopeNamespaces[prefix] = ns
                #if ns.prefix() is None:
                #    ns.setPrefix(prefix)
                # @todo should we record prefix in namespace so we can use it
                # during generation?  I'd rather make the user specify what to
                # use.
            if self.__targetNamespace:
                self.__targetNamespace._referenceNamespace(ns)
            else:
                self.__pendingReferencedNamespaces.add(ns)
        else:
            # NB: XMLNS 6.2 says that you can undefine a default
            # namespace, but does not say anything explicitly about
            # undefining a prefixed namespace.  XML-Infoset 2.2
            # paragraph 6 implies you can do this, but expat blows up
            # if you try it.  I don't think it's legal.
            if prefix is not None:
                raise pyxb.NamespaceError(self, 'Attempt to undefine non-default namespace %s' % (attr.localName,))
            self.__defaultNamespace = None
            self.__inScopeNamespaces.pop(None, None)

    def finalizeTargetNamespace (self, tns_uri=None):
        if tns_uri is not None:
            assert 0 < len(tns_uri)
            self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
            #assert self.__defaultNamespace is not None
        elif self.__targetNamespace is None:
            if tns_uri is None:
                self.__targetNamespace = CreateAbsentNamespace()
            else:
                self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
            if self.__defaultNamespace is None:
                self.__defaultNamespace = self.__targetNamespace
        if self.__pendingReferencedNamespaces is not None:
            [ self.__targetNamespace._referenceNamespace(_ns) for _ns in self.__pendingReferencedNamespaces ]
            self.__pendingReferencedNamespace = None
        assert self.__targetNamespace is not None

    def __init__ (self, dom_node=None, parent_context=None, recurse=True, default_namespace=None, target_namespace=None, in_scope_namespaces=None):
        """Determine the namespace context that should be associated with the
        given node and, optionally, its element children.

        @param dom_node: The DOM node
        @type dom_node: C{xml.dom.Element}
        @keyword parent_context: Optional value that specifies the context
        associated with C{dom_node}'s parent node.  If not provided, only the
        C{xml} namespace is in scope.
        @type parent_context: L{NamespaceContext}
        @keyword recurse: If True (default), create namespace contexts for all
        element children of C{dom_node}
        @type recurse: C{bool}
        @keyword default_namespace: Optional value to set as the default
        namespace.  Values from C{parent_context} would override this, as
        would an C{xmlns} attribute in the C{dom_node}.
        @type default_namespace: L{NamespaceContext}
        @keyword target_namespace: Optional value to set as the target
        namespace.  Values from C{parent_context} would override this, as
        would a C{targetNamespace} attribute in the C{dom_node}
        @type target_namespace: L{NamespaceContext}
        @keyword in_scope_namespaces: Optional value to set as the initial set
        of in-scope namespaces.  The always-present namespaces are added to
        this if necessary.
        @type in_scope_namespaces: C{dict} mapping C{string} to L{Namespace}.
        """
        global _UndeclaredNamespaceMap
        if dom_node is not None:
            dom_node.__namespaceContext = self

        self.__defaultNamespace = default_namespace
        self.__targetNamespace = target_namespace
        self.__attributeMap = { }
        self.__inScopeNamespaces = _UndeclaredNamespaceMap
        self.__mutableInScopeNamespaces = False

        if in_scope_namespaces is not None:
            if parent_context is not None:
                raise LogicError('Cannot provide both parent_context and in_scope_namespaces')
            self.__inScopeNamespaces = _UndeclaredNamespaceMap.copy()
            self.__inScopeNamespaces.update(in_scope_namespaces)
            self.__mutableInScopeNamespaces = True
        
        if parent_context is not None:
            self.__inScopeNamespaces = parent_context.inScopeNamespaces()
            self.__mutableInScopeNamespaces = False
            self.__defaultNamespace = parent_context.defaultNamespace()
            self.__targetNamespace = parent_context.targetNamespace()
            
        if self.__targetNamespace is None:
            self.__pendingReferencedNamespaces = set()
        if dom_node is not None:
            for ai in range(dom_node.attributes.length):
                attr = dom_node.attributes.item(ai)
                if XMLNamespaces.uri() == attr.namespaceURI:
                    prefix = attr.localName
                    if 'xmlns' == prefix:
                        prefix = None
                    self.processXMLNS(prefix, attr.value)
                else:
                    if attr.namespaceURI is not None:
                        uri = NamespaceForURI(attr.namespaceURI, create_if_missing=True)
                        key = ExpandedName(uri, attr.localName)
                    else:
                        key = attr.localName
                    self.__attributeMap[key] = attr.value
        
        self.finalizeTargetNamespace(self.attributeMap().get('targetNamespace'))

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        from xml.dom import Node
        if recurse and (dom_node is not None):
            assert Node.ELEMENT_NODE == dom_node.nodeType
            for cn in dom_node.childNodes:
                if Node.ELEMENT_NODE == cn.nodeType:
                    NamespaceContext(cn, self, True)

    def interpretQName (self, name):
        """Convert the provided name into an L{ExpandedName}, i.e. a tuple of
        L{Namespace} and local name.

        If the name includes a prefix, that prefix must map to an in-scope
        namespace in this context.  Absence of a prefix maps to
        L{defaultNamespace()}, which must be provided (or defaults to the
        target namespace, if that is absent).
        
        @param name: A QName.
        @type name: C{str} or C{unicode}
        @return: An L{ExpandedName} tuple: ( L{Namespace}, C{str} )
        @raise pyxb.SchemaValidationError: The prefix is not in scope
        @raise pyxb.SchemaValidationError: No prefix is given and the default namespace is absent
        """
        assert isinstance(name, (str, unicode))
        if 0 <= name.find(':'):
            (prefix, local_name) = name.split(':', 1)
            assert self.inScopeNamespaces() is not None
            namespace = self.inScopeNamespaces().get(prefix)
            if namespace is None:
                raise pyxb.SchemaValidationError('No namespace declared for QName %s prefix' % (name,))
        else:
            local_name = name
            namespace = self.defaultNamespace()
            if namespace is None:
                raise pyxb.SchemaValidationError('QName %s with absent default namespace' % (local_name,))
        # Anything we're going to look stuff up in requires a component model.
        # Make sure we can load one, unless we're looking up in the thing
        # we're constructing (in which case it's being built right now).
        if (namespace != self.targetNamespace()):
            namespace.validateComponentModel()
        return ExpandedName(namespace, local_name)

    def queueForResolution (self, component):
        """Forwards to L{queueForResolution()<Namespace.queueForResolution>} in L{targetNamespace()}."""
        assert isinstance(component, _Resolvable_mixin)
        return self.targetNamespace().queueForResolution(component)

class NamespaceDependencies (object):

    def rootNamespaces (self):
        return self.__rootNamespaces
    __rootNamespaces = None

    def namespaceGraph (self, reset=False):
        if reset or (self.__namespaceGraph is None):
            self.__namespaceGraph = pyxb.utils.utility.Graph()
            map(self.__namespaceGraph.addRoot, self.rootNamespaces())

            # Make sure all referenced namespaces have valid components
            need_check = self.__rootNamespaces.copy()
            done_check = set()
            while 0 < len(need_check):
                ns = need_check.pop()
                ns.validateComponentModel()
                self.__namespaceGraph.addNode(ns)
                for rns in ns.referencedNamespaces().union(ns.importedNamespaces()):
                    self.__namespaceGraph.addEdge(ns, rns)
                    if not rns in done_check:
                        need_check.add(rns)
                if not ns.hasSchemaComponents():
                    print 'WARNING: Referenced %s has no schema components' % (ns.uri(),)
                done_check.add(ns)
            assert done_check == self.__namespaceGraph.nodes()

        return self.__namespaceGraph
    __namespaceGraph = None

    def namespaceOrder (self, reset=False):
        return self.namespaceGraph(reset).sccOrder()

    def siblingsFromGraph (self, reset=False):
        siblings = set()
        ns_graph = self.namespaceGraph(reset)
        for ns in self.__rootNamespaces:
            ns_siblings = ns_graph.sccMap().get(ns)
            if ns_siblings is not None:
                siblings.update(ns_siblings)
            else:
                siblings.add(ns)
        return siblings

    def siblingNamespaces (self):
        if self.__siblingNamespaces is None:
            self.__siblingNamespaces = self.siblingsFromGraph()
        return self.__siblingNamespaces

    def setSiblingNamespaces (self, sibling_namespaces):
        self.__siblingNamespaces = sibling_namespaces

    __siblingNamespaces = None

    def schemaDefinedNamespaces (self, reset=False):
        return set([ _ns for _ns in self.dependentNamespaces(reset) if _ns.definedBySchema() ])

    def dependentNamespaces (self, reset=False):
        return self.namespaceGraph(reset).nodes()

    def componentGraph (self, reset=False):
        if reset or (self.__componentGraph is None):
            self.__componentGraph = pyxb.utils.utility.Graph()
            all_components = set()
            for ns in self.siblingNamespaces():
                [ all_components.add(_c) for _c in ns.components() if _c.hasBinding() ]
                
            need_visit = all_components.copy()
            while 0 < len(need_visit):
                c = need_visit.pop()
                self.__componentGraph.addNode(c)
                for cd in c.bindingRequires(include_lax=True):
                    if cd in all_components:
                        self.__componentGraph.addEdge(c, cd)
        return self.__componentGraph
    __componentGraph = None

    def componentOrder (self, reset=False):
        return self.componentGraph(reset).sccOrder()

    def __init__ (self, **kw):
        namespace_set = set(kw.get('namespace_set', []))
        namespace = kw.get('namespace')
        if namespace is not None:
            namespace_set.add(namespace)
        if 0 == len(namespace_set):
            raise pyxb.LogicError('NamespaceDependencies requires at least one root namespace')
        self.__rootNamespaces = namespace_set

## Local Variables:
## fill-column:78
## End:
