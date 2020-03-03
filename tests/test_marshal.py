import marshal
import unittest

from hypothesis import example, given, strategies as st

simple_immutables = (
    st.integers()
    | st.booleans()
    | st.floats(allow_nan=False)
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


def marshallable_data(children):
    return st.lists(children, max_size=20) | st.dictionaries(
        composite_immutables, children
    )


marshallable_data = st.recursive(
    composite_immutables | st.sets(composite_immutables),
    marshallable_data,
    max_leaves=20,
)


class TestMarshal(unittest.TestCase):
    @given(dt=marshallable_data)
    def test_roundtrip(self, dt):
        b = marshal.dumps(dt)
        dt2 = marshal.loads(b)  # noqa: S302  # using marshal is fine here
        self.assertEqual(dt, dt2)
