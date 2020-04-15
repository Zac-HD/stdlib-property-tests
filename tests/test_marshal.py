import marshal
import unittest

from hypothesis import given, strategies as st

simple_immutables = (
    st.integers()
    | st.booleans()
    | st.floats(allow_nan=False)  # NaNs compare unequal to themselves
    | st.complex_numbers(allow_nan=False)
    | st.just(None)
    | st.binary()
    | st.text()
)
composite_immutables = st.recursive(
    simple_immutables,
    lambda children: st.tuples(children) | st.frozensets(children, max_size=1),
    max_leaves=20,
)
marshallable_data = st.recursive(
    composite_immutables | st.sets(composite_immutables),
    lambda children: st.lists(children, max_size=20)
    | st.dictionaries(composite_immutables, children),
    max_leaves=20,
)


class TestMarshal(unittest.TestCase):
    @given(dt=marshallable_data)
    def test_roundtrip(self, dt):
        b = marshal.dumps(dt)
        dt2 = marshal.loads(b)  # noqa: S302  # using marshal is fine here
        self.assertEqual(dt, dt2)
