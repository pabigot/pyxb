from exceptions_ import *
import templates
from Namespace import Namespace
import XMLSchema.structures as structures
import XMLSchema.facets as facets

class Generator (object):
    pass

class PythonGenerator (Generator):
    __xsdModule = 'datatypes'
    __facetsModule = 'facets'

    def stringToUnquotedLiteral (self, value):
        value = value.replace('"', '\"')
        return value

    def stringToQuotedLiteral (self, value):
        return '"%s"' % (self.stringToUnquotedLiteral(value),)

    def stringToLongLiteralList (self, value):
        rv = [ self.stringToUnquotedLiteral(_line) for _line in value.split("\n") ]
        rv[0] = '"""%s' % (rv[0],)
        rv[-1] = '%s"""' % (rv[-1],)
        return rv

    def stringToToken (self, value):
        return value

    def stringToComment (self, value):
        return [ '# %s' % (_line,) for _line in value.split("\n") ]

    def __stdAtomicDefinition_s (self, std, **kw):
        assert 'namespace' in kw
        className = kw['tag']
        baseReference = self.reference(std.baseTypeDefinition(), **kw)
        declarations = []
        definitions = []
        facets = []
        if std.facets() is None:
            raise LogicError('STD %s has no facets?' % (std.name(),))
        for (fc, fi) in std.facets().items():
            if fi is not None:
                assert fi.ownerTypeDefinition() is not None
                if fi.ownerTypeDefinition() == std:
                    declarations.extend(self.declaration_l(fi, container=std, **kw))
                    definitions.append(self.definition(fi, **kw))
                facets.append(self.reference(fi, **kw))
        declarations = "\n    ".join(declarations)
        definitions = "\n".join(definitions)
        facets = ",\n        ".join(facets)
        return templates.replaceInText('''
class %{className} (%{baseReference}):
    %{declarations}
    pass
%{definitions}
%{className}._Facets = [ %{facets} ]

''', locals())

    def __stdListDefinition_s (self, std, **kw):
        return str(std)

    def __stdUnionDefinition_s (self, std, **kw):
        return str(std)

    def _stdDefinition_s (self, std, **kw):
        kw = kw.copy()
        kw.setdefault('namespace', std.targetNamespace())
        kw.setdefault('tag', self.reference(std, **kw))
        if std.VARIETY_absent == std.variety():
            return ''
        if std.VARIETY_atomic == std.variety():
            return self.__stdAtomicDefinition_s(std, **kw)
        if std.VARIETY_list == std.variety():
            return self.__stdListDefinition_s(std, **kw)
        if std.VARIETY_union == std.variety():
            return self.__stdUnionDefinition_s(std, **kw)
        raise IncompleteImplementationError('No generate support for STD variety %s' % (std.VarietyToString(std.variety()),))

    __facetsModule = 'xs.facets'
    __enumerationPrefixMap = { }
    
    def __enumerationTag (self, facet, enum_value):
        return '%s%s' % (self.__enumerationPrefixMap.get(facet.ownerTypeDefinition().ncName(), 'EV_'),
                         self.stringToToken(enum_value))

    def __enumerationDeclarations_l (self, facet, **kw):
        rv = []
        for enum_elt in facet.enumerationElements():
            if enum_elt.description is not None:
                rv.extend(self.stringToComment(str(enum_elt.description)))
            rv.append('%s = %s' % (self.__enumerationTag(facet, enum_elt.tag), self.stringToQuotedLiteral(enum_elt.tag)))
            rv.append('')
        return rv

    def __enumerationDefinitions_l (self, facet, **kw):
        rv = []
        for enum_elt in facet.enumerationElements():
            token = self.stringToToken(enum_elt.tag)
            rv.append('%s.addEnumeration(tag=%s, value=%s.%s)' % (self.reference(facet, **kw),
                                                        self.stringToQuotedLiteral(enum_elt.tag),
                                                        self.reference(facet.ownerTypeDefinition(), **kw),
                                                        self.__enumerationTag(facet, enum_elt.tag)))
        return rv

    def __constrainingFacetDefinition_s (self, facet, **kw):
        kw = kw.copy()
        kw.setdefault('tag', self.reference(facet, **kw))
        kw.setdefault('namespace', facet.ownerTypeDefinition().targetNamespace())
        value_literal = []
        if facet.value() is not None:
            value_literal.append('value=%s' % (facet.value().xsdLiteral(),))
        value_literal.append('value_datatype=%s' % (self.reference(facet.baseTypeDefinition(), **kw)))
        rv = [ '%s = %s.%s(%s)' % (self.reference(facet, **kw), self.__facetsModule, facet.__class__.__name__, ','.join(value_literal)) ]
        if isinstance(facet, facets.CF_enumeration):
            rv.extend(self.__enumerationDefinitions_l(facet, **kw))
        return "\n".join(rv)

    def declaration_l (self, v, **kw):
        if isinstance(v, facets.CF_enumeration):
            return self.__enumerationDeclarations_l(v, **kw)
        return []

    def definition (self, v, **kw):
        assert v is not None
        if isinstance(v, structures.SimpleTypeDefinition):
            return self._stdDefinition_s(v, **kw)
        if isinstance(v, facets.ConstrainingFacet):
            return self.__constrainingFacetDefinition_s(v, **kw)
        raise IncompleteImplementationError('No generate definition support for object type %s' % (v.__class__,))

    __constrainingFacetInstancePrefix = '_CF_'
    def __constrainingFacetReference (self, facet, **kw):
        tag = '%s%s' % (self.__constrainingFacetInstancePrefix, facet.Name())
        container = kw.get('container', None)
        if (container is None) or (facet.ownerTypeDefinition() != container):
            tag = '%s.%s' % (self.reference(facet.ownerTypeDefinition(), **kw), tag)
        return tag

    def moduleForNamespace (self, namespace):
        rv = namespace.modulePath()
        if rv is None:
            rv = 'UNDEFINED'
        return rv

    def __stdReference (self, std, **kw):
        ns = kw.get('namespace', None)
        tag = '%s' % (std.ncName(),)
        if (ns is None) or (ns != std.targetNamespace()):
            tag = '%s.%s' % (self.moduleForNamespace(std.targetNamespace()), tag)
        return tag

    # kw namespace
    # kw container
    def reference (self, v, **kw):
        assert v is not None
        if isinstance(v, facets.ConstrainingFacet):
            return self.__constrainingFacetReference(v, **kw)
        if isinstance(v, structures.SimpleTypeDefinition):
            return self.__stdReference(v, **kw)
        raise IncompleteImplementationError('No generate reference support for object type %s' % (v.__class__,))

