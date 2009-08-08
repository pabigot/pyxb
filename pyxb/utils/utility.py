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

"""Utility functions and classes."""

import re
import os
import errno
import pyxb

def QuotedEscaped (s):
    """Convert a string into a literal value that can be used in Python source.

    This just calls repr.  No point in getting all complex when the language
    already gives us what we need.
    """
    return repr(s)

_UnderscoreSubstitute_re = re.compile(r'[- .]')
_NonIdentifier_re = re.compile(r'[^a-zA-Z0-9_]')
_PrefixUnderscore_re = re.compile(r'^_+')
_PrefixDigit_re = re.compile(r'^\d+')

def MakeIdentifier (s):
    """Convert a string into something suitable to be a Python identifier.

    The string is converted to unicode; spaces and periods replaced by
    underscores; non-printables stripped.  Furthermore, any leading
    underscores are removed.  If the result begins with a digit, the
    character 'n' is prepended.  If the result is the empty string,
    the string 'emptyString' is substituted.

    No check is made for conflicts with keywords.
    """
    s = _PrefixUnderscore_re.sub('', _NonIdentifier_re.sub('',_UnderscoreSubstitute_re.sub('_', str(s))))
    if _PrefixDigit_re.match(s):
        s = 'n' + s
    if 0 == len(s):
        s = 'emptyString'
    return s

# Note that types like int and float are not keywords
_Keywords = frozenset( ( "and", "del", "from", "not", "while", "as", "elif", "global",
              "or", "with", "assert", "else", "if", "pass", "yield",
              "break", "except", "import", "print", "class", "exec",
              "in", "raise", "continue", "finally", "is", "return",
              "def", "for", "lambda", "try" ) )
"""The keywords reserved for Python."""

def DeconflictKeyword (s, aux_keywords=frozenset()):
    """If the provide string matches a keyword, append an underscore to distinguish them."""
    if (s in _Keywords) or (s in aux_keywords):
        return '%s_' % (s,)
    return s

def MakeUnique (s, in_use):
    """Return an identifier based on s that is not in the given set.

    in_use must be an instance of set().  in_use is updated to contain
    the returned identifier.  The returned identifier is made unique
    by appending an underscore and, if necessary, a serial number.

    The order is : x, x_, x_2, x_3, ...
    """
    if s in in_use:
        ctr = 2
        s = s.rstrip('_')
        candidate = '%s_' % (s,)
        while candidate in in_use:
            candidate = '%s_%d' % (s, ctr)
            ctr += 1
        s = candidate
    in_use.add(s)
    return s

def PrepareIdentifier (s, in_use, aux_keywords=frozenset(), private=False, protected=False):
    """Combine everything required to create a unique identifier.

    Leading and trailing underscores are stripped from all
    identifiers.

    in_use is the set of already used identifiers.  Upon return from
    this function, it is updated to include the returned identifier.

    aux_keywords is an optional set of additional symbols that are
    illegal in the given context; use this to prevent conflicts with
    known method names.

    If private is True, the returned identifier has two leading
    underscores, making it a private variable within a Python class.
    If private is False, all leading underscores are stripped,
    guaranteeing the identifier will not be private.

    @note: Only module-level identifiers should be treated as
    protected.  The class-level _ReservedSymbol infrastructure does
    not include protected symbols.  All class members beginning with a
    single underscore are reserved for the PyXB infrastructure."""
    s = DeconflictKeyword(MakeIdentifier(s).strip('_'), aux_keywords)
    if private:
        s = '__' + s
    elif protected:
        s = '_' + s
    return MakeUnique(s, in_use)

