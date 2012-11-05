import pyxb
import pyxb.binding.datatypes as xs
import trac26
import unittest

# By default skip the "tests" which actually emit the exception
# backtrace.  Sometimes though it's good to see those, since they're
# what the user will normally see first.
DisplayException = False
#DisplayException = True

class TestAbstractElementError (unittest.TestCase):
    Good_xmls = '<eCardinals><eConcCardCymru>un</eConcCardCymru><eConcCardEnglish>three</eConcCardEnglish></eCardinals>'

    Bad_xmls = '<eCardinals><eConcCardCymru>un</eConcCardCymru><eAbstractCard>three</eAbstractCard></eCardinals>'

    def testSchemaSupport (self):
        cym1 = trac26.eConcCardCymru('un')
        eng3 = trac26.eConcCardEnglish('three')

        # Incremental through owning element
        instance = trac26.eCardinals()
        self.assertEqual(0, len(instance.eAbstractCard))
        instance.append(cym1)
        self.assertEqual(1, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        instance.append(eng3)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())
        xmls = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmls, self.Good_xmls)

        # Incremental through construtor element
        instance = trac26.eCardinals(cym1, eng3)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())
        xmls = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmls, self.Good_xmls)

        # Through parsing
        instance = trac26.CreateFromDocument(self.Good_xmls)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.AbstractElementError) as cm:
            instance = trac26.eAbstractCard('un')
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertEqual(e.element, trac26.eAbstractCard)
        self.assertEqual(e.value, ('un',))
        self.assertEqual(str(e), 'Cannot instantiate abstract element eAbstractCard directly')

    def testFromDocument (self):
        instance = None
        with self.assertRaises(pyxb.AbstractElementError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmls)
        e = cm.exception
        self.assertFalse(e.location is None)
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(47, e.location.columnNumber)

    def testDisplayException (self):
        if DisplayException:
            trac26.eAbstractCard('un')

    def testIncremental (self):
        # Without type information, incremental does not work.  The content
        # model fails to recognize it, and it looks like mixed content.
        instance = trac26.eCardinals()
        self.assertEqual(0, len(instance.eAbstractCard))
        self.assertRaises(pyxb.MixedContentError, instance.append, 'un')

class TestAbstractInstantiationError (unittest.TestCase):

    Good_xmls = '<eUseAbstract xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><eAbstract xsi:type="tConcSubCymru"><welsh>un</welsh></eAbstract></eUseAbstract>'

    Bad_xmls = '<eUseAbstract xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><eAbstract><welsh>un</welsh></eAbstract></eUseAbstract>'

    def testSchemaSupport (self):
        cym1 = trac26.tConcSubCymru('un')
        eng3 = trac26.tConcSubEnglish('three')
        # Direct generation works
        instance = trac26.eUseAbstract(cym1)
        # So does from documents with xsi:type
        i2 = trac26.CreateFromDocument(self.Good_xmls)
        self.assertTrue(isinstance(i2.eAbstract, trac26.tConcSubCymru))

    def testException (self):
        scym1 = trac26.tCardCymru('un')
        instance = None
        with self.assertRaises(pyxb.AbstractInstantiationError) as cm:
            instance = trac26.eAbstract(scym1)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertEqual(str(e), 'Cannot instantiate abstract type tAbstract directly')

    def testFromDocument (self):
        instance = None
        with self.assertRaises(pyxb.AbstractInstantiationError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmls)
        e = cm.exception
        self.assertTrue(instance is None)
        # Location within Bad_xmls where error occurred
        self.assertFalse(e.location is None)
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(68, e.location.columnNumber)

    def testDisplayException (self):
        if DisplayException:
            scym1 = trac26.tCardCymru('un')
            trac26.eAbstract(scym1)

    def testDisplayExceptionDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmls)

class TestSimpleContentAbsentError (unittest.TestCase):

    Good_xmls = '<eCTwSC>3</eCTwSC>'
    Bad_xmls = '<eCTwSC></eCTwSC>'

    GoodSeq_xmls = '<eCTwSCSequence><eCTwSC>1</eCTwSC><eCTwSC>2</eCTwSC></eCTwSCSequence>'
    BadSeq_xmls = '<eCTwSCSequence><eCTwSC>1</eCTwSC><eCTwSC></eCTwSC></eCTwSCSequence>'

    def testSchemaSupport (self):
        instance = trac26.eCTwSC(3)
        self.assertEqual(3, instance.value())
        instance = trac26.CreateFromDocument(self.Good_xmls)
        self.assertEqual(3, instance.value())
        instance = trac26.eCTwSCSequence()
        # Can't infer conversion why?
        instance.eCTwSC.append(trac26.eCTwSC(1))
        instance.eCTwSC.append(trac26.eCTwSC(2))
        instance = trac26.CreateFromDocument(self.GoodSeq_xmls)
        xmls = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmls, self.GoodSeq_xmls)
        

    def testDirect (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.eCTwSC()
        e = cm.exception
        self.assertTrue(instance is None)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmls)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertFalse(e.location is None)
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(str(e), 'Type {http://www.w3.org/2001/XMLSchema}int requires content')

    def testDocumentSeq (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.CreateFromDocument(self.BadSeq_xmls)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertFalse(e.location is None)
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(34, e.location.columnNumber)
        self.assertEqual(str(e), 'Type {http://www.w3.org/2001/XMLSchema}int requires content')

    def testDisplayException (self):
        if DisplayException:
            instance = trac26.eCTwSC()

    def testDisplayExceptionDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.BadSeq_xmls)
        
