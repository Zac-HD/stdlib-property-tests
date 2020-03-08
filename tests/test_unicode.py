import unittest
from unicodedata import normalize

from hypothesis import given, strategies as st

# For every (n1, n2, n3) triple, applying n1 then n2 must be the same
# as applying n3.
# Reference: http://unicode.org/reports/tr15/#Design_Goals
compositions = [
    ("NFC", "NFC", "NFC"),
    ("NFC", "NFD", "NFD"),
    ("NFC", "NFKC", "NFKC"),
    ("NFC", "NFKD", "NFKD"),
    ("NFD", "NFC", "NFC"),
    ("NFD", "NFD", "NFD"),
    ("NFD", "NFKC", "NFKC"),
    ("NFD", "NFKD", "NFKD"),
    ("NFKC", "NFC", "NFKC"),
    ("NFKC", "NFD", "NFKD"),
    ("NFKC", "NFKC", "NFKC"),
    ("NFKC", "NFKD", "NFKD"),
    ("NFKD", "NFC", "NFKC"),
    ("NFKD", "NFD", "NFKD"),
    ("NFKD", "NFKC", "NFKC"),
    ("NFKD", "NFKD", "NFKD"),
]


class TestUnicode(unittest.TestCase):
    @given(s=st.text(), comps=st.sampled_from(compositions))
    def test_composition(self, s, comps):
        # see issues https://foss.heptapod.net/pypy/pypy/issues/2289
        # and https://bugs.python.org/issue26917
        norm1, norm2, norm3 = comps
        self.assertEqual(normalize(norm2, normalize(norm1, s)), normalize(norm3, s))

    @given(u=st.text(), prefix=st.text(), suffix=st.text())
    def test_find_index(self, u, prefix, suffix):
        s = prefix + u + suffix
        index = s.find(u)
        index2 = s.index(u)
        self.assertEqual(index, index2)
        self.assertLessEqual(0, index)
        self.assertLessEqual(index, len(prefix))

        index = s.find(u, len(prefix), len(s) - len(suffix))
        index2 = s.index(u, len(prefix), len(s) - len(suffix))
        self.assertEqual(index, len(prefix))
        self.assertEqual(index2, len(prefix))

    @given(u=st.text(), prefix=st.text(), suffix=st.text())
    def test_rfind(self, u, prefix, suffix):
        s = prefix + u + suffix
        index = s.rfind(u)
        index2 = s.rindex(u)
        self.assertEqual(index, index2)
        self.assertGreaterEqual(index, len(prefix))

        index = s.rfind(u, len(prefix), len(s) - len(suffix))
        index2 = s.rindex(u, len(prefix), len(s) - len(suffix))
        self.assertEqual(index, index2)
        self.assertEqual(index, len(prefix))