# @todo: descend from pyxb.cscRoot, if we import pyxb
class _DeconflictSymbols_mixin (object):
    """Mix-in used to deconflict public symbols in classes that may be
    inherited by generated binding classes.

    Some classes, like the L{pyxb.binding.basis.element} or
    L{pyxb.binding.basis.simpleTypeDefinition} classes in
    L{pyxb.binding.basis}, have public symbols associated with
    functions and variables.  It is possible that an XML schema might
    include tags and attribute names that match these symbols.  To
    avoid conflict, the reserved symbols marked in this class are
    added to the pre-defined identifier set.

    Subclasses should create a class-level variable that contains a
    set of strings denoting the symbols reserved in this class,
    combined with those from any superclasses that also have reserved
    symbols.  Code like the following is suggested::

       # For base classes (direct mix-in):
       _ReservedSymbols = set([ 'one', 'two' ])
       # For subclasses:
       _ReservedSymbols = SuperClass._ReservedSymbols.union(set([ 'three' ]))

    Only public symbols (those with no underscores) are current
    supported.  (Private symbols can't be deconflicted that easily,
    and no protected symbols that derive from the XML are created by
    the binding generator.)
    """

    _ReservedSymbols = set()
    """There are no reserved symbols in the base class."""

__TabCRLF_re = re.compile("[\t\n\r]")
__MultiSpace_re = re.compile(" +")
    
def NormalizeWhitespace (text, preserve=False, replace=False, collapse=False):
    """Normalize the given string.

    Exactly one of the C{preserve}, C{replace}, and C{collapse} keyword
    parameters must be assigned the value C{True} by the caller.

    In the case of C{preserve}, the text is returned unchanged.

    In the case of C{replace}, all tabs, newlines, and carriage returns
    are replaced with ASCII spaces.

    In the case of C{collapse}, the C{replace} normalization is done,
    then sequences of two or more spaces are replaced by a single
    space.
    """
    if preserve:
        return text
    text = __TabCRLF_re.sub(' ', text)
    if replace:
        return text
    if collapse:
        return __MultiSpace_re.sub(' ', text).strip()
    # pyxb not imported here; could be.
    raise Exception('NormalizeWhitespace: No normalization specified')

