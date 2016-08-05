import unittest
from plugins.util.dict import CaseInsensitiveDefaultDict as CIDD

class TestCIDD(unittest.TestCase):
    def testDelete(self):
        sample = CIDD()
        sample["abc"] = 42
        self.assertEqual(sample, {"abc": 42})
        del sample["abc"]
        self.assertEqual(sample, {})
    def testDefaultGet(self):
        """
        This test checks whether the dict behaves as a defaultdict
        """
        sample = CIDD(default=[])
        self.assertEqual(sample["ABC"], [])

    def testDefaultCopy(self):
        """
        This test checks whether the provided default value gets
        copied properly.
        """
        sample = CIDD(default=[])
        sample["abc"].append(42)
        self.assertNotEqual(sample["abc"], sample.default)

    def testCaseInsensitivity(self):
        """
        This test checks whether keys are compared
        insensitively.
        """
        sample = CIDD()
        sample["abc"] = 42
        self.assertEqual(sample["aBc"], 42)

    def testCasePreservation(self):
        """
        This test checks whether key case is preserved
        internally.
        """
        sample = CIDD()
        sample["aBc"] = 42
        self.assertEqual(sample, {"aBc": 42})
        self.assertNotEqual(sample, {"abc": 42})
