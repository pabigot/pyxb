#!/usr/bin/env python
# -*- coding: utf-8 -*-
import TestPatternRestriction as t

xml=u"\U00010314";
p = t.TestPatternRestriction(xml)
print p.toxml("utf-8")
