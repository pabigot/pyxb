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
        self.__root = root
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

    def root (self):
        return self.__root
    def setRoot (self, root):
        self.__root = root

    __roots = None
    def roots (self, reset=False):
        if reset or (self.__roots is None):
            self.__roots = set()
            for n in self.__nodes:
                if not (n in self.__reverseMap):
                    self.__roots.add(n)
        return self.__roots

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
        if (0 == len(roots)) and (self.root() is not None):
            roots = set([self.root()])
        if (0 == len(roots)) and (0 < len(self.__nodes)):
            raise Exception('TARJAN: No roots found in graph with %d nodes' % (len(self.__nodes),))
        for r in roots:
            self._tarjan(r)
        self.__didTarjan = True

    def _tarjan (self, v):
        self.__tarjanIndex[v] = self.__tarjanLowLink[v] = self.__index
        #print "Adding %s" % v
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
        print 'GENERATING DOT'
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
        
