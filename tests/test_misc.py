import imghdr
import sys
import unittest

from hypothesis import example, given, strategies as st


class TestBuiltins(unittest.TestCase):
    @example(n=2 ** 63)
    @given(st.integers(min_value=0))
    def test_len_of_range(self, n):
        seq = range(n)
        try:
            length = len(seq)
        except OverflowError:
            # len() internally casts to ssize_t, so we expect overflow here.
            self.assertGreater(n, sys.maxsize)
        else:
            self.assertEqual(length, n)


class TestImghdr(unittest.TestCase):
    @given(st.binary())
    def test_imghdr_what(self, payload):
        imghdr.what("<ignored filename>", h=payload)