import unittest

class PythonGeneratorTestCase (unittest.TestCase):
    __generator = None
    def setUp (self):
        self.__generator = PythonGenerator()

    def testStringToUnquotedLiteral (self):
        g = self.__generator
        self.assertEqual('', g.stringToUnquotedLiteral(''))
        self.assertEqual('\"quoted\"', g.stringToUnquotedLiteral('"quoted"'))
        self.assertEqual('\n', g.stringToUnquotedLiteral('''
'''))

    def testStringToQuotedLiteral (self):
        g = self.__generator
        self.assertEqual('""', g.stringToQuotedLiteral(''))
        self.assertEqual('"text"', g.stringToQuotedLiteral('text'))
        self.assertEqual('"\"quoted\""', g.stringToQuotedLiteral('"quoted"'))
        self.assertEqual('"\n"', g.stringToQuotedLiteral('''
'''))

    def testStringToLongLiteralList (self):
        g = self.__generator
        self.assertEqual('"""text"""', ''.join(g.stringToLongLiteralList('text')))
        self.assertEqual('''\
"""line one
line two"""\
''', "\n".join(g.stringToLongLiteralList("line one\nline two")))

    def testStringToComment (self):
        g = self.__generator
        self.assertEqual('# comment', ''.join(g.stringToComment("comment")))
        self.assertEqual('''# line one
# line two''', "\n".join(g.stringToComment("line one\nline two")))

    def testStringToToken (self):
        g = self.__generator
        self.assertEqual('token', g.stringToToken('token'))

if __name__ == '__main__':
    unittest.main()
