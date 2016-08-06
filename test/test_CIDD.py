import unittest
from plugins.util.dict import CaseInsensitiveDefaultDict as CIDD

class TestCIDD(unittest.TestCase):
    def testContains(self):
        sample = CIDD()
        sample["aBc"] = 42
        self.assertTrue("aBc" in sample)
        self.assertTrue("abc" in sample)

    def testPop(self):
        sample = CIDD()
        sample["aBc"] = 42
        self.assertEqual(sample.pop("aBc"), 42)

        # Test case-insensitive compare
        sample["aBc"] = 42
        self.assertEqual(sample.pop("abc"), 42)

        # Test default value pop
        default = "Life, the Universe and Everything"
        self.assertEqual(sample.pop("abc", default), default)

    def testGet(self):
        sample = CIDD()
        sample["aBc"] = 42
        self.assertEqual(sample.get("abc"), 42)

        del sample["abc"]

        default = "Life, the Universe and Everything"
        self.assertEqual(sample.get("abc", default), default)

    def testDelete(self):
        sample = CIDD()
        sample["abc"] = 42
        self.assertEqual(sample, {"abc": 42})

        del sample["aBc"]
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
