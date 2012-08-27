# -*- coding: utf-8 -*-

# "Regular Expressions with Numerical Constraints and Automata with
# Counters", Dag Hovland.  Proceedings of the 6th International
# Colloquium on Theoretical Aspects of Computing, pp 231--245.  Pages
# 231 - 245 Springer-Verlag Berlin, Heidelberg, 2009.
#
# http://www.ii.uib.no/~dagh/
#
# LATA 2012: The Membership Problem for Regular Expressions with
# Unordered Concatenation and Numerical Constraints
# (http://www.ii.uib.no/~dagh/presLATA2012.pdf)
 

class Node (object):
    """Abstract class for any node in the term tree."""

    pass

class NumericalConstraint (Node):
    """A term with a numeric range constraint.

    This corresponds to a "particle" in the XML Schema content model."""

    _IsSimple = False

    __min = None
    __max = None
    __term = None

    def __init__ (self, term, min=0, max=1):
        """Term with a numerical constraint.

        @param term: A term, the number of appearances of which is
        constrained in this term.
        @type term: L{Node}

        @keyword min: The minimum number of occurrences of C{term}.
        The value must be non-negative.

        @keyword max: The maximum number of occurrences of C{term}.
        The value must be positive (in which case it must also be no
        smaller than C{min}), or C{None} to indicate an unbounded
        number of occurrences."""
        self.__term = term
        self.__min = min
        self.__max = max

    def __str__ (self):
        rv = unicode(self.__term)
        if not self.__term._IsSimple:
            rv = '(' + rv + ')'
        rv += '^(%u,' % (self.__min,)
        if self.__max is None:
            rv += u'∞'
        else:
            rv += '%u' % (self.__max)
        return rv + ')'


class Choice (Node):
    """A term that may be any one of a set of terms.

    This term matches if any one of its contained terms matches."""
    
    _IsSimple = False

    __terms = None
    
    def __init__ (self, *terms):
        """Term that selects one of a set of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def __str__ (self):
        return '(' + u'+'.join([ unicode(_t) for _t in self.__terms ]) + ')'

class Sequence (Node):
    """A term that is an ordered sequence of terms."""
    
    _IsSimple = False

    __terms = None

    def __init__ (self, *terms):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def __str__ (self):
        return u'∙'.join([ unicode(_t) for _t in self.__terms ])

class All (Node):
    """A term that is an unordered sequence of terms."""

    _IsSimple = False

    __terms = None

    def __init__ (self, *terms):
        """Term that collects an unordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""

        self.__terms = terms

    def __str__ (self):
        return u'&(' + ','.join([unicode(_t) for _t in self.__terms]) + ')'

class Symbol (Node):
    """A term that is a symbol (leaf node)."""
    __symbol = None

    _IsSimple = True

    def __init__ (self, symbol):
        self.__symbol = symbol

    def __str__ (self):
        return unicode(self.__symbol)

class Empty (Node):
    """A term indicating that no symbol is consumed."""

    _IsSimple = True

    def __str__ (self):
        return u'ε'

expr = NumericalConstraint(Symbol('a'), 2, 2)
expr = Choice(expr, Sequence(Symbol('b'), Symbol('c')))
expr = NumericalConstraint(expr, 3, 5)
print unicode(expr)
