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
            [lzma.CHECK_NONE, lzma.CHECK_CRC32, lzma.CHECK_CRC64, lzma.CHECK_SHA256]
        ),
        compresslevel=st.integers(0, 9),
    )
    def test_lzma_round_trip_format_xz(self, payload, check, compresslevel):
        result = lzma.decompress(
            lzma.compress(
                payload, format=lzma.FORMAT_XZ, check=check, preset=compresslevel
            )
        )
        self.assertEqual(payload, result)

    @given(
        payload=st.binary(), compresslevel=st.integers(0, 9),
    )
    def test_lzma_round_trip_format_alone(self, payload, compresslevel):
        result = lzma.decompress(
            lzma.compress(payload, format=lzma.FORMAT_ALONE, preset=compresslevel)
        )
        self.assertEqual(payload, result)

    @st.composite
    def filters(self, draw):
        filter_ids = draw(
            st.lists(
                st.sampled_from(
                    [
                        lzma.FILTER_DELTA,
                        lzma.FILTER_X86,
                        lzma.FILTER_IA64,
                        lzma.FILTER_ARM,
                        lzma.FILTER_ARMTHUMB,
                        lzma.FILTER_POWERPC,
                        lzma.FILTER_SPARC,
                    ]
                ),
                max_size=3,
            )
        )
        filter_ids.append(lzma.FILTER_LZMA2)
        # create filters options
        filters = []
        for filter in filter_ids:
            lc = draw(st.integers(0, 4))
            lp = draw(st.integers(0, 4 - lc))
            filters.append(
                {
                    "id": filter,
                    "preset": data.draw(st.integers(0, 9)),
                    "dict_size": data.draw(st.integers(4000, 1.875e8)),
                    "lc": lc,
                    "lp": lp,
                    "mode": data.draw(
                        st.sampled_from([lzma.MODE_FAST, lzma.MODE_NORMAL])
                    ),
                    "mf": data.draw(
                        st.sampled_from(
                            [
                                lzma.MF_HC3,
                                lzma.MF_HC4,
                                lzma.MF_BT2,
                                lzma.MF_BT3,
                                lzma.MF_BT4,
                            ]
                        )
                    ),
                    "depth": data.draw(st.integers(min_value=0)),
                }
            )
        return filters

    @given(payload=st.binary(), data=st.data())
    def test_lzma_round_trip_format_raw(self, payload, data):
        # create the list of filter ids
        filters = self.filters(data.draw)
        result = lzma.decompress(
            lzma.compress(payload, format=lzma.FORMAT_RAW, filters=filters)
        )
        self.assertEqual(payload, result)


class TestZlib(unittest.TestCase):
    # TODO: https://docs.python.org/3/library/zlib.html
    pass
