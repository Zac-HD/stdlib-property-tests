import base64
import quopri
import unittest

from hypothesis import given, strategies as st


class TestBase64(unittest.TestCase):
    @given(payload=st.binary())
    def test_b64_encode_decode_round_trip(self, payload):
        x = base64.b64encode(payload)
        self.assertEqual(payload, base64.b64decode(x))

    @given(payload=st.binary())
    def test_standard_b64_encode_decode_round_trip(self, payload):
        x = base64.standard_b64encode(payload)
        self.assertEqual(payload, base64.standard_b64decode(x))

    @given(payload=st.binary())
    def test_urlsafe_b64_encode_decode_round_trip(self, payload):
        x = base64.urlsafe_b64encode(payload)
        self.assertEqual(payload, base64.urlsafe_b64decode(x))

    @given(payload=st.binary())
    def test_b32_encode_decode_round_trip(self, payload):
        x = base64.b32encode(payload)
        self.assertEqual(payload, base64.b32decode(x))

    @given(payload=st.binary())
    def test_b16_encode_decode_round_trip(self, payload):
        x = base64.b16encode(payload)
        self.assertEqual(payload, base64.b16decode(x))

    @given(
        payload=st.binary(),
        foldspaces=st.booleans(),
        wrapcol=st.integers(0, 10),
        adobe=st.booleans(),
    )
    def test_a85_encode_decode_round_trip(self, payload, foldspaces, wrapcol, adobe):
        x = base64.a85encode(
            payload, foldspaces=foldspaces, wrapcol=wrapcol, adobe=adobe
        )
        self.assertEqual(
            payload, base64.a85decode(x, foldspaces=foldspaces, adobe=adobe)
        )

    @given(payload=st.binary())
    def test_b85_encode_decode_round_trip(self, payload):
        x = base64.b85encode(payload)
        self.assertEqual(payload, base64.b85decode(x))

    # this is failing for payload = b'\x00'
    # expected to remove padding implicitly
    @unittest.expectedFailure
    @given(payload=st.binary())
    def test_b85_encode_with_padding_decode_round_trip(self, payload):
        x = base64.b85encode(payload, True)
        self.assertEqual(payload, base64.b85decode(x))


class TestBinASCII(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/binascii.html
    pass


class TestColorsys(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/colorsys.html
    pass


class TestPlistlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/plistlib.html
    pass


class TestQuodpri(unittest.TestCase):
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    def test_quodpri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)
