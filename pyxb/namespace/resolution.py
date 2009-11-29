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

"""Classes and global objects related to resolving U{XML
Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}."""

import pyxb
import os
import fnmatch
import pyxb.utils.utility
import archive
import utility

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

    def _transferReferencedNamespaces (self, module_record):
        assert isinstance(module_record, archive.ModuleRecord)
        module_record._setReferencedNamespaces(self.__referencedNamespaces)
        self.__referencedNamespaces.clear()
        
    def referencedNamespaces (self):
        """Return the set of namespaces which appear in namespace declarations
        of schema with this namespace as target."""
        return frozenset(self.__referencedNamespaces)
        rn = self.__referencedNamespaces.copy()
        for mr in self.moduleRecords():
            if mr.isIncorporated():
                rn.update(mr.referencedNamespaces())
        return rn

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
        ns.configureCategories([archive.NamespaceArchive._AnonymousCategory()])
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

class NamespaceContext (object):
    """Records information associated with namespaces at a DOM node.
    """

    def __str__ (self):
        rv = [ 'NamespaceContext ' ]
        if self.defaultNamespace() is not None:
            rv.extend([ '(defaultNamespace=', str(self.defaultNamespace()), ') '])
        if self.targetNamespace() is not None:
            rv.extend([ '(targetNamespace=', str(self.targetNamespace()), ') '])
        rv.append("\n")
        for (pfx, ns) in self.inScopeNamespaces().items():
            if pfx is not None:
                rv.append('  xmlns:%s=%s' % (pfx, str(ns)))
        return ''.join(rv)

    __TargetNamespaceAttributes = { }
    @classmethod
    def _AddTargetNamespaceAttribute (cls, expanded_name, attribute_name):
        assert expanded_name is not None
        cls.__TargetNamespaceAttributes[expanded_name] = attribute_name
    @classmethod
    def _TargetNamespaceAttribute (cls, expanded_name):
        return cls.__TargetNamespaceAttributes.get(expanded_name, None)

    # Support for holding onto referenced namespaces until we have a target
    # namespace to give them to.
    __pendingReferencedNamespaces = None
    
    def defaultNamespace (self):
        """The default namespace in effect at this node.  E.g., C{xmlns="URN:default"}."""
        return self.__defaultNamespace
    __defaultNamespace = None

    # If C{True}, this context is within a schema that has no target
    # namespace, and we should use the target namespace as a fallback if no
    # default namespace is available and no namespace prefix appears on a
    # QName.  This situation arises when a top-level schema has an absent
    # target namespace, or when a schema with an absent target namespace is
    # being included into a schema with a non-absent target namespace.
    __fallbackToTargetNamespace = False

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

    def setNodeContext (self, node):
        node.__namespaceContext = self

    def processXMLNS (self, prefix, uri):
        if not self.__mutableInScopeNamespaces:
            self.__inScopeNamespaces = self.__inScopeNamespaces.copy()
            self.__mutableInScopeNamespaces = True
        if uri:
            if prefix is None:
                ns = self.__defaultNamespace = utility.NamespaceForURI(uri, create_if_missing=True)
                self.__inScopeNamespaces[None] = self.__defaultNamespace
            else:
                ns = utility.NamespaceForURI(uri, create_if_missing=True)
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
            self.__inScopeNamespaces.pop(prefix, None)
            self.__defaultNamespace = None

    def finalizeTargetNamespace (self, tns_uri=None, including_context=None):
        if tns_uri is not None:
            assert 0 < len(tns_uri)
            # Do not prevent overwriting target namespace; need this for WSDL
            # files where an embedded schema inadvertently inherits a target
            # namespace from its enclosing definitions element.  Note that if
            # we don't check this here, we do have to check it when schema
            # documents are included into parent schema documents.
            self.__targetNamespace = utility.NamespaceForURI(tns_uri, create_if_missing=True)
        elif self.__targetNamespace is None:
            if including_context is not None:
                self.__targetNamespace = including_context.targetNamespace()
                self.__fallbackToTargetNamespace = True
            elif tns_uri is None:
                self.__targetNamespace = utility.CreateAbsentNamespace()
            else:
                self.__targetNamespace = utility.NamespaceForURI(tns_uri, create_if_missing=True)
        if self.__pendingReferencedNamespaces is not None:
            [ self.__targetNamespace._referenceNamespace(_ns) for _ns in self.__pendingReferencedNamespaces ]
            self.__pendingReferencedNamespace = None
        assert self.__targetNamespace is not None
        if (not self.__fallbackToTargetNamespace) and self.__targetNamespace.isAbsentNamespace():
            self.__fallbackToTargetNamespace = True

    def __init__ (self,
                  dom_node=None,
                  parent_context=None,
                  including_context=None,
                  recurse=True,
                  default_namespace=None,
                  target_namespace=None,
                  in_scope_namespaces=None,
                  expanded_name=None,
                  finalize_target_namespace=True):  # MUST BE True for WSDL to work with minidom
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
        import builtin

        if dom_node is not None:
            try:
                assert dom_node.__namespaceContext is None
            except AttributeError:
                pass
            dom_node.__namespaceContext = self

        self.__defaultNamespace = default_namespace
        self.__targetNamespace = target_namespace
        self.__inScopeNamespaces = builtin._UndeclaredNamespaceMap
        self.__mutableInScopeNamespaces = False

        if in_scope_namespaces is not None:
            if parent_context is not None:
                raise LogicError('Cannot provide both parent_context and in_scope_namespaces')
            self.__inScopeNamespaces = builtin._UndeclaredNamespaceMap.copy()
            self.__inScopeNamespaces.update(in_scope_namespaces)
            self.__mutableInScopeNamespaces = True
        
        if parent_context is not None:
            self.__inScopeNamespaces = parent_context.inScopeNamespaces()
            self.__mutableInScopeNamespaces = False
            self.__defaultNamespace = parent_context.defaultNamespace()
            self.__targetNamespace = parent_context.targetNamespace()
            self.__fallbackToTargetNamespace = parent_context.__fallbackToTargetNamespace
            
        if self.__targetNamespace is None:
            self.__pendingReferencedNamespaces = set()
        attribute_map = {}
        if dom_node is not None:
            if expanded_name is None:
                expanded_name = pyxb.namespace.ExpandedName(dom_node)
            for ai in range(dom_node.attributes.length):
                attr = dom_node.attributes.item(ai)
                if builtin.XMLNamespaces.uri() == attr.namespaceURI:
                    prefix = attr.localName
                    if 'xmlns' == prefix:
                        prefix = None
                    self.processXMLNS(prefix, attr.value)
                else:
                    if attr.namespaceURI is not None:
                        uri = utility.NamespaceForURI(attr.namespaceURI, create_if_missing=True)
                        key = pyxb.namespace.ExpandedName(uri, attr.localName)
                    else:
                        key = pyxb.namespace.ExpandedName(None, attr.localName)
                    attribute_map[key] = attr.value
        
        if finalize_target_namespace:
            tns_uri = None
            tns_attr = self._TargetNamespaceAttribute(expanded_name)
            if tns_attr is not None:
                tns_uri = attribute_map.get(tns_attr)
                self.finalizeTargetNamespace(tns_uri, including_context=including_context)

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        if (dom_node is not None) and recurse:
            from xml.dom import Node
            assert Node.ELEMENT_NODE == dom_node.nodeType
            for cn in dom_node.childNodes:
                if Node.ELEMENT_NODE == cn.nodeType:
                    NamespaceContext(cn, self, True)

    def interpretQName (self, name, namespace=None):
        """Convert the provided name into an L{ExpandedName}, i.e. a tuple of
        L{Namespace} and local name.

        If the name includes a prefix, that prefix must map to an in-scope
        namespace in this context.  Absence of a prefix maps to
        L{defaultNamespace()}, which must be provided (or defaults to the
        target namespace, if that is absent).
        
        @param name: A QName.
        @type name: C{str} or C{unicode}
        @param name: Optional namespace to use for unqualified names when
        there is no default namespace.  Note that a defined default namespace,
        even if absent, supersedes this value.
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
            # Context default supersedes caller-provided namespace
            if self.defaultNamespace() is not None:
                namespace = self.defaultNamespace()
            # If there's no default namespace, but there is a fallback
            # namespace, use that instead.
            if (namespace is None) and self.__fallbackToTargetNamespace:
                namespace = self.targetNamespace()
            if namespace is None:
                raise pyxb.SchemaValidationError('QName %s with absent default namespace cannot be resolved' % (local_name,))
        # Anything we're going to look stuff up in requires a component model.
        # Make sure we can load one, unless we're looking up in the thing
        # we're constructing (in which case it's being built right now).
        if (namespace != self.targetNamespace()):
            namespace.validateComponentModel()
        return pyxb.namespace.ExpandedName(namespace, local_name)

    def queueForResolution (self, component):
        """Forwards to L{queueForResolution()<Namespace.queueForResolution>} in L{targetNamespace()}."""
        assert isinstance(component, _Resolvable_mixin)
        return self.targetNamespace().queueForResolution(component)

## Local Variables:
## fill-column:78
## End:
