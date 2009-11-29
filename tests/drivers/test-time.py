import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/time.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

def make_tTime (*args, **kw):
    for cls in [ tXMTime, tISO8601 ]:
        try:
            v = cls(*args, **kw)
            v.toxml()
            return v
        except Exception, e:
            pass
    return None
tTime._SetAlternativeConstructor(make_tTime)

import unittest

class TestTime (unittest.TestCase):
    KW_tISO8601 = { 'time' : '2009-06-03T13:43:00Z' }
    KW_tXMTime = { 'seconds' : 2, 'fractionalSeconds' : 0.3 }
    def testXMTime (self):
        t = tXMTime(seconds=1)
        self.assertEqual(1, t.seconds)
        self.assertEqual(None, t.fractionalSeconds)
        t = tXMTime(**self.KW_tXMTime)
        self.assertEqual(2, t.seconds)
        self.assertEqual(0.3, t.fractionalSeconds)
        t._setElement(time)
        xmls = t.toxml()
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.seconds, t.seconds)
        self.assertEqual(instance.fractionalSeconds, t.fractionalSeconds)

    def testISO8601 (self):
        t = tISO8601(**self.KW_tISO8601)
        self.assertEqual((2009, 6, 3, 13, 43, 0, 2, 154, -1), t.time.timetuple())
        t._setElement(time)
        xmls = t.toxml()
        instance = CreateFromDocument(xmls)
        self.assertEqual(instance.time.timetuple(), t.time.timetuple())

    def testAbstract (self):
        self.assertRaises(pyxb.AbstractInstantiationError, tTime, **self.KW_tXMTime)
        t = make_tTime(**self.KW_tXMTime)
        self.assertTrue(isinstance(t, tTime))
        self.assertTrue(isinstance(t, tXMTime))
        t = make_tTime(**self.KW_tISO8601)
        self.assertTrue(isinstance(t, tTime))
        self.assertTrue(isinstance(t, tISO8601))
        t = tTime.Factory(**self.KW_tXMTime)
        self.assertTrue(isinstance(t, tTime))
        self.assertTrue(isinstance(t, tXMTime))
        


if __name__ == '__main__':
    unittest.main()
    
        
