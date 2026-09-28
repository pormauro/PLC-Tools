from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("pdw_analyze", HERE / "analyze.py")
pdw = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pdw
assert SPEC.loader is not None
SPEC.loader.exec_module(pdw)


def synthetic_template(path: Path) -> None:
    """Build a minimal synthetic PDW-like container for writer regression tests."""
    prefix = bytearray(pdw.RECORD_START)
    prefix[:len(pdw.MAGIC)] = pdw.MAGIC

    key = bytes((i * 37 + 11) & 0xFF for i in range(pdw.RECORD_SIZE))
    erased = bytes([0xFF]) * pdw.RECORD_SIZE
    encrypted_erased = pdw.xor_bytes(erased, key)

    active = bytearray(erased)
    active[0:2] = b"\x12\x34"
    active[0x1FE:0x200] = b"\x55\xAA"
    encrypted_active = pdw.xor_bytes(bytes(active), key)

    records = bytearray()
    records.extend(encrypted_active)
    for _ in range(pdw.PROGRAM_RECORD_COUNT - 1):
        records.extend(encrypted_erased)

    # Extra bytes are irrelevant to the current writer but emulate a container tail.
    path.write_bytes(bytes(prefix) + bytes(records) + b"\x00" * 256)


class MinimalWordTests(unittest.TestCase):
    def test_confirmed_words(self):
        self.assertEqual(pdw.minimal_rung_words(0, 0, False), (0x0040, 0x00C1, 0x0100))
        self.assertEqual(pdw.minimal_rung_words(1, 0, False), (0x0140, 0x00C1, 0x0200))
        self.assertEqual(pdw.minimal_rung_words(0, 1, False), (0x0040, 0x01C1, 0x0200))
        self.assertEqual(pdw.minimal_rung_words(0, 0, True), (0x0050, 0x00C1, 0x0110))
        self.assertEqual(pdw.minimal_rung_words(0, 1, True), (0x0050, 0x01C1, 0x0210))

    def test_checksum_formula_for_index_2_candidates(self):
        self.assertEqual(pdw.minimal_rung_words(2, 0, False), (0x0240, 0x00C1, 0x0300))
        self.assertEqual(pdw.minimal_rung_words(0, 2, False), (0x0040, 0x02C1, 0x0300))


class MinimalWriterTests(unittest.TestCase):
    def test_writer_round_trip_on_synthetic_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "template.pdw"
            output = Path(tmp) / "out.pdw"
            synthetic_template(template)

            result = pdw.write_minimal_rung(template, output, 1, 1, nc=True)
            self.assertEqual(result["contact_word"], "0x0150")
            self.assertEqual(result["output_word"], "0x01C1")
            self.assertEqual(result["checksum"], "0x0310")

            recovered = pdw.recover_program_candidate(output.read_bytes())
            words = pdw.words_le(recovered)
            self.assertEqual(
                words[pdw.PROGRAM_CODE_START_WORD:pdw.PROGRAM_CODE_START_WORD + 2],
                [0x0150, 0x01C1],
            )
            self.assertEqual(recovered[0xCC:0xCE], b"\x10\x03")

    def test_writer_refuses_unconfirmed_index_without_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "template.pdw"
            output = Path(tmp) / "out.pdw"
            synthetic_template(template)
            with self.assertRaises(ValueError):
                pdw.write_minimal_rung(template, output, 2, 0)

    def test_writer_never_overwrites_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "template.pdw"
            synthetic_template(template)
            before = template.read_bytes()
            with self.assertRaises(ValueError):
                pdw.write_minimal_rung(template, template, 0, 0)
            self.assertEqual(template.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
