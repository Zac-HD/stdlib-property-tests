import bz2
import gzip
import lzma
import unittest
import zlib

from hypothesis import HealthCheck, given, settings, strategies as st

no_health_checks = settings(suppress_health_check=HealthCheck.all())


@st.composite
def lzma_filters(draw):
    """Generating filters options"""
    op_filters = [
        lzma.FILTER_DELTA,
        lzma.FILTER_X86,
        lzma.FILTER_IA64,
        lzma.FILTER_ARM,
        lzma.FILTER_ARMTHUMB,
        lzma.FILTER_POWERPC,
        lzma.FILTER_SPARC,
    ]
    filter_ids = draw(st.lists(st.sampled_from(op_filters), max_size=3))
    filter_ids.append(lzma.FILTER_LZMA2)
    # create filters options
    filters = []
    for filter_ in filter_ids:
        lc = draw(st.integers(0, 4))
        lp = draw(st.integers(0, 4 - lc))
        mf = [lzma.MF_HC3, lzma.MF_HC4, lzma.MF_BT2, lzma.MF_BT3, lzma.MF_BT4]
        filters.append(
            {
                "id": filter_,
                "preset": draw(st.integers(0, 9)),
                "lc": lc,
                "lp": lp,
                "mode": draw(st.sampled_from([lzma.MODE_FAST, lzma.MODE_NORMAL])),
                "mf": draw(st.sampled_from(mf)),
                "depth": draw(st.integers(min_value=0)),
            }
        )
    return filters


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

    @unittest.skip(reason="LZMA filter strategy too general?")
    @given(payload=st.binary(), filters=lzma_filters())
    def test_lzma_round_trip_format_raw(self, payload, filters):
        # This test is a stub from our attempt to write a round-trip test with
        # custom LZMA filters (from the strategy above).  Ultimately we decided
        # to defer implementation to a future PR and merge what we had working.
        # TODO: work out what's happening here and fix it.
        compressed = lzma.compress(payload, format=lzma.FORMAT_RAW, filters=filters)
        self.assertEqual(payload, lzma.decompress(compressed))


class TestZlib(unittest.TestCase):
    @given(payload=st.binary(), value=st.just(0) | st.integers())
    def test_adler32(self, payload, value):
        checksum = zlib.adler32(payload, value)
        self.assertIsInstance(checksum, int)

    @given(
        payload_piece_1=st.binary(),
        payload_piece_2=st.binary(),
        value=st.just(0) | st.integers(),
    )
    def test_adler32_two_part(self, payload_piece_1, payload_piece_2, value):
        combined_checksum = zlib.adler32(payload_piece_1 + payload_piece_2, value)
        checksum_part1 = zlib.adler32(payload_piece_1, value)
        checksum = zlib.adler32(payload_piece_2, checksum_part1)
        self.assertEqual(combined_checksum, checksum)

    @given(payload=st.binary(), value=st.just(0) | st.integers())
    def test_crc32(self, payload, value):
        crc = zlib.crc32(payload, value)
        self.assertIsInstance(crc, int)

    @given(
        payload_piece_1=st.binary(),
        payload_piece_2=st.binary(),
        value=st.just(0) | st.integers(),
    )
    def test_crc32_two_part(self, payload_piece_1, payload_piece_2, value):
        combined_crc = zlib.crc32(payload_piece_1 + payload_piece_2, value)
        crc_part1 = zlib.crc32(payload_piece_1, value)
        crc = zlib.crc32(payload_piece_2, crc_part1)
        self.assertEqual(combined_crc, crc)

    @given(
        payload=st.binary(), level=st.just(-1) | st.integers(0, 9),
    )
    def test_compress_decompress_round_trip(self, payload, level):
        x = zlib.compress(payload, level=level)
        self.assertEqual(payload, zlib.decompress(x))
