import colorsys
import quopri
import unittest

from hypothesis import given, strategies as st, target


class TestBase64(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/base64.html
    pass


class TestBinASCII(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/binascii.html
    pass


class TestColorsys(unittest.TestCase):
    # Module documentation https://docs.python.org/3/library/colorsys.html

    @given(
        r=st.floats(0.0, 1.0), g=st.floats(0.0, 1.0), b=st.floats(0.0, 1.0),
    )
    def test_rgb_yiq_round_trip(self, r, g, b):
        y, i, q = colorsys.rgb_to_yiq(r, g, b)
        r2, g2, b2 = colorsys.yiq_to_rgb(y, i, q)

        self.assertAlmostEqual(r, r2)
        self.assertAlmostEqual(g, g2)
        self.assertAlmostEqual(b, b2)

    # This appears to be a genuine and serious bug in YIQ/RBG/YIQ color
    # conversion.  We're using the `@unittest.expectedFailure` decorator
    # to silence this for now, but will report it on bugs.python.org too.
    # Highest observed target scores:
    #     0.247024  (label='absolute difference in Q values')
    #     0.247234  (label='absolute difference in Y values')
    #     0.341794  (label='absolute difference in I values')
    @unittest.expectedFailure
    @given(
        y=st.floats(0.0, 1.0), i=st.floats(-0.523, 0.523), q=st.floats(-0.596, 0.596),
    )
    def test_yiq_rgb_round_trip(self, y, i, q):
        r, g, b = colorsys.yiq_to_rgb(y, i, q)
        y2, i2, q2 = colorsys.rgb_to_yiq(r, g, b)

        target(abs(y - y2), label="absolute difference in Y values")
        target(abs(i - i2), label="absolute difference in I values")
        target(abs(q - q2), label="absolute difference in Q values")
        self.assertAlmostEqual(y, y2)
        self.assertAlmostEqual(i, i2)
        self.assertAlmostEqual(q, q2)

    @given(
        r=st.floats(0.0, 1.0), g=st.floats(0.0, 1.0), b=st.floats(0.0, 1.0),
    )
    def test_rgb_hls_round_trip(self, r, g, b):
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)

        self.assertAlmostEqual(r, r2)
        self.assertAlmostEqual(g, g2)
        self.assertAlmostEqual(b, b2)

    @given(
        r=st.floats(0.0, 1.0), g=st.floats(0.0, 1.0), b=st.floats(0.0, 1.0),
    )
    def test_rgb_hsv_round_trip(self, r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)

        self.assertAlmostEqual(r, r2)
        self.assertAlmostEqual(g, g2)
        self.assertAlmostEqual(b, b2)


class TestPlistlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/plistlib.html
    pass


class TestQuodpri(unittest.TestCase):
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    def test_quodpri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)
