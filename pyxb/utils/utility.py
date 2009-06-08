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
