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

"""Classes and global objects related to archiving U{XML
Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}."""

import pyxb
import os
import fnmatch
import pyxb.utils.utility
import utility

PathEnvironmentVariable = 'PYXB_ARCHIVE_PATH'
"""Environment variable from which default path to pre-loaded namespaces is
read.  The value should be a colon-separated list of absolute paths.  A path
of C{+} will be replaced by the system default path (normally
C{pyxb/standard/bindings/raw})."""

import os.path
import stat

DefaultArchivePath = os.path.realpath("%s/standard/bindings/raw" % (os.path.join(os.path.dirname( __file__), '..'),))
"""Default location for reading C{.wxs} files"""
print DefaultArchivePath

def GetArchivePath ():
    import os
    rv = os.environ.get(PathEnvironmentVariable)
    if rv is None:
        rv = '+'
    return rv

# Stuff required for pickling
import cPickle as pickle
#import pyxb.utils.pickle_trace as pickle

class NamespaceArchive (object):
    """Represent a file from which one or more namespaces can be read, or to
    which they will be written."""

    # YYYYMMDDHHMM
    __PickleFormat = '200907190858'

    @classmethod
    def _AnonymousCategory (cls):
        """The category name to use when storing references to anonymous type
        definitions.  For example, attribute definitions defined within an
        attribute use in a model group definition.that can be referenced frojm
        ax different namespace."""
        return cls.__AnonymousCategory
    __AnonymousCategory = '_anonymousTypeDefinition'


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
    # Class variable recording the namespace that is currently being
    # pickled.  Used to prevent storing components that belong to
    # other namespaces.  Should be None unless within an invocation of
    # SaveToFile.
    __PicklingArchive = None

    @classmethod
    def __ResetNamespaceArchives (cls):
        print 'RESETTING NAMESPACE ARCHIVES'
        if cls.__NamespaceArchives is not None:
            for nsa in cls.__NamespaceArchives.values():
                for ns in nsa.__namespaces:
                    ns._removeArchive(nsa)
        cls.__NamespaceArchives = {}

    __NamespaceArchives = None
    """A mapping from namespace URIs to names of files which appear to
    provide a serialized version of the namespace with schema."""

    @classmethod
    def __GetArchiveInstance (cls, archive_file):
        """Return a L{NamespaceArchive} instance associated with the given file.

        To the extent possible, the same file accessed through different paths
        returns the same L{NamespaceArchive} instance.
        """
        
        normalized_path = os.path.realpath(archive_file)
        nsa = cls.__NamespaceArchives.get(normalized_path)
        if nsa is None:
            nsa = cls.__NamespaceArchives[normalized_path] = NamespaceArchive(archive_path=archive_file)
        return nsa

    @classmethod
    def PreLoadArchives (cls, archive_path=None, required_archive_files=None, reset=False):
        """Scan for available archives, associating them with namespaces.

        This only validates potential archive contents; it does not load
        namespace data from the archives.  If invoked with no arguments, 

        @keyword archive_path: A colon-separated list of files or directories in
        which namespace archives can be found; see L{PathEnvironmentVariable}.
        Defaults to L{GetArchivePath()}.  If not defaulted, C{reset} will be
        forced to C{True}.  For any directory in the path, all files ending with
        C{.wxs} are examined.

        @keyword required_archive_files: A list of paths to files that must
        resolve to valid namespace archives.

        @keyword reset: If C{False} (default), the most recently read set of
        archives is returned; if C{True}, the archive path is re-scanned and the
        namespace associations validated.

        @return: A list of L{NamespaceArchive} instances corresponding to the
        members of C{required_archive_files}, in order.  If
        C{required_archive_files} was not provided, returns an empty list.

        @raise pickle.UnpicklingError: a C{required_archive_files} member does not
        contain a valid namespace archive.
        """
        
        reset = reset or (archive_path is not None) or (required_archive_files is not None) or (cls.__NamespaceArchives is None)
        required_archives = []
        if reset:
            # Erase any previous archive associations
            cls.__ResetNamespaceArchives()

            # Get archives for all required files
            if required_archive_files is not None:
                for afn in required_archive_files:
                    required_archives.append(cls.__GetArchiveInstance(afn))
    
            # Ensure we have an archive path
            if archive_path is None:
                archive_path = GetArchivePath()
    
            # Get archive instances for everything in the archive path
            for bp in archive_path.split(':'):
                if '+' == bp:
                    bp = DefaultArchivePath
                files = []
                try:
                    stbuf = os.stat(bp)
                    if stat.S_ISDIR(stbuf.st_mode):
                        files = [ os.path.join(bp, _fn) for _fn in os.listdir(bp) if _fn.endswith('.wxs') ]
                    else:
                        files = [ bp ]
                except OSError, e:
                    files = []
                for afn in files:
                    try:
                        nsa = cls.__GetArchiveInstance(afn)
                    except pickle.UnpicklingError, e:
                        print 'Cannot use archive %s: %s' % (afn, e)
                    except pyxb.NamespaceArchiveError, e:
                        print 'Cannot use archive %s: %s' % (afn, e)
        return required_archives

    def archivePath (self):
        """Path to the file in which this namespace archive is stored."""
        return self.__archivePath
    __archivePath = None

    def generationUID (self):
        return self.__generationUID
    __generationUID = None

    def isLoadable (self):
        return self.__isLoadable
    def setLoadable (self, loadable):
        if self.__isLoadable is None:
            raise pyxb.LogicError('Cannot set loadability on output namespace archive')
        self.__isLoadable = loadable
    __isLoadable = None

    def __init__ (self, namespaces=None, archive_path=None, generation_uid=None, loadable=True):
        """Create a new namespace archive.

        If C{namespaces} is given, this is an output archive.

        If C{namespaces} is absent, this is an input archive.

        @raise IOError: error attempting to read the archive file
        @raise pickle.UnpicklingError: something is wrong with the format of the library
        """
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
            self.__isLoadable = loadable
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
            return
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
        print 'Unpickling from %s' % (self.__archivePath,)
        object_maps = unpickler.load()
        for ns in ns_set:
            print 'Read %s from %s - active %s' % (ns, self.__archivePath, ns.isActive())
            ns._loadNamedObjects(object_maps[ns])
            ns._setLoadedFromArchive(self)
        print 'completed Unpickling from %s' % (self.__archivePath,)

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
                assert not ns.isAbsentNamespace()
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
                print "Archiving namespace %s in archive %s" % (ns, self.archivePath())
                ns.configureCategories([self._AnonymousCategory()])
                object_map[ns] = ns._categoryMap()
                ns._setWroteToArchive(self)
                for obj in ns._namedObjects().union(ns.components()):
                    if isinstance(obj, _ArchivableObject_mixin):
                        obj._prepareForArchive(self, ns)
            pickler.dump(object_map)
        finally:
            sys.setrecursionlimit(recursion_limit)
        NamespaceArchive.__PicklingArchive = None

    def __readNamespaceSet (self, unpickler, define_namespaces=False):
        uri_map = unpickler.load()
        
        for (uri, categories) in uri_map.items():
            cat_map = uri_map[uri]
            ns = utility.NamespaceInstance(uri)
            for cat in cat_map.keys():
                if not (cat in ns.categories()):
                    continue
                cross_objects = frozenset([ _ln for _ln in cat_map[cat].intersection(ns.categoryMap(cat).keys()) if not ns.categoryMap(cat)[_ln]._allowUpdateFromOther(None) ])
                if 0 < len(cross_objects):
                    raise pyxb.NamespaceArchiveError('Archive %s namespace %s archive/active conflict on category %s: %s' % (self.__archivePath, ns, cat, " ".join(cross_objects)))

        if not define_namespaces:
            return

        for uri in uri_map.keys():
            ns = utility.NamespaceForURI(uri, create_if_missing=True)
            ns._addArchive(self)
            self.__namespaces.add(ns)

        return uri_map

    def __str__ (self):
        archive_path = self.__archivePath
        if archive_path is None:
            archive_path = '??'
        return 'NSArchive@%s' % (archive_path,)

