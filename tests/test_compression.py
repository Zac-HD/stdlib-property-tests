import bz2
import gzip
import lzma
import unittest

from hypothesis import HealthCheck, given, settings, strategies as st

no_health_checks = settings(suppress_health_check=HealthCheck.all())


class TestBz2(unittest.TestCase):
    @given(payload=st.binary(), compresslevel=st.integers(1, 9))
    def test_bz2_round_trip(self, payload, compresslevel):
        result = bz2.decompress(bz2.compress(payload, compresslevel=compresslevel))
        self.assertEqual(payload, result)

    @given(payloads=st.lists(st.binary()), compresslevel=st.integers(1, 9))
    def test_bz2_incremental_compress_eq_oneshot(self, payloads, compresslevel):
        c = bz2.BZ2Compressor(compresslevel)
        compressed = b"".join(c.compress(p) for p in payloads) + c.flush()
        self.assertEqual(compressed, bz2.compress(b"".join(payloads), compresslevel))

    @no_health_checks
    @given(payload=st.binary(), compresslevel=st.integers(1, 9), data=st.data())
    def test_bz2_incremental_decompress_eq_oneshot(self, payload, compresslevel, data):
        compressed = bz2.compress(payload, compresslevel=compresslevel)
        d = bz2.BZ2Decompressor()

        output = []
        while compressed:
            chunksize = data.draw(st.integers(int(not d.needs_input), len(compressed)))
            max_length = data.draw(st.integers(0, len(payload)))
            output.append(d.decompress(compressed[:chunksize], max_length=max_length))
            self.assertLessEqual(len(output[-1]), max_length)
            compressed = compressed[chunksize:]
        if not d.eof:
            self.assertFalse(d.needs_input)
            output.append(d.decompress(b""))

        self.assertEqual(payload, b"".join(output))


class TestGzip(unittest.TestCase):
    @given(payload=st.binary(), compresslevel=st.integers(0, 9))
    def test_gzip_round_trip(self, payload, compresslevel):
        result = gzip.decompress(gzip.compress(payload, compresslevel=compresslevel))
        self.assertEqual(payload, result)


class TestLZMA(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/lzma.html
    @given(
        payload=st.binary(),
        check=st.sampled_from(
            ["CHECK_NONE", "CHECK_CRC32", "CHECK_CRC64", "CHECK_SHA256"]
        ),
        compresslevel=st.integers(0, 9),
    )
    def test_lzma_round_trip_format_xz(self, payload, check, compresslevel):
        result = lzma.decompress(
            lzma.compress(
                payload, format="FORMAT_XZ", check=check, preset=compresslevel
            )
        )
        self.assertEqual(payload, result)

    @given(
        payload=st.binary(),
        format=st.sampled_from(["FORMAT_ALONE", "FORMAT_RAW"]),
        compresslevel=st.integers(0, 9),
    )
    def test_lzma_round_trip_format_others(self, payload, format, compresslevel):
        result = lzma.decompress(
            lzma.compress(payload, format=format, preset=compresslevel)
        )
        self.assertEqual(payload, result)


class TestZlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/zlib.html
    pass
