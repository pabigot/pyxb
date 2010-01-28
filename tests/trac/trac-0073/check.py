import base
import profile
import unittest

class TestTrac0073 (unittest.TestCase):
    def testProfile (self):
        amap = profile.AbstractFeatureBaseType._AttributeMap
        self.assertEqual(1, len(amap))
        base_id = base.Namespace.createExpandedName('id')
        self.assertTrue(base_id in amap)

if __name__ == '__main__':
    unittest.main()
