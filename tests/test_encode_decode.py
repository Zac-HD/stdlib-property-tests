import base64
import quopri
import unittest

from hypothesis import given, strategies as st


# function which adds padding, till len(payload) is a multiple of 4
def add_padding(payload):
    padding = b"\0" * ((-len(payload)) % 4)
    payload = payload + padding
    return payload


class TestBase64(unittest.TestCase):
    # @given(
    #     payload=st.binary(),
    #     altchars=(st.none() | st.binary(min_size=2, max_size=2)),
    #     validate=st.booleans(),
    # )
    @given(
        payload=st.binary(),
        altchars=(st.none() | st.just(b"_-")),
        validate=st.booleans(),
    )
    def test_b64_encode_decode_round_trip(self, payload, altchars, validate):
        x = base64.b64encode(payload, altchars=altchars)
        self.assertEqual(
            payload, base64.b64decode(x, altchars=altchars, validate=validate)
        )

    @given(payload=st.binary())
    def test_standard_b64_encode_decode_round_trip(self, payload):
        x = base64.standard_b64encode(payload)
        self.assertEqual(payload, base64.standard_b64decode(x))

    @given(payload=st.binary())
    def test_urlsafe_b64_encode_decode_round_trip(self, payload):
        x = base64.urlsafe_b64encode(payload)
        self.assertEqual(payload, base64.urlsafe_b64decode(x))

    @given(
        payload=st.binary(),
        casefold=st.booleans(),
        map01=(st.none() | st.binary(min_size=1, max_size=1)),
    )
    def test_b32_encode_decode_round_trip(self, payload, casefold, map01):
        x = base64.b32encode(payload)
        self.assertEqual(payload, base64.b32decode(x, casefold=casefold, map01=map01))

    @given(payload=st.binary(), casefold=st.booleans())
    def test_b16_encode_decode_round_trip(self, payload, casefold):
        x = base64.b16encode(payload)
        self.assertEqual(payload, base64.b16decode(x, casefold=casefold))

    @given(
        payload=st.binary(),
        foldspaces=st.booleans(),
        wrapcol=(st.just(0) | st.integers(0, 1000)),
        pad=st.booleans(),
        adobe=st.booleans(),
    )
    def test_a85_encode_decode_round_trip(
        self, payload, foldspaces, wrapcol, pad, adobe
    ):
        x = base64.a85encode(
            payload, foldspaces=foldspaces, wrapcol=wrapcol, pad=pad, adobe=adobe
        )
        # adding padding manually to payload, when pad is True and len(payload)%4!=0
        if pad:
            payload = add_padding(payload)
        self.assertEqual(
            payload, base64.a85decode(x, foldspaces=foldspaces, adobe=adobe)
        )

    @given(payload=st.binary(), pad=st.booleans())
    def test_b85_encode_decode_round_trip(self, payload, pad):
        x = base64.b85encode(payload, pad=pad)
        # adding padding manually to payload, when pad is True and len(payload)%4!=0
        if pad:
            payload = add_padding(payload)
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
