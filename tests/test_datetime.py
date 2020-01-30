import unittest
from datetime import datetime, timezone

from hypothesis import given, settings, strategies as st
from hypothesis.extra.dateutil import timezones as dateutil_timezones

TIME_ZONES_STRATEGY = st.one_of(
    st.sampled_from([None, timezone.utc]), dateutil_timezones()
)


class TestDatetime(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/datetime.html

    # The search space here is large and as of January 2020 the sampling
    # functions for characters() and datetimes() are not biased towards
    # "interesting" examples, so it's worth throwing some extra cycles at this.
    @settings(max_examples=2500)
    @given(dt=st.datetimes(timezones=TIME_ZONES_STRATEGY), sep=st.characters())
    def test_fromisoformat_auto(self, dt, sep):
        """Test isoformat with timespec="auto"."""
        dtstr = dt.isoformat(sep=sep, timespec="auto")
        dt_rt = datetime.fromisoformat(dtstr)

        self.assertEqual(dt, dt_rt)