class Graph:
    """Represent some sort of graph.

    This is used to determine order dependencies among components
    within a namespace, and schema that comprise various
    namespaces."""
    
    def __init__ (self, root=None):
        self.__roots = None
        if root is not None:
            self.__roots = set([root])
        self.__edges = set()
        self.__edgeMap = { }
        self.__reverseMap = { }
        self.__nodes = set()

    __scc = None
    __sccMap = None
    __dfsOrder = None

    def addEdge (self, source, target):
        self.__edges.add( (source, target) )
        self.__edgeMap.setdefault(source, set()).add(target)
        if source != target:
            self.__reverseMap.setdefault(target, set()).add(source)
        self.__nodes.add(source)
        self.__nodes.add(target)

    def addNode (self, node):
        self.__nodes.add(node)

    __roots = None
    def roots (self, reset=False):
        if reset or (self.__roots is None):
            self.__roots = set()
            for n in self.__nodes:
                if not (n in self.__reverseMap):
                    self.__roots.add(n)
        return self.__roots
    def addRoot (self, root):
        if self.__roots is None:
            self.__roots = set()
        self.__nodes.add(root)
        self.__roots.add(root)
        return self

    def edgeMap (self):
        return self.__edgeMap

    def edges (self):
        return self.__edges

    def nodes (self):
        return self.__nodes

    def tarjan (self, reset=False):
        if (self.__scc is not None) and (not reset):
            return
        self.__sccMap = { }
        self.__stack = []
        self.__sccOrder = []
        self.__scc = []
        self.__index = 0
        self.__tarjanIndex = { }
        self.__tarjanLowLink = { }
        for v in self.__nodes:
            self.__tarjanIndex[v] = None
        roots = self.roots()
        if (0 == len(roots)) and (0 < len(self.__nodes)):
            raise Exception('TARJAN: No roots found in graph with %d nodes' % (len(self.__nodes),))
        for r in roots:
            self._tarjan(r)
        self.__didTarjan = True

    def _tarjan (self, v):
        if self.__tarjanIndex.get(v) is not None:
            # "Root" was already reached.
            return
        self.__tarjanIndex[v] = self.__tarjanLowLink[v] = self.__index
        self.__index += 1
        self.__stack.append(v)
        source = v
        for target in self.__edgeMap.get(source, []):
            if self.__tarjanIndex[target] is None:
                #print "Target %s not found in processed" % (target,)
                self._tarjan(target)
                self.__tarjanLowLink[v] = min(self.__tarjanLowLink[v], self.__tarjanLowLink[target])
            elif target in self.__stack:
                #print "Found %s in stack" % (target,)
                self.__tarjanLowLink[v] = min(self.__tarjanLowLink[v], self.__tarjanLowLink[target])
            else:
                #print "No %s in stack" % (target,)
                pass

        if self.__tarjanLowLink[v] == self.__tarjanIndex[v]:
            scc = []
            while True:
                scc.append(self.__stack.pop())
                if v == scc[-1]:
                    break;
            self.__sccOrder.append(scc)
            if 1 < len(scc):
                self.__scc.append(scc)
                [ self.__sccMap.setdefault(_v, scc) for _v in scc ]
                #print 'SCC at %s' % (' '.join( [str(_s) for _s in scc ]),)

    def scc (self, reset=False):
        if reset or (self.__scc is None):
            self.tarjan(reset)
        return self.__scc
    __scc = None

    def sccMap (self, reset=False):
        if reset or (self.__sccMap is None):
            self.tarjan(reset)
        return self.__sccMap
    __sccMap = None

    def sccOrder (self, reset=False):
        if reset or (self.__sccOrder is None):
            self.tarjan(reset)
        return self.__sccOrder
    __sccOrder = None

    def sccForNode (self, node, **kw):
        return self.sccMap(**kw).get(node, None)

    def cyclomaticComplexity (self):
        self.tarjan()
        return len(self.__edges) - len(self.__nodes) + 2 * len(self.__scc)

    def __dfsWalk (self, source):
        assert not (source in self.__dfsWalked)
        self.__dfsWalked.add(source)
        for target in self.__edgeMap.get(source, []):
            if not (target in self.__dfsWalked): 
                self.__dfsWalk(target)
        self.__dfsOrder.append(source)

    def _generateDOT (self, title='UNKNOWN', labeller=None):
        node_map = { }
        idx = 1
        for n in self.__nodes:
            node_map[n] = idx
            idx += 1
        text = []
        text.append('digraph "%s" {' % (title,))
        for n in self.__nodes:
            if labeller is not None:
                nn = labeller(n)
            else:
                nn = str(n)
            text.append('%s [shape=box,label="%s"];' % (node_map[n], nn))
        for s in self.__nodes:
            for d in self.__edgeMap.get(s, []):
                if s != d:
                    text.append('%s -> %s;' % (node_map[s], node_map[d]))
        text.append("};")
        return "\n".join(text)

    def dfsOrder (self, reset=False):
        if reset or (self.__dfsOrder is None):
            self.__dfsWalked = set()
            self.__dfsOrder = []
            for root in self.roots(reset=reset):
                self.__dfsWalk(root)
            self.__dfsWalked = None
            if len(self.__dfsOrder) != len(self.__nodes):
                raise Exception('DFS walk did not cover all nodes (walk %d versus nodes %d)' % (len(self.__dfsOrder), len(self.__nodes)))
        return self.__dfsOrder
        
def NormalizeLocation (uri, parent_uri=None):
    """Normalize a URI against an optional parent_uri in the way that is
    done for C{schemaLocation} attribute values.

    Note that, if no URI scheme is present, this will normalize a file
    system path."""
    import urlparse
    import os
    
    if uri is None:
        return uri
    if parent_uri is None:
        abs_uri = uri
    else:
        #if (0 > parent_uri.find(':')) and (not parent_uri.endswith(os.sep)):
        #    parent_uri = parent_uri + os.sep
        abs_uri = urlparse.urljoin(parent_uri, uri)
    if 0 > abs_uri.find(':'):
        abs_uri = os.path.realpath(abs_uri)
    return abs_uri

