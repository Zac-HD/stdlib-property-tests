import unittest
from datetime import datetime, timezone

from hypothesis import given, strategies as st
from hypothesis.extra.dateutil import timezones as dateutil_timezones

TIME_ZONES_STRATEGY = st.one_of(
    st.sampled_from([None, timezone.utc]), dateutil_timezones()
)


class TestDatetime(unittest.TestCase):
    # Surrogate characters have been particularly problematic here in the past,
    # so we give them a boost by combining strategies pending an upstream
    # feature (https://github.com/HypothesisWorks/hypothesis/issues/1401)
    @given(
        dt=st.datetimes(timezones=TIME_ZONES_STRATEGY),
        sep=st.characters() | st.characters(whitelist_categories=["Cs"]),
    )
    def test_fromisoformat_auto(self, dt, sep):
        """Test isoformat with timespec="auto"."""
        dtstr = dt.isoformat(sep=sep, timespec="auto")
        dt_rt = datetime.fromisoformat(dtstr)
        self.assertEqual(dt, dt_rt)

    # TODO: https://docs.python.org/3/library/datetime.html
    # e.g. round-trip for datetime.isocalendar and other pairs
