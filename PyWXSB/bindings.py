from exceptions_ import *
import templates
import Namespace
import XMLSchema as xs

class _ComponentTemplateRecord:
    __localTemplate = None
    def localTemplate (self): return self.__localTemplate
    
    __namedTemplate = None
    def namedTemplate (self): return self.__namedTemplate
    
    __identifier = None
    def identifier (self):
        self.__identifier += 1
        return self.__identifier

    def __init__ (self, local_template, named_template):
        self.__localTemplate = local_template
        self.__namedTemplate = named_template
        self.__identifier = 0

class GeneratorConfiguration:
    """Parameters and support methods to produce Python references to
    schema components and properties.

    The context in which a reference is used determines its form.
    Context is provided through the following keyword parameters:

    * namespace_context : A reference to a Namespace instance, or None
      if the reference is within the namespace for which code is being
      generated.

    * class_context : A reference to a schema component corresponding
      to the Python class being generated, or None if generating at
      the module level.

    * method_context : None if not within a method; otherwise a string
      denoting the reference to the object or class to which the
      method belongs (generally, 'self' or 'cls').

    * target : An object reference to the schema component that
      produced the Python class for which a source code reference is
      required.

    """
    
    __targetNamespace = None
    def targetNamespace (self): return self.__targetNamespace

    def __init__ (self, target_namespace):
        self.__targetNamespace = target_namespace

    __facetInstanceTemplate = '_F_%{name}'

    # Reference in class body: no qualifier [in_class=C]
    # Reference in method body: self or cls [in_method='self'|'cls']
    # Reference outside class but in module: class dot name (in_class is None)
    # Reference in different module: module dot class dot name (in_module != module)

    __templateMap = {
        xs.structures.SimpleTypeDefinition : _ComponentTemplateRecord('STD_local_%{id}', '%{name}_std'),
        xs.facets.ConstrainingFacet : _ComponentTemplateRecord(None, '_CF_%{name}'),
        xs.facets._EnumerationElement : _ComponentTemplateRecord(None, '_EV_%{name}')
        }
    def templateMap (self): return self.__templateMap

    __defaultEnumPrefix = 'EV'
    __defaultEnumTemplate = '%{pfx}_%{name}'

    def enumConstantName (self, enum_elt):
        pfx = enum_elt.bindingPrefix()
        if pfx is None:
            pfx = self.__defaultEnumPrefix
        template = enum_elt.bindingTemplate()
        if template is None:
            template = self.__defaultEnumTemplate
        return templates.replaceInText(template, { 'pfx': pfx, 'name': enum_elt.tag }


    def enumConstantValue (self, enum_elt):
        pass

    def enumConstantString (self, enum_elt):
        pass

    def facetValueClass (self, facet):
        pass

    def facetConstrainedClass (self, facet):
        pass

    def facetOwnerClass (self, facet):
        pass

    def facetValue (self, facet):
        pass

    def facetObjectName (self, facet, context):
        pass

    def getReference (self, target, **kw):
        name = kw.get('name', None)
        namespace = kw.get('namespace', None)
        if name is None:
            if isinstance(target, xs.structures._NamedComponent_mixin):
                name = target.ncName()
                namespace = target.targetNamespace()
            elif isinstance(target, xs.facets._EnumerationElement):
                name = target.tag
            elif isinstance(target, xs.facets.ConstrainingFacet):
                name = target.Name()
            else:
                raise LogicError('name %s' % (target.__class__,))
        if namespace is None:
            assert isinstance(target, xs.structures._NamedComponent_mixin)
            namespace = target.targetNamespace()
        in_class = kw.get('in_class', None)
        in_method = kw.get('in_method', None)
        if (namespace is not None) and (namespace != self.targetNamespace()):
            assert namespace.bindingConfiguration() is not None
            return '%s.%s' % (namespace.modulePath(), namespace.bindingConfiguration().getReference(target, **kw))
        for (key, trec) in self.__templateMap.items():
            if isinstance(target, key):
                owner = None
                if in_class is None:
                    owner = self.getReference(target.ownerTypeDefinition(), **kw)
                id = None
                if name is not None:
                    template = trec.namedTemplate()
                else:
                    template = trec.localTemplate()
                    id = trec.identifier()
                print 'name %s type %s template %s' % (name, target.__class__, template)
                return templates.replaceInText(template, name=name, id=id)
        raise LogicError('No support to get reference to instance of %s' % (target.__class__,))

xsg = GeneratorConfiguration(Namespace.XMLSchema)
Namespace.XMLSchema.bindingConfiguration(xsg)
xsg.templateMap().update({
        xs.structures.SimpleTypeDefinition : _ComponentTemplateRecord('STD_local_%{id}', '%{name}'),
        xs.facets._EnumerationElement : _ComponentTemplateRecord(None, '_EV_%{name}')
        })

class ConstrainingFacet (object):
    """Record a facet constraint within a binding class."""

    # The ncName of the facet in the xsd namespace
    __name = None
    def name (self): return self.__name

    # The Python class that represents values of the facet
    __valueType = None
    def valueType (self): return self.__valueType

    # The value of the facet at the level of the owning class
    __value = None
    def value (self): return self.__value

    # A boolean that indicates whether the value is fixed for
    # subclasses; or None if the facet does not support fixation
    # (pattern and enumeration).
    __fixed = None
    def fixed (self):
        if fixed is None:
            raise Exception('Facet %s does not support the fixed property' % (self.name(),))
        return self.__fixed

    def __init__ (self, name, value_type, value, fixed = None):
        args = (name, value_type, value)
        kw = { 'fixed': fixed }
        super(ConstrainingFacet, self).__init__(*args, **kw)
        self.__name = name
        self.__valueType = value_type
        self.__value = value
        if fixed is not None:
            self.__fixed = fixed