def TextFromURI (uri):
    """Retrieve the contents of the uri as a text string.

    If the uri does not include a scheme (e.g., C{http:}), it is
    assumed to be a file path on the local system."""
    import urllib2
    xmls = None
    try:
        if 0 <= uri.find(':'):
            xmls = urllib2.urlopen(uri).read()
        else:
            xmls = file(uri).read()
    except Exception, e:
        print 'TextFromURI: open %s caught: %s' % (uri, e)
        raise
    return xmls

class ConstrainedMutableSequence (object):
    """A mutable sequence type constrained so its values are instances
    of a given type.

    After converting any user input, operations are delegated to an
    underlying sequence instance."""

    # Type of sequence members
    __memberType = None
    def _memberType (self):
        """The type of which sequence members must be an instance.

        This value is never used in maintaining the sequence, since in
        many cases there is no single type object that is correct for
        all members.  Cf. pyxb.binding.basis.STD_union."""
        return self.__memberType

    __memberConverter = None
    def _memberConverter (self):
        """The function object that can convert something to be of member type."""
        return self.__memberConverter

    # Underlying sequence storage
    __sequence = None

    # Convert a single value to the required type, if not already an instance
    def __convertOne (self, v):
        return self.__memberConverter(v)

    # Convert a sequence of values to the required type, if not already instances
    def __convertMany (self, values):
        nv = []
        for v in values:
            nv.append(self.__memberConverter(v))
        return nv

    def __init__ (self, mutable_sequence, member_type, member_converter=None):
        """Create a constrained sequence.

        @param mutable_sequence: A by-value reference to a sequence
        instance that will be managed by this instance.

        @keyword member_type: An object that represents the type of members of the sequence
        @type member_type: C{type}

        @keyword member_converter: An invocable that converts values
        to be valid members of the sequence.
        """
        self.__memberType = member_type
        if member_converter is None:
            member_converter = self.__memberType
        self.__memberConverter = member_converter
        self.__sequence = mutable_sequence
        if 0 < len(self.__sequence):
            self.__sequence[:] = self.__convertMany(self.__sequence)
        # If I could do things like any of these:
        #    self.__str__ = self.__sequence.__str__
        #    setattr(self, '__str__', self.__sequence.__str__)
        # I'd add all the relevant methods.  But I can't.

    # Standard underlying container methods, per Python Reference Manual "Emulating Container Types"
    def __len__ (self):
        return len(self.__sequence)
    
    def __getitem__ (self, key):
        return self.__sequence[key]

    def __setitem__ (self, key, value):
        if isinstance(key, slice):
            self.__sequence[key] = self.__convertMany(value)
        else:
            self.__sequence[key] = self.__convertOne(value)

    def __setslice__ (self, start, stop, value):
        self.__sequence.__setslice__(start, stop, self.__convertMany(value))

    def __delitem__ (self, key):
        del self.__sequence[key]

    def __iter__ (self):
        return iter(self.__sequence)

    def __contains__ (self, item):
        return self.__sequence.__contains__(self.__convertOne(item))

    # Standard mutable sequence methods, per Python Library Reference "Mutable Sequence Types"

    def append (self, x):
        ls = len(self.__sequence)
        self.__sequence[ls:ls] = [ self.__convertOne(x) ]

    def extend (self, x):
        ls = len(self.__sequence)
        self.__sequence[ls:ls] = self.__convertMany(x)

    def count (self, x):
        return self.__sequence.count(self.__convertOne(x))

    def index (self, x, *args):
        return self.__sequence.index(self.__convertOne(x), *args)

    def insert (self, i, x):
        self.__sequence[i:i] = self.__convertOne(x)

    def pop (self, *args):
        return self.__sequence.pop(*args)

    def remove (self, x):
        self.__sequence.remove(self.__convertOne(x))

    def reverse (self):
        self.__sequence.reverse()

    def sort (self, *args):
        self.__sequence.sort(*args)

    # Miscellaneous support methods

    def __str__ (self):
        return self.__sequence.__str__()
    
    def __eq__ (self, other):
        if isinstance(other, type(self)):
            other = other.__sequence
        return self.__sequence.__eq__(other)

    def __ne__ (self, other):
        if isinstance(other, type(self)):
            other = other.__sequence
        return self.__sequence.__ne__(other)

    def __hash__ (self):
        return self.__sequence.__hash__()

    def __nonzero__ (self):
        return self.__sequence.__nonzero__()

