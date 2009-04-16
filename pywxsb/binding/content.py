"""Helper classes that maintain the content model of XMLSchema in the binding classes."""

from pywxsb.exceptions_ import *
import basis

import xml.dom

class AttributeUse (object):
    """A helper class that encapsulates everything we need to know
    about the way an attribute is used within a binding class."""
    __tag = None       # Unicode XML tag @todo not including namespace
    __pythonField = None # Identifier used for this attribute within the owning class
    __valueAttributeName = None # Private attribute used in instances to hold the attribute value
    __dataType = None  # PST datatype
    __unicodeDefault = None     # Default value as a unicode string, or None
    __defaultValue = None       # Default value as an instance of datatype, or None
    __fixed = False             # If True, value cannot be changed
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, tag, python_field, value_attribute_name, data_type, unicode_default=None, fixed=False, required=False, prohibited=False):
        self.__tag = tag
        self.__pythonField = python_field
        self.__valueAttributeName = value_attribute_name
        self.__dataType = data_type
        self.__unicodeDefault = unicode_default
        if self.__unicodeDefault is not None:
            self.__defaultValue = self.__dataType(self.__unicodeDefault)
        self.__fixed = fixed
        self.__required = required
        self.__prohibited = prohibited

    def tag (self):
        """Unicode tag for the attribute in its element"""
        return self.__tag
    
    def pythonField (self):
        """Tag used within Python code for the attribute"""
        return self.__pythonField

    def __getValue (self, ctd_instance):
        return getattr(ctd_instance, self.__valueAttributeName, (False, None))

    def __getProvided (self, ctd_instance):
        return self.__getValue(ctd_instance)[0]

    def value (self, ctd_instance):
        """Get the value of the attribute."""
        return self.__getValue(ctd_instance)[1]

    def __setValue (self, ctd_instance, new_value, provided):
        return setattr(ctd_instance, self.__valueAttributeName, (provided, new_value))

    def reset (self, ctd_instance):
        self.__setValue(ctd_instance, self.__defaultValue, False)

    def setFromDOM (self, ctd_instance, node):
        """Set the value of the attribute in the given instance from
        the corresponding attribute of the DOM Element node.  If node
        is None, or does not have an attribute, the default value is
        assigned.  Raises ProhibitedAttributeError and
        MissingAttributeError in the cases of prohibited and required
        attributes.
        """
        unicode_value = self.__unicodeDefault
        provided = False
        assert isinstance(node, xml.dom.Node)
        if node.hasAttribute(self.__tag):
            if self.__prohibited:
                raise ProhibitedAttributeError('Prohibited attribute %s found' % (self.__tag,))
            unicode_value = node.getAttribute(self.__tag)
            provided = True
        else:
            if self.__required:
                raise MissingAttributeError('Required attribute %s not found' % (self.__tag,))
        if unicode_value is None:
            # Must be optional and absent
            self.__setValue(ctd_instance, None, False)
        else:
            if self.__fixed and (unicode_value != self.__defaultValue):
                raise AttributeChangeError('Attempt to change value of fixed attribute %s' % (self.__tag,))
            # NB: Do not set provided here; this may be the default
            self.__setValue(ctd_instance, self.__dataType(unicode_value), provided)
        return self

    def addDOMAttribute (self, ctd_instance, element):
        """If this attribute as been set, add the corresponding attribute to the DOM element."""
        ( provided, value ) = self.__getValue(ctd_instance)
        if provided:
            assert value is not None
            element.setAttribute(self.__tag, value.xsdLiteral())
        return self

    def setValue (self, ctd_instance, new_value):
        """Set the value of the attribute.

        This validates the value against the data type."""
        assert new_value is not None
        if not isinstance(new_value, self.__dataType):
            new_value = self.__dataType(new_value)
        self.__setValue(ctd_instance, new_value, True)
        return new_value

