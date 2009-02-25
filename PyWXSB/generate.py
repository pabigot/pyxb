from exceptions_ import *
import templates
from Namespace import Namespace
import XMLSchema.structures as structures
import XMLSchema.facets as facets
import bindings

class Generator (object):
    pass

class DependencyError (PyWXSBException):
    __component = None
    def __init__ (self, generator, component):
        super(DependencyError, self).__init__('Dependency on ungenerated %s' % (component.name(),))
        if generator is not None:
            generator._queueForGeneration(component)
        self.__component = component

class PythonGenerator (Generator):
    __targetNamespace = None
    def targetNamespace (self): return self.__targetNamespace

    __generatorConfiguration = None
    def generatorConfiguration (self): return self.__generatorConfiguration

    def __init__ (self, namespace, xs_module, generator_configuration=None):
        self.__targetNamespace = namespace
        self.__xsModule = xs_module
        if generator_configuration is None:
            generator_configuration = bindings.GeneratorConfiguration(self.targetNamespace())
        self.__generatorConfiguration = generator_configuration

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

    def _stdDefinition_s (self, std, **kw):
        container = kw.get('container', std)
        kw.setdefault('namespace', container.targetNamespace())
        tag = kw.setdefault('tag', self.reference(container, require_defined=False, **kw))

        if std.VARIETY_absent == std.variety():
            return ''

        assert 'namespace' in kw
        assert kw['namespace'] is not None
        className = kw['tag']
        baseReference = self.reference(container.baseTypeDefinition(), **kw)

        declarations = []
        definitions = []

        if std.VARIETY_atomic == std.variety():
            pass
        if std.VARIETY_list == std.variety():
            # @todo create a list instance
            pass
        if std.VARIETY_union == std.variety():
            # @todo create a value instance
            pass

        attribute_uses = kw.get('attribute_uses', [])
        for attr_use in attribute_uses:
            declarations.append(self.__attributeUseDeclaration_s(attr_use, **kw))

        facets = []
        if std.facets() is None:
            raise LogicError('STD %s has no facets?' % (std.name(),))

        for (fc, fi) in std.facets().items():
            if fi is not None:
                assert fi.ownerTypeDefinition() is not None
                if fi.ownerTypeDefinition() == container:
                    declarations.extend(self.declaration_l(fi, container=container, **kw))
                    definitions.append(self.__constrainingFacetDefinition_s(fi, **kw))
                elif not self._definitionAvailable(fi.ownerTypeDefinition(), **kw):
                    raise DependencyError(self, fi.ownerTypeDefinition())
                facets.append(self.reference(fi, **kw))

        if 0 == len(declarations):
            declarations.append('pass')
        declarations = "\n    ".join(declarations)
        definitions = "\n".join(definitions)
        facets = ",\n        ".join(facets)
        self._definitionAvailable(container, value=True)
        return templates.replaceInText('''
# SimpleType or SimpleContent
class %{className} (%{baseReference}):
    %{declarations}
%{definitions}
%{className}._Facets = [ %{facets} ]

''', **locals())

        raise IncompleteImplementationError('No generate support for STD variety %s' % (std.VarietyToString(std.variety()),))

    def __initializer (self, component, **kw):
        is_plural = kw.get('is_plural', False)
        elt_type = kw['elt_type']
        elt_type_ref = self.reference(elt_type, **kw)
        if is_plural:
            member_init = '[]'
        elif component.valueConstraint() is not None:
            ( value, constraint ) = component.valueConstraint()
            member_init = '%s(%s)' % (elt_type_ref, elt_type.pythonSupport().XsdFromString(value).xsdLiteral())
        else:
            member_init = 'None'
        return member_init
        
    def __attributeDeclarationDeclaration_s (self, attr_decl, **kw):
        return '%s = %s' % (attr_decl.name(), self.__initializer(attr_decl, elt_type=attr_decl.typeDefinition(), **kw))

    def __attributeUseDeclaration_s (self, attr_use, **kw):
        return self.__attributeDeclarationDeclaration_s(attr_use.attributeDeclaration(), **kw)

    def __ctdSimpleContentDefinition_s (self, std, **kw):
        container = kw['container']
        return self._stdDefinition_s(std, attribute_uses=container.attributeUses(), **kw)

    def _ctdDefinition_s (self, ctd, **kw):
        kw = kw.copy()
        kw.setdefault('namespace', ctd.targetNamespace())
        kw.setdefault('tag', self.reference(ctd, require_defined=False, **kw))
        content_type = ctd.contentType()
        if ctd.CT_EMPTY == content_type:
            return self.__ctdParticleDefinition_s(None, container=ctd, **kw)
        base_type = ctd.baseTypeDefinition()
        assert base_type is not None
        if not self._definitionAvailable(base_type, **kw):
            raise DependencyError(self, base_type)
        assert isinstance(content_type, tuple)
        ( type_tag, particle ) = content_type
        if ctd.CT_SIMPLE == type_tag:
            return self.__ctdSimpleContentDefinition_s(particle, container=ctd, **kw)
        return self.__ctdParticleDefinition_s(particle, container=ctd, **kw)

    def __elementDeclaration_l (self, element_decl, **kw):
        member_name = element_decl.name()
        elt_type = element_decl.typeDefinition()
        elt_type_ref = self.reference(elt_type, **kw)
        member_init = self.__initializer(element_decl, elt_type=elt_type, **kw)
        return [ templates.replaceInText('''
    # %{elt_type_ref}
    %{member_name} = %{member_init}\
''', **locals()) ]

    def __modelGroupDeclarations_l (self, model_group, **kw):
        rv = []
        for p in model_group.particles():
            rv.extend(self.__particleDeclarations_l(p, **kw))
        return rv

    def __particleDeclarations_l (self, particle, **kw):
        kw = kw.copy()
        kw['is_plural'] = particle.isPlural()
        rv = []
        if isinstance(particle.term(), structures.ModelGroup):
            rv.extend(self.__modelGroupDeclarations_l(particle.term(), **kw))
        elif isinstance(particle.term(), structures.ElementDeclaration):
            rv.extend(self.__elementDeclaration_l(particle.term(), **kw))
        elif isinstance(particle.term(), structures.Wildcard):
            pass
        else:
            print particle
            raise IncompleteImplementationError('No support for particle term type %s' % (type(particle.term()),))
        return rv

    def __ctdParticleDefinition_s (self, particle, **kw):
        className = kw['tag']
        container = kw['container']
        baseReference = self.reference(container.baseTypeDefinition(), **kw)
        declarations = []
        if particle is not None:
            declarations.extend(self.__particleDeclarations_l(particle, **kw))
        if 0 == len(declarations):
            declarations.append('pass')
        declarations = "\n    ".join(declarations)
        self._definitionAvailable(container, value=True)
        return templates.replaceInText('''
# Complex type
class %{className} (%{baseReference}):
    %{declarations}

''', **locals())
        

    __facetsModule = 'xs.facets'
    __enumerationPrefixMap = { }
    
    def __enumerationTag (self, facet, enum_value):
        return '%s%s' % (self.__enumerationPrefixMap.get(facet.ownerTypeDefinition().ncName(), 'EV_'),
                         self.stringToToken(enum_value))

    def __enumerationDeclarations_l (self, facet, **kw):
        rv = []
        g = self.generatorConfiguration()
        ickw = kw.copy()
        ickw['in_class'] = facet.ownerTypeDefinition()
        facet_ref = g.getReference(facet, **ickw)
        facet_value_type_ref = g.getReference(facet.baseTypeDefinition(), **ickw)
        rv.append('%s = bindings.ConstrainingFacet(value_datatype=%s)' % (facet_ref, facet_value_type_ref))
        for enum_elt in facet.enumerationElements():
            if enum_elt.description is not None:
                rv.extend(self.stringToComment(str(enum_elt.description)))
            var = g.getReference(enum_elt, **ickw)
            # @todo optionally use integer values to speed comparisons
            val = self.stringToQuotedLiteral(enum_elt.tag)
            rv.append('%s = %s' % (var, val))
            rv.append('%s.addEnumeration(tag=%s, value=%s)' % (facet_ref,
                                                               self.stringToQuotedLiteral(enum_elt.tag),
                                                               var))
            rv.append('')
        return rv

    def __enumerationDefinitions_l (self, facet, **kw):
        rv = []
        for enum_elt in facet.enumerationElements():
            token = self.stringToToken(enum_elt.tag)
            rv.append('%s.addEnumeration(tag=%s, value=%s.%s)' % (self.reference(facet, **kw),
                                                        self.stringToQuotedLiteral(enum_elt.tag),
                                                        self.reference(facet.ownerTypeDefinition(), require_defined=False, **kw),
                                                        self.__enumerationTag(facet, enum_elt.tag)))
        return rv

    def __patternDefinitions_l (self, facet, **kw):
        rv = []
        for pattern_elt in facet.patternElements():
            rv.append('%s.addPattern(%s)' % (self.reference(facet, **kw),
                                             self.stringToQuotedLiteral(pattern_elt.pattern)))
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
        elif isinstance(facet, facets.CF_pattern):
            rv.extend(self.__patternDefinitions_l(facet, **kw))
        return "\n".join(rv)

    def declaration_l (self, v, **kw):
        if isinstance(v, facets.CF_enumeration):
            return self.__enumerationDeclarations_l(v, **kw)
        return []

    def _definition (self, v, **kw):
        assert v is not None
        if self._definitionAvailable(v, **kw):
            return ''
        try:
            if isinstance(v, structures.SimpleTypeDefinition):
                return self._stdDefinition_s(v, **kw)
            if isinstance(v, structures.ComplexTypeDefinition):
                return self._ctdDefinition_s(v, **kw)
            if isinstance(v, facets.ConstrainingFacet):
                return self.__constrainingFacetDefinition_s(v, **kw)
            raise IncompleteImplementationError('No generate definition support for object type %s' % (v.__class__,))
        except DependencyError, e:
            #print 'Halted generation of %s: %s' % (v.name(), e)
            self._queueForGeneration(v)
            return None

    __constrainingFacetInstancePrefix = '_CF_'
    def __constrainingFacetReference (self, facet, **kw):
        tag = '%s%s' % (self.__constrainingFacetInstancePrefix, facet.Name())
        container = kw.get('container', None)
        if (container is None) or (facet.ownerTypeDefinition() != container):
            tag = '%s.%s' % (self.reference(facet.ownerTypeDefinition(), require_defined=False, **kw), tag)
        return tag

    def moduleForNamespace (self, namespace):
        rv = namespace.modulePath()
        if rv is None:
            rv = 'UNDEFINED'
        return rv

    __pendingGeneration = None
    def _queueForGeneration (self, component):
        #self.__pendingGeneration.add(component)
        if component not in self.__pendingGeneration:
            self.__pendingGeneration.append(component)
    def _removeFromGenerationQueue (self, component):
        #self.__pendingGeneration.discard(component)
        if component in self.__pendingGeneration:
            self.__pendingGeneration.remove(component)

    def generateDefinitions (self, definitions):
        generated_code = []
        self.__pendingGeneration = definitions
        iter = 1
        while 0 < len(self.__pendingGeneration):
            print '%d LOOPING OVER GENERATABLES: %d' % (iter, len(self.__pendingGeneration))
            iter += 1
            ungenerated = self.__pendingGeneration
            self.__pendingGeneration = []
            for component in ungenerated:
                code = self._definition(component)
                if code is not None:
                    generated_code.append(code)
            if self.__pendingGeneration == ungenerated:
                # This only happens if we didn't code things right, or
                # the schema actually has a circular dependency in
                # some named component.
                failed_components = []
                for d in self.__pendingGeneration:
                    if isinstance(d, structures._NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise LogicError('Infinite loop in generation:\n  %s' % ("\n  ".join(failed_components),))
        self.__pendingGeneration = None
        return generated_code

    def _definitionAvailable (self, component, **kw):
        def_tag = '__defined'
        value = kw.get('value', None)
        if value is not None:
            assert isinstance(value, bool)
            setattr(component, def_tag, value)
            self._removeFromGenerationQueue(component)
            return True
        #if isinstance(component, structures.SimpleTypeDefinition) and component.isBuiltin():
        #    return True
        #if component == structures.ComplexTypeDefinition.UrTypeDefinition():
        #    return True
        ns = kw.get('namespace', None)
        if (ns is not None) and (component.targetNamespace() != ns):
            return True
        return hasattr(component, def_tag)

    __componentLocalIndex = 0
    def __componentReference (self, component, **kw):
        kw = kw.copy()
        require_defined = kw.get('require_defined', True)
        ref_tag = '__referenceTag'
        if hasattr(component, ref_tag):
            tag = getattr(component, ref_tag)
        else:
            if component.ncName() is None:
                self.__componentLocalIndex += 1
                tag = '_Local_%s_%d' % (component.__class__.__name__, self.__componentLocalIndex)
            else:
                tag = '%s' % (component.ncName(),)
            if isinstance(component, structures.ComplexTypeDefinition):
                tag = '_CT_%s' % (tag,)
            setattr(component, ref_tag, tag)
        if require_defined and not self._definitionAvailable(component, **kw):
            raise DependencyError(self, component)
        ns = kw.get('namespace', None)
        if (ns is None) or (ns != component.targetNamespace()):
            tag = '%s.%s' % (self.moduleForNamespace(component.targetNamespace()), tag)
        return tag

    # kw namespace
    # kw container
    def reference (self, v, **kw):
        assert v is not None
        if isinstance(v, facets.ConstrainingFacet):
            return self.__constrainingFacetReference(v, **kw)
        if isinstance(v, structures.SimpleTypeDefinition):
            return self.__componentReference(v, **kw)
        if isinstance(v, structures.ComplexTypeDefinition):
            return self.__componentReference(v, **kw)
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