def OpenOrCreate (file_name, tag=None, preserve_contents=False):
    """Return a file object used to write the given file.

    Use the C{tag} keyword to preserve the contents of existing files
    that are not supposed to be overwritten.

    To get a writable file but leaving any existing contents in place,
    set the C{preserve_contents} keyword to C{True}.  Normally, existing file
    contents are erased.

    The returned file pointer is positioned at the end of the file.

    @keyword tag: If not C{None} and the file already exists, absence
    of the given value in the first 4096 bytes of the file causes an
    IOError to be raised with errno EEXIST.  I.e., only files with
    this value in the first 4KB will be returned for writing.

    @keyword preserve_contents: This value controls whether existing
    contents of the file will be erased (C{False}, default) or left in
    place (C{True}).
    """
    (path, leaf) = os.path.split(file_name)
    if path:
        try:
            os.makedirs(path)
        except Exception, e:
            if not (isinstance(e, (OSError, IOError)) and (errno.EEXIST == e.errno)):
                raise
    fp = file(file_name, 'a+')
    if (tag is not None) and (0 < os.fstat(fp.fileno()).st_size):
        text = fp.read(4096)
        if 0 > text.find(tag):
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST))
    if not preserve_contents:
        fp.seek(0) # os.SEEK_SET
        fp.truncate()
    else:
        fp.seek(2) # os.SEEK_END
    return fp
            
import sha
# @todo: support hashlib
def HashForText (text):
    return sha.new(text).hexdigest()

__HaveUUID = False
try:
    import uuid
    __HaveUUID = True
except ImportError:
    import time
    import random
def _NewUUIDString ():
    if __HaveUUID:
        return uuid.uuid1().urn
    return '%s:%08.8x' % (time.strftime('%Y%m%d%H%M%S'), random.randint(0, 0xFFFFFFFFL))

class UniqueIdentifier (object):
    """Records a unique identifier associated with a binding
    generation action.

    The identifier is a string, but gets wrapped in an instance of
    this class to optimize comparisons and reduce memory footprint.

    An instance of this class compares equal to, and hashes equivalent
    to, the uid string.  When C{str}'d, the result is the uid; when
    C{repr}'d, the result is a constructor call to
    C{pyxb.utils.utility.UniqueIdentifier}.
    """

    __ExistingUIDs = {}

    __uid = None
    def uid (self):
        """The string unique identifier"""
        return self.__uid
    
    # Support pickling
    def __getnewargs__ (self):
        return (self.__uid,)

    def __getstate__ (self):
        return self.__uid

    def __setstate__ (self, state):
        assert self.__uid == state

    # Singleton-like
    def __new__ (cls, *args):
        if 0 == len(args):
            uid = _NewUUIDString()
        else:
            uid = args[0]
        if isinstance(uid, UniqueIdentifier):
            uid = uid.uid()
        if not isinstance(uid, basestring):
            raise TypeError('UniqueIdentifier uid must be a string')
        rv = cls.__ExistingUIDs.get(uid)
        if rv is None:
            rv = super(UniqueIdentifier, cls).__new__(cls)
            rv.__uid = uid
            cls.__ExistingUIDs[uid] = rv
        return rv

    def associateObject (self, obj):
        self.__associatedObjects.add(obj)
    def associatedObjects (self):
        return self.__associatedObjects
    __associatedObjects = None

    def __init__ (self, uid=None):
        """Create a new UniqueIdentifier instance.

        @param uid: The unique identifier string.  If present, it is
        the callers responsibility to ensure the value is universally
        unique.  If C{None}, one will be provided.
        @type uid: C{str} or C{unicode}
        """
        assert (uid is None) or (self.uid() == uid), 'UniqueIdentifier: ctor %s, actual %s' % (uid, self.uid())
        self.__associatedObjects = set()

    def __eq__ (self, other):
        if other is None:
            return False
        elif isinstance(other, UniqueIdentifier):
            other_uid = other.uid()
        elif isinstance(other, basestring):
            other_uid = other
        else:
            raise TypeError('UniqueIdentifier: Cannot compare with type %s' % (type(other),))
        return self.uid() == other_uid

    def __hash__ (self):
        return hash(self.uid())

    def __str__ (self):
        return self.uid()

    def __repr__ (self):
        return 'pyxb.utils.utility.UniqueIdentifier(%s)' % (repr(self.uid()),)