class TestReservedNameError (unittest.TestCase):
    def testSchemaSupport (self):
        instance = trac26.eCTwSC(4)
        instance.nottoxml = 1

    def testException (self):
        instance = trac26.eCTwSC(4)
        with self.assertRaises(pyxb.ReservedNameError) as cm:
            instance.toxml = 1
        e = cm.exception
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.name, 'toxml')

    def testDisplayException (self):
        if DisplayException:
            trac26.eCTwSC(4).toxml = 1

class TestNotComplexContentError (unittest.TestCase):
    # No tests on documents as the exception is raised only in code
    # that invokes the content() method.

    def testSchemaSupport (self):
        instance = trac26.eEmpty()
        instance = trac26.eCTwSC(4)

    def testEmptyException (self):
        content = None
        instance = trac26.eEmpty()
        with self.assertRaises(pyxb.NotComplexContentError) as cm:
            content = instance.content()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testSimpleException (self):
        content = None
        instance = trac26.eCTwSC(4)
        with self.assertRaises(pyxb.NotComplexContentError) as cm:
            content = instance.content()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testDisplayException (self):
        if DisplayException:
            trac26.eEmpty().content()

class TestNotSimpleContentError (unittest.TestCase):
    # No tests on documents as the exception is raised only in code
    # that invokes the content() method.

    def testSchemaSupport (self):
        instance = trac26.eEmpty()
        cym1 = trac26.tConcSubCymru('un')
        instance = trac26.eUseAbstract(cym1)

    def testEmptyException (self):
        value = None
        instance = trac26.eEmpty()
        with self.assertRaises(pyxb.NotSimpleContentError) as cm:
            value = instance.value()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testComplexException (self):
        value = None
        instance = trac26.eUseAbstract(trac26.tConcSubCymru('un'))
        with self.assertRaises(pyxb.NotSimpleContentError) as cm:
            value = instance.value()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testDisplayException (self):
        if DisplayException:
            trac26.eEmpty().value()

class TestAttributeChangeError (unittest.TestCase):

    Good_xmls = '<eAttributes aFixed="5" aReq="2"/>'
    Bad_xmls = '<eAttributes aFixed="2" aReq="2"/>'

    def testSchemaSupport (self):
        instance = trac26.tAttributes(aReq=2)
        self.assertEqual(instance.aReq, 2)
        self.assertEqual(instance.aFixed, 5)
        self.assertTrue(instance.validateBinding())
        # OK to explicitly assign fixed value
        instance.aFixed = 5
        instance = trac26.CreateFromDocument(self.Good_xmls)
        self.assertEqual(self.Good_xmls, instance.toxml('utf-8',root_only=True))

    def testDirect (self):
        instance = trac26.tAttributes(aReq=2)
        with self.assertRaises(pyxb.AttributeChangeError) as cm:
            instance.aFixed = 1
        e = cm.exception
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aFixed')
        self.assertEqual(e.instance, instance)
        self.assertTrue(e.location is None)

    def testDisplayException (self):
        if DisplayException:
            trac26.tAttributes(aReq=2).aFixed = 1

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.AttributeChangeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmls)
        self.assertTrue(instance is None)
        e = cm.exception
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aFixed')
        self.assertFalse(e.instance is None) # there, but partially defined
        self.assertFalse(e.location is None)
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(0, e.location.columnNumber)

    def testDisplayExceptionDoc (self):
        if DisplayException:
            trac26.CreateFromDocument(self.Bad_xmls)


class TestAttributeValueError (unittest.TestCase):
    # AttributeValueError was intended to be raised when batch
    # validation discovered that the value was not suited for the type
    # of the attribute.  This can no longer happen since attribute
    # values are validated when they are assigned.  Consequently such
    # errors show up as SimpleTypeValueErrors.  Test for those instead.

    Good_xmls = '<eAttributes aCardCymru="pedwar" aReq="4"/>'
    Bad_xmls = '<eAttributes aCardCymru="four" aReq="4"/>'

    def testSchemaSupport (self):
        instance = trac26.tAttributes(aCardCymru='pedwar', aReq=4)
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmls)
        self.assertEqual(self.Good_xmls, instance.toxml('utf-8', root_only=True))
        instance.aCardCymru = 'dau'
        self.assertTrue(instance.validateBinding())

    def testAssignment (self):
        instance = trac26.eAttributes(aReq=4)
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance.aCardCymru = 'four'
        e = cm.exception
        au = trac26.tAttributes._AttributeMap['aCardCymru']
        self.assertTrue(isinstance(e, pyxb.SimpleFacetValueError))
        self.assertEqual(e.type, au.dataType())
        self.assertEqual(e.value, 'four')
        self.assertEqual(e.facet, au.dataType()._CF_enumeration)
        self.assertEqual(str(e), "Type <class 'trac26.tCardCymru'> enumeration constraint violated by value four")

    def testConstructor (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = trac26.eAttributes(aReq=4, aCardCymru='four')

    def testDocument (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmls)

if __name__ == '__main__':
    unittest.main()
