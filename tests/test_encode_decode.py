import base64
import binascii
import binhex
import colorsys
import io
import os
import platform
import quopri
import string
import sys
import unittest
import uu
from tempfile import TemporaryDirectory

from hypothesis import example, given, strategies as st, target

IS_PYPY = platform.python_implementation() == "PyPy"


def add_padding(payload):
    """Add the expected padding for test_b85_encode_decode_round_trip."""
    if len(payload) % 4 != 0:
        padding = b"\0" * ((-len(payload)) % 4)
        payload = payload + padding
    return payload


@st.composite
def altchars(draw):
    """Generate 'altchars' for base64 encoding.

    Via https://docs.python.org/3/library/base64.html#base64.b64encode :
    "Optional altchars must be a bytes-like object of at least length 2
    (additional characters are ignored) which specifies an alternative
    alphabet for the + and / characters."
    """
    reserved_chars = (string.digits + string.ascii_letters + "=").encode("ascii")
    allowed_chars = st.sampled_from([n for n in range(256) if n not in reserved_chars])
    return bytes(draw(st.lists(allowed_chars, min_size=2, max_size=2, unique=True)))


class TestBase64(unittest.TestCase):
    @given(
        payload=st.binary(),
        altchars=st.none() | st.just(b"_-") | altchars(),
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
    @given(payload=st.binary(), backtick=st.booleans())
    def test_b2a_uu_a2b_uu_round_trip(self, payload, backtick):
        if sys.version_info[:2] >= (3, 7):
            x = binascii.b2a_uu(payload, backtick=backtick)
        else:
            x = binascii.b2a_uu(payload)
        self.assertEqual(payload, binascii.a2b_uu(x))

    @given(payload=st.binary(), newline=st.booleans())
    def test_b2a_base64_a2b_base64_round_trip(self, payload, newline):
        x = binascii.b2a_base64(payload, newline=newline)
        self.assertEqual(payload, binascii.a2b_base64(x))

    @given(
        payload=st.binary(),
        quotetabs=st.booleans(),
        istext=st.booleans(),
        header=st.booleans(),
    )
    def test_b2a_qp_a2b_qp_round_trip(self, payload, quotetabs, istext, header):
        x = binascii.b2a_qp(payload, quotetabs=quotetabs, istext=istext, header=header)
        self.assertEqual(payload, binascii.a2b_qp(x, header=header))

    @given(payload=st.binary())
    def test_rlecode_hqx_rledecode_hqx_round_trip(self, payload):
        x = binascii.rlecode_hqx(payload)
        self.assertEqual(payload, binascii.rledecode_hqx(x))

    @given(payload=st.binary())
    def test_b2a_hqx_a2b_hqx_round_trip(self, payload):
        # assuming len(payload) as 3, since it throws exception: binascii.Incomplete, when length is not a multiple of 3
        if len(payload) % 3:
            with self.assertRaises(binascii.Incomplete):
                x = binascii.b2a_hqx(payload)
                binascii.a2b_hqx(x)
            payload += b"\x00" * (-len(payload) % 3)
        x = binascii.b2a_hqx(payload)
        res, _ = binascii.a2b_hqx(x)
        self.assertEqual(payload, res)

    @unittest.skipIf(IS_PYPY, "we found an overflow bug")
    @given(payload=st.binary(), value=st.just(0) | st.integers())
    @example(payload=b"", value=2 ** 63)
    def test_crc_hqx(self, payload, value):
        crc = binascii.crc_hqx(payload, value)
        self.assertIsInstance(crc, int)

    @unittest.skipIf(IS_PYPY, "we found an overflow bug")
    @given(
        payload_piece_1=st.binary(),
        payload_piece_2=st.binary(),
        value=st.just(0) | st.integers(),
    )
    def test_crc_hqx_two_pieces(self, payload_piece_1, payload_piece_2, value):
        combined_crc = binascii.crc_hqx(payload_piece_1 + payload_piece_2, value)
        crc_part1 = binascii.crc_hqx(payload_piece_1, value)
        crc = binascii.crc_hqx(payload_piece_2, crc_part1)
        self.assertEqual(combined_crc, crc)

    @given(payload=st.binary(), value=st.just(0) | st.integers())
    def test_crc32(self, payload, value):
        crc = binascii.crc32(payload, value)
        self.assertIsInstance(crc, int)

    @given(
        payload_piece_1=st.binary(),
        payload_piece_2=st.binary(),
        value=st.just(0) | st.integers(),
    )
    def test_crc32_two_part(self, payload_piece_1, payload_piece_2, value):
        combined_crc = binascii.crc32(payload_piece_1 + payload_piece_2, value)
        crc_part1 = binascii.crc32(payload_piece_1, value)
        crc = binascii.crc32(payload_piece_2, crc_part1)
        self.assertEqual(combined_crc, crc)

    @given(payload=st.binary())
    def test_b2a_hex_a2b_hex_round_trip(self, payload):
        x = binascii.b2a_hex(payload)
        self.assertEqual(payload, binascii.a2b_hex(x))

    @given(payload=st.binary())
    def test_hexlify_unhexlify_round_trip(self, payload):
        x = binascii.hexlify(payload)
        self.assertEqual(payload, binascii.unhexlify(x))


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

    @unittest.expectedFailure
    @given(r=st.floats(0, 1), g=st.floats(0, 1), b=st.floats(0, 1))
    @example(r=0.5714285714285715, g=0.0, b=2.2204460492503136e-16)
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


class TestQuopri(unittest.TestCase):
    @unittest.expectedFailure
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    @example(payload=b"\n\r\n", quotetabs=False, header=False)
    @example(payload=b"\r\n\n", quotetabs=False, header=False)
    def test_quopri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)


class TestBinhex(unittest.TestCase):
    @given(payload=st.binary())
    def test_binhex_encode_decode(self, payload):
        with TemporaryDirectory() as dirname:
            input_file_name = os.path.join(dirname, "input.txt")
            encoded_file_name = os.path.join(dirname, "encoded.hqx")
            decoded_file_name = os.path.join(dirname, "decoded.txt")
            with open(input_file_name, "wb") as input_file:
                input_file.write(payload)
            binhex.binhex(input_file_name, encoded_file_name)
            binhex.hexbin(encoded_file_name, decoded_file_name)
            with open(decoded_file_name, "rb") as decoded_file:
                decoded_payload = decoded_file.read()
            assert payload == decoded_payload


class TestUu(unittest.TestCase):
    @given(
        payload=st.binary(),
        name=st.none() | st.just("-") | st.just("0o666"),
        quiet=st.binary(),
    )
    def test_uu_encode_decode(self, payload, name, quiet):
        input_file = io.BytesIO(payload)
        encoded_file = io.BytesIO()
        decoded_file = io.BytesIO()
        uu.encode(input_file, encoded_file, name=name)
        encoded_file.seek(0)
        uu.decode(encoded_file, out_file=decoded_file, quiet=quiet)
        decoded_payload = decoded_file.getvalue()
        assert payload == decoded_payload