import datetime
import calendar
import time
class UTCOffsetTimeZone (datetime.tzinfo):
    """A tzinfo subclass that helps deal with UTC conversions in an ISO8601 world.

    This class only supports fixed offsets from UTC.
    """

    # Regular expression that matches valid ISO8601 time zone suffixes
    __Lexical_re = re.compile('^([-+])(\d\d):(\d\d)$')

    # The offset in minutes east of UTC.
    __utcOffset_min = 0

    # Same as __utcOffset_min, but as a datetime.timedelta
    __utcOffset_td = None

    # A zero-length duration
    __ZeroDuration = datetime.timedelta(0)

    def __init__ (self, spec=None, flip=False):
        """Create a time zone instance with a fixed offset from UTC.

        @param spec: Specifies the offset.  Can be an integer counting
        minutes east of UTC, the value C{None} (equal to 0 minutes
        east), or a string that conform to the ISO8601 time zone
        sequence (B{Z}, or B{[+-]HH:MM}).

        @param flip: If C{False} (default), no adaptation is done.  If
        C{True}, the time zone offset is negated, resulting in the
        conversion from localtime to UTC rather than the default of
        UTC to localtime.
        """

        if spec is not None:
            if isinstance(spec, basestring):
                if 'Z' == spec:
                    self.__utcOffset_min = 0
                else:
                    match = self.__Lexical_re.match(spec)
                    if match is None:
                        raise ValueError('Bad time zone: %s' % (spec,))
                    self.__utcOffset_min = int(match.group(2)) * 60 + int(match.group(3))
                    if '-' == match.group(1):
                        self.__utcOffset_min = - self.__utcOffset_min
            elif isinstance(spec, int):
                self.__utcOffset_min = spec
            elif isinstance(spec, datetime.timedelta):
                self.__utcOffset_min = spec.seconds / 60
            else:
                raise TypeError('%s: unexpected type %s' % (type(self), type(spec)))
            if flip:
                self.__utcOffset_min = - self.__utcOffset_min
        self.__utcOffset_td = datetime.timedelta(minutes=self.__utcOffset_min)
        if 0 == self.__utcOffset_min:
            self.__tzName = 'Z'
        elif 0 > self.__utcOffset_min:
            self.__tzName = '-%02d%02d' % divmod(-self.__utcOffset_min, 60)
        else:
            self.__tzName = '+%02d%02d' % divmod(self.__utcOffset_min, 60)

    def utcoffset (self, dt):
        """Returns the constant offset for this zone."""
        return self.__utcOffset_td

    def tzname (self, dt):
        """Return the name of the timezone in ISO8601 format."""
        return self.__tzName
    
    def dst (self, dt):
        """Returns a constant zero duration."""
        return self.__ZeroDuration

