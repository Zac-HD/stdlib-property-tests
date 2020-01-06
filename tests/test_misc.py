import imghdr
import unittest

from hypothesis import example, given, strategies as st


class TestBuiltins(unittest.TestCase):
    @unittest.expectedFailure
    @example(n=2 ** 63)
    @given(st.integers(min_value=0))
    def test_len_of_range(self, n):
        seq = range(n)
        length = len(seq)  # OverflowError: Python int too large to convert to C ssize_t
        self.assertEqual(length, n)


class TestImghdr(unittest.TestCase):
    @given(st.binary())
    def test_imghdr_what(self, payload):
        imghdr.what("<ignored filename>", h=payload)
