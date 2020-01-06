import quopri
import unittest

from hypothesis import given, strategies as st


class TestQuodpri(unittest.TestCase):
    @given(payload=st.binary(), quotetabs=st.booleans(), header=st.booleans())
    def test_quodpri_encode_decode_round_trip(self, payload, quotetabs, header):
        encoded = quopri.encodestring(payload, quotetabs=quotetabs, header=header)
        decoded = quopri.decodestring(encoded, header=header)
        self.assertEqual(payload, decoded)
