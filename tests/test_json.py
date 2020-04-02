import json
import unittest

from hypothesis import given, strategies as st

INDENTS = st.one_of(
    st.none(), st.integers(-2, 100), st.from_regex("[ \t\n\r]*", fullmatch=True)
)


def jsondata(all_finite=False):
    # The JSON spec does not allow non-finite numbers; so Python's json module has
    # an option to reject such numbers.  We therefore make it easy to avoid them.
    if all_finite:
        floats = st.floats(allow_infinity=False, allow_nan=False)
    else:
        floats = st.floats()
    return st.recursive(
        st.one_of(st.none(), st.booleans(), floats, st.text()),
        lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    )


class TestJson(unittest.TestCase):
    @given(
        allow_nan=st.booleans(),
        ensure_ascii=st.booleans(),
        indent=INDENTS,
        obj=jsondata(all_finite=True),
        sort_keys=st.booleans(),
    )
    def test_roundtrip_dumps_loads(
        self, allow_nan, ensure_ascii, indent, obj, sort_keys
    ):
        # For any self-equal JSON object, we can deserialise it to an equal object.
        # (regardless of how we vary string encoding, indentation, and sorting)
        self.assertEqual(obj, obj)
        deserialised = json.loads(
            json.dumps(
                obj,
                allow_nan=allow_nan,
                ensure_ascii=ensure_ascii,
                indent=indent,
                sort_keys=sort_keys,
            )
        )
        self.assertEqual(obj, deserialised)

    @given(
        ensure_ascii=st.booleans(),
        indent=INDENTS,
        obj=jsondata(),
        sort_keys=st.booleans(),
    )
    def test_roundtrip_dumps_loads_dumps(self, ensure_ascii, indent, obj, sort_keys):
        # For any json object, even those with non-finite numbers and with all the
        # variations as above, object -> string -> object -> string should produce
        # identical strings.
        as_str = json.dumps(
            obj, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys
        )
        deserialised = json.loads(as_str)
        as_str2 = json.dumps(
            deserialised, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys
        )
        self.assertEqual(as_str, as_str2)
