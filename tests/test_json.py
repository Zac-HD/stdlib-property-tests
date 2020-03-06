import json
import unittest

from hypothesis import given, strategies as st

jsondata = st.recursive(
    st.none()
    | st.booleans()
    | st.floats(allow_nan=False)  # NaNs compare unequal to themselves
    | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
)


class TestJson(unittest.TestCase):
    @given(jsondata)
    def test_roundtrip(self, d):
        self.assertEqual(json.loads(json.dumps(d)), d)
