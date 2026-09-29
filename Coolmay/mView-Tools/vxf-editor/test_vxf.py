from __future__ import annotations

import struct
import sys
from pathlib import Path
import unittest
import zlib

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from vxf_core import (  # noqa: E402
    MAGIC,
    PROJECT_BLOCK_MARKER_BYTES,
    SIGNATURE,
    VXFError,
    build_project_block,
    crc16_modbus,
    mutate_project_block,
    parse_vxf,
    validate_vxf,
)


def synthetic_vxf(body: bytes, suffix: bytes = b"TAIL") -> bytes:
    payload = (
        SIGNATURE
        + b"\x00" * 32
        + b"PREFIX"
        + build_project_block(body)
        + suffix
    )
    return MAGIC + zlib.compress(payload, level=6)


class TestVXFOuterContainer(unittest.TestCase):
    def test_variable_length_edit_repairs_size_crc_and_preserves_suffix(self):
        raw = synthetic_vxf(b"A" * 100, suffix=b"UNCHANGED-SUFFIX")
        before = parse_vxf(raw)
        before_size = before.project_block.stored_size

        modified = mutate_project_block(raw, lambda body: body + b"B" * 400)
        after = parse_vxf(modified)

        self.assertEqual(after.project_block.stored_size, before_size + 400)
        self.assertEqual(after.suffix, b"UNCHANGED-SUFFIX")
        self.assertEqual(after.project_body[-400:], b"B" * 400)

        content = after.payload[
            after.project_block.content_offset:after.project_block.content_end
        ]
        stored_crc = struct.unpack_from("<H", content, len(content) - 2)[0]
        self.assertEqual(stored_crc, crc16_modbus(content[:-2]))

    def test_stale_outer_crc_is_rejected(self):
        raw = synthetic_vxf(b"A" * 100)
        payload = bytearray(zlib.decompress(raw[len(MAGIC):]))
        doc = parse_vxf(raw)

        # Simulate the historical bug: change data inside the project block
        # without rebuilding its outer CRC.
        payload[doc.project_block.content_offset] ^= 0x01
        broken = MAGIC + zlib.compress(bytes(payload), level=6)

        with self.assertRaisesRegex(VXFError, "CRC mismatch"):
            validate_vxf(broken)

    def test_stale_outer_size_from_variable_length_splice_is_rejected(self):
        raw = synthetic_vxf(b"A" * 100, suffix=b"NEXT-BLOCK")
        payload = zlib.decompress(raw[len(MAGIC):])
        doc = parse_vxf(raw)

        # Simulate inserting bytes into the block while leaving its stored size
        # untouched. The old CRC is no longer at the location implied by size.
        insertion = b"X" * 400
        bad_payload = (
            payload[:doc.project_block.body_end]
            + insertion
            + payload[doc.project_block.body_end:]
        )
        broken = MAGIC + zlib.compress(bad_payload, level=6)

        with self.assertRaises(VXFError):
            validate_vxf(broken)

    def test_noop_mutation_keeps_payload_semantics(self):
        raw = synthetic_vxf(b"ABC" * 50)
        modified = mutate_project_block(raw, lambda body: body)
        self.assertEqual(
            zlib.decompress(modified[len(MAGIC):]),
            zlib.decompress(raw[len(MAGIC):]),
        )


if __name__ == "__main__":
    unittest.main()
