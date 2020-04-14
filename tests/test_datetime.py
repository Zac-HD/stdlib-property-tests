import unittest
from datetime import date, datetime, time, timezone

from hypothesis import given, strategies as st
from hypothesis.extra.dateutil import timezones as dateutil_timezones

TIME_ZONES_STRATEGY = st.one_of(
    st.sampled_from([None, timezone.utc]), dateutil_timezones()
)


class TestDatetime(unittest.TestCase):
    # Surrogate characters have been particularly problematic here in the past,
    # so we give them a boost by combining strategies pending an upstream
    # feature (https://github.com/HypothesisWorks/hypothesis/issues/1401)
    @unittest.skipIf(not hasattr(datetime, "fromisoformat"), reason="new in 3.7")
    @given(
        dt=st.datetimes(timezones=TIME_ZONES_STRATEGY),
        sep=st.characters() | st.characters(whitelist_categories=["Cs"]),
    )
    def test_fromisoformat_auto(self, dt, sep):
        """Test isoformat with timespec="auto"."""
        dtstr = dt.isoformat(sep=sep, timespec="auto")
        dt_rt = datetime.fromisoformat(dtstr)
        self.assertEqual(dt, dt_rt)

    @unittest.skipIf(not hasattr(datetime, "fromisocalendar"), reason="new in 3.8")
    @given(dt=st.datetimes())
    def test_fromisocalendar_date_datetime(self, dt):
        isocalendar = dt.isocalendar()
        dt_rt = datetime.fromisocalendar(*isocalendar)

        # Only the date portion of the datetime survives a round trip.
        d = dt.date()
        d_rt = dt_rt.date()

        self.assertEqual(d, d_rt)

        # .fromisocalendar() should always return a datetime at midnight
        t = time(0)
        t_rt = dt_rt.time()

        self.assertEqual(t, t_rt)

    # TODO: https://docs.python.org/3/library/datetime.html
    # e.g. round-trip for other serialization / deserialization pairs.
    # Use exhaustive testing rather than Hypothesis where possible!


class TestDate(unittest.TestCase):
    @unittest.skipIf(not hasattr(datetime, "fromisocalendar"), reason="new in 3.8")
    @given(d=st.dates())
    def test_fromisocalendar(self, d):
        isocalendar = d.isocalendar()
        d_rt = date.fromisocalendar(*isocalendar)

        self.assertEqual(d, d_rt)