class LocalTimeZone (datetime.tzinfo):
    """A C{datetime.tzinfo} for the local time zone.

    Mostly pinched from the C{datetime.tzinfo} documentation in Python 2.5.1.
    """

    __STDOffset = datetime.timedelta(seconds=-time.timezone)
    __DSTOffset = __STDOffset
    if time.daylight:
        __DSTOffset = datetime.timedelta(seconds=-time.altzone)
    __ZeroDelta = datetime.timedelta(0)
    __DSTDelta = __DSTOffset - __STDOffset

    def utcoffset (self, dt):
        if self.__isDST(dt):
            return self.__DSTOffset
        return self.__STDOffset

    def dst (self, dt):
        if self.__isDST(dt):
            return self.__DSTDelta
        return self.__ZeroDelta

    def tzname (self, dt):
        return time.tzname[self.__isDST(dt)]

    def __isDST (self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              0, 0, -1)
        tt = time.localtime(time.mktime(tt))
        return tt.tm_isdst > 0

class PrivateTransient_mixin (pyxb.cscRoot):
    """Emulate the B{transient} keyword from Java for private member
    variables.

    This class defines a C{__getstate__} method which returns a copy
    of C{self.__dict__} with certain members removed.  Specifically,
    if a string "s" appears in a class member variable named
    C{__PrivateTransient}, then the corresponding private variable
    "_Class__s" will be removed from the state dictionary.

    If you use this, it is your responsibility to define the
    C{__PrivateTransient} class variable and add to it the required
    variable names.

    Classes that inherit from this are free to define their own
    C{__getstate__} method, which may or may not invoke the superclass
    one.  If you do this, be sure that the class defining
    C{__getstate__} lists L{PrivateTransient_mixin} as one of its
    direct superclasses, lest the latter end up earlier in the mro and
    consequently bypass the local override.
    """

    __Attribute = '__PrivateTransient'
    
    def __getstate__ (self):
        #print '%s %x state' % (type(self), id(self))
        state = self.__dict__.copy()
        # Note that the aggregate set is stored in a class variable
        # with a slightly different name than the class-level set.
        attr = '_%s%s_' % (self.__class__.__name__, self.__Attribute)
        skipped = getattr(self.__class__, attr, None)
        if skipped is None:
            skipped = set()
            for cl in self.__class__.mro():
                for (k, v) in cl.__dict__.items():
                    if k.endswith(self.__Attribute):
                        cl2 = k[:-len(self.__Attribute)]
                        skipped.update([ '%s__%s' % (cl2, _n) for _n in v ])
            setattr(self.__class__, attr, skipped)
            #print 'Defined skipped for %s: %s' % (self.__class__, skipped)
        for k in skipped:
            if state.get(k) is not None:
                #print 'Stripping %s from instance %x of %s' % (k, id(self), type(self))
                del state[k]
        # Uncomment the following to test whether undesirable types are being
        # pickled.
        #for (k, v) in state.items():
        #    import pyxb.namespace
        #    import xml.dom
        #    import pyxb.xmlschema.structures
        #    if isinstance(v, (pyxb.namespace.resolution.NamespaceContext, xml.dom.Node, pyxb.xmlschema.structures.Schema)):
        #        raise pyxb.LogicError('Unexpected instance of %s key %s in %s' % (type(v), k, self))

        return state

_DefaultPathWildcard = '+'
def GetMatchingFiles (path='.', pattern=None, default_path=None):
    matching_files = []
    path_set = path.split(':')
    while 0 < len(path_set):
        path = path_set.pop(0)
        if _DefaultPathWildcard == path:
            if default_path is not None:
                path_set[0:0] = default_path.split(':')
            continue
        recursive = False
        if path.endswith('//'):
            recursive = True
            path = path[:-2]
        if os.path.isfile(path):
            if (pattern is None) or (pattern.search(path) is not None):
                matching_files.append(path)
        else:
            for (root, dirs, files) in os.walk(path):
                for f in files:
                    if (pattern is None) or (pattern.search(f) is not None):
                        matching_files.append(os.path.join(root, f))
                if not recursive:
                    break
    return matching_files
    
if '__main__' == __name__:
    unittest.main()
            
        