class _ArchivableObject_mixin (pyxb.cscRoot):
    """Mix-in to any object that can be stored in a namespace within an archive."""
    
    # Need to set this per category item
    __objectOrigin = None
    def _objectOrigin (self):
        return self.__objectOrigin
    def _setObjectOrigin (self, object_origin, override=False):
        if (self.__objectOrigin is not None) and (not override):
            if  self.__objectOrigin != object_origin:
                raise pyxb.LogicError('Inconsistent origins for object %s: %s %s' % (self, self.__objectOrigin, object_origin))
        else:
            self.__objectOrigin = object_origin

    def _prepareForArchive_csc (self, archive, namespace):
        return getattr(super(_ArchivableObject_mixin, self), '_prepareForArchive_csc', lambda *_args,**_kw: self)(archive, namespace)

    def _prepareForArchive (self, archive, namespace):
        #assert self.__objectOrigin is not None
        return self._prepareForArchive_csc(archive, namespace)

    def _updateFromOther_csc (self, other):
        return getattr(super(_ArchivableObject_mixin, self), '_updateFromOther_csc', lambda *_args,**_kw: self)(other)

    def _updateFromOther (self, other):
        """Update this instance with additional information provided by the other instance.

        This is used, for example, when a built-in type is already registered
        in the namespace, but we've processed the corresponding schema and
        have obtained more details."""
        assert self != other
        return self._updateFromOther_csc(other)

    def _allowUpdateFromOther (self, other):
        import builtin
        assert self._objectOrigin()
        return builtin.BuiltInObjectUID == self._objectOrigin().generationUID()

class _NamespaceArchivable_mixin (pyxb.cscRoot):
    """Encapsulate the operations and data relevant to archiving namespaces."""

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles category-related data."""
        getattr(super(_NamespaceArchivable_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__sourceArchives = set()
        self.__loadedFromArchive = None
        self.__wroteToArchive = None
        self.__active = False
        self.__moduleRecordMap = {}

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
        
    def archives (self):
        return self.__sourceArchives.copy()
    __sourceArchives = None
    
    def moduleRecords (self):
        return self.__moduleRecordMap.values()
    __moduleRecordMap = None

    def addModuleRecord (self, module_record):
        assert isinstance(module_record, ModuleRecord)
        assert not (module_record.generationUID() in self.__moduleRecordMap)
        self.__moduleRecordMap[module_record.generationUID()] = module_record
        return module_record
    def lookupModuleRecordByUID (self, generation_uid, create_if_missing=False, *args, **kw):
        rv = self.__moduleRecordMap.get(generation_uid)
        if (rv is None) and create_if_missing:
            rv = self.addModuleRecord(ModuleRecord(self, generation_uid, *args, **kw))
        return rv

    def isLoadable (self):
        """Return C{True} iff the component model for this namespace can be
        loaded from a namespace archive."""
        return 0 < len(self.loadableFrom())

    def loadableFrom (self):
        """Return a list of namespace archives from which this namespace can be read."""
        return [ _archive for _archive in self.__sourceArchives if _archive.isLoadable() ]

    def _setState_csc (self, kw):
        #assert not self.__isActive, 'ERROR: State set for active namespace %s' % (self,)
        return getattr(super(_NamespaceArchivable_mixin, self), '_getState_csc', lambda _kw: _kw)(kw)
    
    def markNotLoadable (self):
        """Prevent loading this namespace from an archive.

        This marks all archives in which the namespace appears, whether
        publically or privately, as not loadable."""
        if self._loadedFromArchive():
            raise pyxb.NamespaceError(self, 'cannot mark not loadable when already loaded')
        for archive in self.__sourceArchives.copy():
            archive.setLoadable(False)

class ModuleRecord (pyxb.utils.utility.PrivateTransient_mixin):
    __PrivateTransient = set()
    
    def namespace (self):
        return self.__namespace
    __namespace = None

    def archive (self):
        return self.__archive
    def _setArchive (self, archive):
        self.__archive = archive
        return self
    __archive = None
    __PrivateTransient.add('archive')

    def isPublic (self):
        return self.__isPublic
    def _setIsPublic (self, is_public):
        self.__isPublic = is_public
        return self
    __isPublic = None

    def isIncorporated (self):
        return self.__isIncorporated
    def markIncorporated (self):
        assert self.__isLoadable
        self.__isIncorporated = True
        self.__isLoadable = False
        return self
    __isIncorporated = None
    __PrivateTransient.add('archive')

    def isLoadable (self):
        return self.__isLoadable
    def _setIsLoadable (self, is_loadable):
        self.__isLoadable = is_loadable
        return self
    __isLoadable = None

    def generationUID (self):
        return self.__generationUID
    __generationUID = None

    def origins (self):
        return self.__originMap.values()
    def addOrigin (self, origin):
        assert isinstance(origin, _ObjectOrigin)
        assert not (origin.signature() in self.__originMap)
        self.__originMap[origin.signature()] = origin
        return origin
    def lookupOriginBySignature (self, signature):
        return self.__originMap.get(signature)
    def _setOrigins (self, origins):
        if self.__originMap is None:
            self.__originMap = {}
        else:
            self.__originMap.clear()
        [ self.addOrigin(_o) for _o in origins ]
        return self
    __originMap = None
    __PrivateTransient.add('originMap')

    def modulePath (self):
        return self.__modulePath
    def _setModulePath (self, module_path):
        self.__modulePath = module_path
        return self
    __modulePath = None

    def __init__ (self, namespace, generation_uid, **kw):
        super(ModuleRecord, self).__init__()
        self.__namespace = namespace
        self.__isPublic = kw.get('is_public', False)
        self.__isIncoporated = kw.get('is_incorporated', False)
        self.__isLoadable = kw.get('is_loadable', True)
        self.__modulePath = kw.get('module_path')
        assert isinstance(generation_uid, pyxb.utils.utility.UniqueIdentifier)
        self.__generationUID = generation_uid
        self.__originMap = {}

class _ObjectOrigin (pyxb.utils.utility.PrivateTransient_mixin, pyxb.cscRoot):
    """Marker class for objects that can serve as an origin for an object in a
    namespace."""

    def signature (self):
        return self.__signature
    __signature = None

    def moduleRecord (self):
        return self.__moduleRecord
    __moduleRecord = None

    def namespace (self):
        return self.moduleRecord().namespace()

    def generationUID (self):
        return self.moduleRecord().generationUID()

    def __init__ (self, namespace, generation_uid, **kw):
        self.__signature = kw.pop('signature', None)
        super(_ObjectOrigin, self).__init__(**kw)
        self.__moduleRecord = namespace.lookupModuleRecordByUID(generation_uid, create_if_missing=True, **kw)
        self.__moduleRecord.addOrigin(self)

class _SchemaOrigin (_ObjectOrigin):
    """Holds the data regarding components derived from a single schema.

    Coupled to a particular namespace through the
    L{_NamespaceComponentAssociation_mixin}.
    """

    __PrivateTransient = set()

    def __setDefaultKW (self, kw):
        schema = kw.get('schema')
        if schema is not None:
            assert not ('location' in kw)
            kw['location'] = schema.location()
            assert not ('signature' in kw)
            kw['signature'] = schema.signature()
            assert not ('generation_uid' in kw)
            kw['generation_uid'] = schema.generationUID()
            assert not ('namespace' in kw)
            kw['namespace'] = schema.targetNamespace()
            assert not ('version' in kw)
            kw['version'] = schema.schemaAttribute('version')

    def match (self, **kw):
        """Determine whether this record matches the parameters.

        @keyword schema: a L{pyxb.xmlschema.structures.Schema} instance from
        which the other parameters are obtained.
        @keyword location: a schema location (URI)
        @keyword signature: a schema signature
        @return: C{True} iff I{either} C{location} or C{signature} matches."""
        self.__setDefaultKW(kw)
        location = kw.get('location')
        if (location is not None) and (self.location() == location):
            return True
        signature = kw.get('signature')
        if (signature is not None) and (self.signature() == signature):
            return True
        return False

    def importedNamespaces (self):
        """Return the set of namespaces which some schema imported while
        processing with this namespace as target."""
        return self.__importedNamespaces
    __importedNamespaces = None

    def referencedNamespaces (self):
        """Return the set of namespaces which appear in namespace declarations
        of schema with this namespace as target."""
        return self.__referencedNamespaces
    __referencedNamespaces = None

    def location (self):
        return self.__location
    __location = None

    def schema (self):
        return self.__schema
    __schema = None
    __PrivateTransient.add('schema')

    def version (self):
        return self.__version
    __version = None

    def componentMapSlice (self):
        pass

    def __init__ (self, **kw):
        self.__setDefaultKW(kw)
        self.__schema = kw.pop('schema', None)
        self.__location = kw.pop('location', None)
        self.__version = kw.pop('version', None)
        super(_SchemaOrigin, self).__init__(kw.pop('namespace'), kw.pop('generation_uid'), **kw)

    def __str__ (self):
        rv = [ '_SchemaOrigin(%s@%s' % (self.namespace(), self.location()) ]
        if self.version() is not None:
            rv.append(',version=%s' % (self.version(),))
        rv.append(')')
        return ''.join(rv)

def AvailableForLoad ():
    """Return a list of namespace URIs for which we may be able to load the
    namespace contents from a pre-parsed file.  The corresponding L{Namespace}
    can be retrieved using L{NamespaceForURI}, and the declared objects in
    that namespace loaded with L{Namespace.validateComponentModel}.

    Note that success of the load is not guaranteed if the packed file
    is not compatible with the schema class being used."""
    # Invoke this to ensure we have searched for loadable namespaces
    return _LoadableNamespaceMap().keys()

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
