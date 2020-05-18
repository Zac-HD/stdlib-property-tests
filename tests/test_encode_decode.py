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

    def assertColorsValid(self, **colors):
        assert len(colors) == 3  # sanity-check
        # Our color assertion helper checks that each color is in the range
        # [0, 1], and that it approximately round-tripped.  We also "target"
        # the difference, to maximise and report the largest error each run.
        for name, values in colors.items():
            for v in values:
                self.assertGreaterEqual(
                    v, 0 if name not in "iq" else -1, msg=f"color={name!r}"
                )
                self.assertLessEqual(v, 1, msg=f"color={name!r}")
            target(
                abs(values[0] - values[1]),
                label=f"absolute difference in {name.upper()} values",
            )
            self.assertAlmostEqual(*values, msg=f"color={name!r}")

    @given(r=st.floats(0, 1), g=st.floats(0, 1), b=st.floats(0, 1))
    def test_rgb_yiq_round_trip(self, r, g, b):
        y, i, q = colorsys.rgb_to_yiq(r, g, b)
        r2, g2, b2 = colorsys.yiq_to_rgb(y, i, q)
        self.assertColorsValid(r=(r, r2), g=(g, g2), b=(b, b2))

    # Allowed ranges for I and Q values are not documented in CPython
    # https://docs.python.org/3/library/colorsys.html - and code comments
    # note "I and Q ... covers a slightly larger range [than `[0, 1`]]".
    # We therefore follow https://en.wikipedia.org/wiki/YIQ#Preconditions
    @unittest.expectedFailure
    @given(
        y=st.floats(0.0, 1.0),
        i=st.floats(-0.5957, 0.5957),
        q=st.floats(-0.5226, 0.5226),
    )
    def test_yiq_rgb_round_trip(self, y, i, q):
        r, g, b = colorsys.yiq_to_rgb(y, i, q)
        y2, i2, q2 = colorsys.rgb_to_yiq(r, g, b)
        self.assertColorsValid(y=(y, y2), i=(i, i2), q=(q, q2))

    @given(r=st.floats(0, 1), g=st.floats(0, 1), b=st.floats(0, 1))
    def test_rgb_hls_round_trip(self, r, g, b):
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
        self.assertColorsValid(r=(r, r2), g=(g, g2), b=(b, b2))

        h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)
        self.assertColorsValid(h=(h, h2), l=(l, l2), s=(s, s2))

    @unittest.expectedFailure
    @given(r=st.floats(0, 1), g=st.floats(0, 1), b=st.floats(0, 1))
    def test_rgb_hsv_round_trip(self, r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
        self.assertColorsValid(r=(r, r2), g=(g, g2), b=(b, b2))

        h2, s2, v2 = colorsys.rgb_to_hls(r2, g2, b2)
        self.assertColorsValid(h=(h, h2), s=(s, s2), v=(v, v2))


class TestPlistlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/plistlib.html
    pass


class TestQuodpri(unittest.TestCase):
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    def test_quodpri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)
