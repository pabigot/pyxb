# -*- coding: utf-8 -*-
# Copyright 2009-2017, Peter A. Bigot
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

from __future__ import print_function
import os.path
from docutils import nodes
import sys
import re

__Reference_re = re.compile('\s*(.*)\s+<(.*)>\s*$', re.MULTILINE + re.DOTALL)

def ticket_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:ticket:` generates references to SourceForge tickets.
    """
    trac_root = 'https://sourceforge.net/p/pyxb/tickets'

    # assume module is references

    #print 'Text "%s"' % (text,)
    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    ticket = text.strip()

    uri = '%s/%s/' % (trac_root, ticket)
    if label is None:
        label = 'SF ticket %s' % (ticket,)
    node = nodes.reference(rawtext, label, refuri=uri, **options)

    return [node], []

def issue_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:issue:` generates references to github issues.
    """
    issue_root = 'https://github.com/pabigot/pyxb/issues'

    # assume module is references

    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    ticket = text.strip()

    uri = '%s/%s/' % (issue_root, ticket)
    if label is None:
        label = 'issue %s' % (ticket,)
    node = nodes.reference(rawtext, label, refuri=uri, **options)

    return [node], []

def setup(app):
    app.add_role('ticket', ticket_role)
    app.add_role('issue', issue_role)