class ElementUse (object):
    """Aggregate the information relevant to an element of a complex type.

    This includes the original tag name, the spelling of the
    corresponding object in Python, an indicator of whether multiple
    instances might be associated with the field, and a list of types
    for legal values of the field."""

    __tag = None
    __pythonField = None
    __valueElementName = None
    __dataTypes = None
    __isPlural = False

    def __init__ (self, tag, python_field, value_element_name, is_plural, default=None, data_types=[]):
        self.__tag = tag
        self.__pythonField = python_field
        self.__valueElementName = value_element_name
        self.__isPlural = is_plural
        self.__dataTypes = data_types

    def _setDataTypes (self, data_types):
        self.__dataTypes = data_types

    def tag (self):
        return self.__tag
    
    def pythonField (self):
        return self.__pythonField

    def isPlural (self):
        return self.__isPlural

    def validElements (self):
        return self.__dataTypes

    def defaultValue (self):
        if self.isPlural():
            return []
        return None

    def clearGenerationMarkers (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                return
            value = [ value ]
        for v in value:
            assert v is not None
            v.__generated = False

    def nextValueToGenerate (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                raise DOMGenerationError('Optional %s value is not available' % (self.pythonField(),))
            value = [ value ]
        for v in value:
            if not v.__generated:
                v.__generated = True
                return v
        raise DOMGenerationError('No %s values remain to be generated' % (self.pythonField(),))

    def hasUngeneratedValues (self, ctd_instance):
        value = self.value(ctd_instance)
        if not self.isPlural():
            if value is None:
                return False
            value = [ value ]
        for v in value:
            if not v.__generated:
                return True
        return False

    def value (self, ctd_instance):
        return getattr(ctd_instance, self.__valueElementName, self.defaultValue())

    def reset (self, ctd_instance):
        setattr(ctd_instance, self.__valueElementName, self.defaultValue())
        return self

    def __setValue (self, ctd_instance, value):
        if self.isPlural():
            values = self.value(ctd_instance)
            values.append(value)
            return values
        return setattr(ctd_instance, self.__valueElementName, value)

    # @todo Distinguish based on plurality
    def setValue (self, ctd_instance, value):
        """Set the value of this element in the given instance."""
        if value is None:
            return self.reset(ctd_instance)
        assert self.__dataTypes is not None
        for dt in self.__dataTypes:
            if isinstance(value, dt):
                self.__setValue(ctd_instance, value)
                ctd_instance._addContent(value)
                return self
        for dt in self.__dataTypes:
            try:
                iv = dt(value)
                self.__setValue(ctd_instance, iv)
                ctd_instance._addContent(iv)
                return self
            except BadTypeValueError, e:
                pass
        raise BadTypeValueError('Cannot assign value of type %s to field %s: legal types %s' % (type(value), self.tag(), ' '.join([str(_dt) for _dt in self.__dataTypes])))

    def addDOMElement (self, value, document, element):
        """Add the given value of the corresponding element field to the DOM element."""
        if value is not None:
            assert isinstance(value, basis.element)
            value.toDOM(document, parent=element)
        return self

class Particle (object):
    """Record defining the structure and number of an XML object.
    This is a min and max count associated with a
    ModelGroup, ElementDeclaration, or Wildcard."""
    # The minimum number of times the term may appear.
    __minOccurs = 1
    def minOccurs (self):
        """The minimum number of times the term may appear.

        Defaults to 1."""
        return self.__minOccurs

    # Upper limit on number of times the term may appear.
    __maxOccurs = 1
    def maxOccurs (self):
        """Upper limit on number of times the term may appear.

        If None, the term may appear any number of times; otherwise,
        this is an integral value indicating the maximum number of times
        the term may appear.  The default value is 1; the value, unless
        None, must always be at least minOccurs().
        """
        return self.__maxOccurs

    # A reference to a ModelGroup, WildCard, or ElementDeclaration
    __term = None
    def term (self):
        """A reference to a ModelGroup, Wildcard, or ElementDeclaration."""
        return self.__term

    def isPlural (self):
        """Return true iff the term might appear multiple times."""
        if (self.maxOccurs() is None) or 1 < self.maxOccurs():
            return True
        return self.term().isPlural()

    def __init__ (self, min_occurs, max_occurs, term):
        self.__minOccurs = min_occurs
        self.__maxOccurs = max_occurs
        self.__term = term

    def extendDOMFromContent (self, document, element, ctd_instance):
        rep = 0
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        while ((self.maxOccurs() is None) or (rep < self.maxOccurs())):
            try:
                if isinstance(self.term(), ModelGroup):
                    self.term().extendDOMFromContent(document, element, ctd_instance)
                elif isinstance(self.term(), type) and issubclass(self.term(), basis.element):
                    eu = ctd_instance._UseForElement(self.term())
                    assert eu is not None
                    value = eu.nextValueToGenerate(ctd_instance)
                    value.toDOM(document, element)
                elif isinstance(self.term(), Wildcard):
                    print 'Generation ignoring wildcard'
                    # @todo handle generation of wildcards
                    break
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except IncompleteImplementationError, e:
                raise
            except DOMGenerationError, e:
                break
            except Exception, e:
                #print 'Caught extending DOM from term %s: %s' % (self.term(), e)
                raise
            rep += 1
        if rep < self.minOccurs():
            raise DOMGenerationError('Expected at least %d instances of %s, got only %d' % (self.minOccurs(), self.term(), rep))

    def extendFromDOM (self, ctd_instance, node_list):
        """Extend the content of the given ctd_instance from the DOM
        nodes in the list.

        Nodes are removed from the front of the list as their content
        is extracted and saved.  The unconsumed portion of the list is
        returned."""
        rep = 0
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        while ((self.maxOccurs() is None) or (rep < self.maxOccurs())):
            ctd_instance._stripMixedContent(node_list)
            try:
                if isinstance(self.term(), ModelGroup):
                    self.term().extendFromDOM(ctd_instance, node_list)
                elif isinstance(self.term(), type) and issubclass(self.term(), basis.element):
                    if 0 == len(node_list):
                        raise MissingContentError('Expected element %s' % (self.term()._XsdName,))
                    element = self.term().CreateFromDOM(node_list[0])
                    node_list.pop(0)
                    ctd_instance._addElement(element)
                elif isinstance(self.term(), Wildcard):
                    if 0 == len(node_list):
                        raise MissingContentError('Expected wildcard')
                    ignored = node_list.pop(0)
                    print 'Ignoring wildcard match %s' % (ignored,)
                else:
                    raise IncompleteImplementationError('Particle.extendFromDOM: No support for term type %s' % (self.term(),))
            except StructuralBadDocumentError, e:
                #print 'Informational MCE: %s' % (e,)
                break
            except IncompleteImplementationError, e:
                raise
            except Exception, e:
                #print 'Caught creating term from DOM: %s' % (e,)
                raise
            rep += 1
        if rep < self.minOccurs():
            if 0 < len(node_list):
                raise UnrecognizedContentError('Expected at least %d instances of %s, got only %d before %s' % (self.minOccurs(), self.term(), rep, node_list[0].nodeName))
            raise MissingContentError('Expected at least %d instances of %s, got only %d' % (self.minOccurs(), self.term(), rep))
        return node_list

class ModelGroup (object):
    """Record the structure of a model group.

    This is used when interpreting a DOM document fragment, to be sure
    the correct binding structure is used to extract the contents of
    each element.  It almost does something like validation, as a side
    effect."""

    C_INVALID = 0
    C_ALL = 0x01
    C_CHOICE = 0x02
    C_SEQUENCE = 0x03

    # One of the C_* values above.  Set at construction time from the
    # keyword parameter "compositor".
    __compositor = C_INVALID
    def compositor (self):
        return self.__compositor

    # A list of _Particle instances.  Set at construction time from
    # the keyword parameter "particles".  May be sorted; see
    # _setContent.
    __particles = None
    def particles (self):
        return self.__particles

    def _setContent (self, compositor, particles):
        self.__compositor = compositor
        self.__particles = particles
        # Particle lists that might be involved in a choice are sorted
        # for greedy matching.
        if self.compositor() in (self.C_ALL, self.C_CHOICE):
            self.__particles.sort(lambda _x,_y: -cmp(_x.minOccurs(), _y.minOccurs()))

    def __init__ (self, compositor=C_INVALID, particles=None):
        self._setContent(compositor, particles)

    def __extendDOMFromChoice (self, document, element, ctd_instance, candidate_particles):
        # Correct behavior requires that particles with a minOccurs()
        # of 1 preceed any particle with minOccurs() of zero;
        # otherwise we can incorrectly succeed at matching while not
        # consuming everything that's available.  This sorting was
        # done in _setContent.
        for particle in candidate_particles:
            try:
                particle.extendDOMFromContent(document, element, ctd_instance)
                return particle
            except DOMGenerationError, e:
                pass
            except Exception, e:
                #print 'GEN CHOICE failed: %s' % (e,)
                raise
        return None

    def extendDOMFromContent (self, document, element, ctd_instance):
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        if self.C_SEQUENCE == self.compositor():
            for particle in self.particles():
                particle.extendDOMFromContent(document, element, ctd_instance)
        elif self.C_ALL == self.compositor():
            mutable_particles = self.particles().copy()
            while 0 < len(mutable_particles):
                try:
                    choice = self.__extendDOMFromChoice(document, element, ctd_instance, mutable_particles)
                    mutable_particles.remove(choice)
                except DOMGenerationError, e:
                    #print 'ALL failed: %s' % (e,)
                    break
            for particle in mutable_particles:
                if 0 < particle.minOccurs():
                    raise DOMGenerationError('ALL: Could not generate instance of required %s' % (particle.term(),))
        elif self.C_CHOICE == self.compositor():
            choice = self.__extendDOMFromChoice(document, element, ctd_instance, self.particles())
            if choice is None:
                raise DOMGenerationError('CHOICE: No candidates found')
        else:
            assert False
        
    def __extendContentFromChoice (self, ctd_instance, node_list, candidate_particles):
        # @todo Is there a preference to match particles that have a
        # minOccurs of 1?  Probably....
        for particle in candidate_particles:
            assert particle.minOccurs() in (0, 1)
            assert 1 == particle.maxOccurs()
            try:
                particle.extendFromDOM(ctd_instance, node_list)
                return particle
            except BadDocumentError, e:
                #print 'CHOICE failed: %s' % (e,)
                pass
        if 0 < len(node_list):
            raise UnrecognizedContentError(node_list[0])
        raise MissingContentError('No match for required choice')

    def extendFromDOM (self, ctd_instance, node_list):
        assert isinstance(ctd_instance, basis.complexTypeDefinition)
        if self.C_SEQUENCE == self.compositor():
            for particle in self.particles():
                try:
                    particle.extendFromDOM(ctd_instance, node_list)
                except BadDocumentError, e:
                    #print 'SEQUENCE failed: %s' % (e,)
                    raise
            return
        elif self.C_ALL == self.compositor():
            mutable_particles = self.particles()[:]
            while 0 < len(mutable_particles):
                try:
                    choice = self.__extendContentFromChoice(ctd_instance, node_list, mutable_particles)
                    mutable_particles.remove(choice)
                except BadDocumentError, e:
                    #print 'ALL failed: %s' % (e,)
                    break
            for particle in mutable_particles:
                if 0 < particle.minOccurs():
                    raise MissingContentError('ALL: Expected an instance of %s' % (particle.term(),))
            #print 'Ignored unused %s' % (mutable_particles,)
            return
        elif self.C_CHOICE == self.compositor():
            choice = self.__extendContentFromChoice(ctd_instance, node_list, self.particles())
            return
        else:
            assert False

class Wildcard (object):
    """Placeholder for wildcard objects."""

    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace'
    NC_local = '##local'

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:
         * Wildcard.NC_any
         * A tuple ( Wildcard.NC_not, a_namespace )
         * set(of_namespaces)

        Namespaces are represented by their URIs.  Absence is
        represented by None, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    PC_skip = 'skip'            #<<< No constraint is applied
    PC_lax = 'lax'              #<<< Validate against available uniquely determined declaration
    PC_strict = 'strict'        #<<< Validate against declaration or xsi:type which must be available

    # One of PC_*
    __processContents = None
    def processContents (self): return self.__processContents

    def __init__ (self, *args, **kw):
        pass
