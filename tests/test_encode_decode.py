import quopri
import unittest
import colorsys

from hypothesis import given, strategies as st


class TestBase64(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/base64.html
    pass


class TestBinASCII(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/binascii.html
    pass


class TestColorsys(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/colorsys.html
    @given(
        r=st.floats(0.0, 1.0),
        g=st.floats(0.0, 1.0),
        b=st.floats(0.0, 1.0),
        h=st.floats(0.0, 1.0),
        s=st.floats(0.0, 1.0),
        v=st.floats(0.0, 1.0),
    )
    def test_rgb_hsv_round_trip(self, r, g, b, h, s, v):
        hsv = colorsys.rgb_to_hsv(r, g, b)
        rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])

        self.assertSequenceEqual((r, g, b), rgb)


class TestPlistlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/plistlib.html
    pass


class TestQuodpri(unittest.TestCase):
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    def test_quodpri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)
