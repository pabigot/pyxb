#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import TestPatternRestriction as t

xml=u"\U00010314"
p = t.test(xml)
print(p.toxml("utf-8"))
