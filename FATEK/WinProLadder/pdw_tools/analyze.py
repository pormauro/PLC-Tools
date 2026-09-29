#!/usr/bin/env python3
"""Read-only structural analysis for FATEK WinProLadder .pdw projects.

The tool never mutates a source PDW. Experimental recovery commands may write
derived binary data to a separate output path when explicitly requested.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

MAGIC = b"Fatek WinProladder, File Format 1"
RECORD_START = 0x120
RECORD_SIZE = 1280
RECORD_SCAN_END = 0x10228
HEADER_STABLE_END = 290
KNOWN_STABLE_TAIL = 66130

# Strong empirical candidate for the FBs program-memory image:
# 32 records * 1280 bytes = 40960 bytes = 20480 16-bit words = 20K words.
PROGRAM_RECORD_COUNT = 32
PROGRAM_BYTES = PROGRAM_RECORD_COUNT * RECORD_SIZE
PROGRAM_WORDS = PROGRAM_BYTES // 2
PROGRAM_REFERENCE_RECORD_INDEX = 1
ERASED_BYTE = 0xFF
PROGRAM_CODE_START_WORD = 257

# Low-byte opcodes established by controlled fixtures.
# Device index is stored in the high byte for the observed X0/X1 and Y0/Y1 cases.
KNOWN_LOW_OPCODES = {
    0x40: ("ORG", "X", "confirmed for X0/X1"),
    0x50: ("ORG NOT", "X", "confirmed for X0; index layout inferred"),
    0xC1: ("OUT", "Y", "confirmed for Y0/Y1"),
}

PERIOD_CANDIDATES = (
    32, 64, 128, 144, 160, 192, 256, 320, 384, 512, 640, 768,
    1024, 1280, 1536, 2048, 2560, 3840, 4096,
)


@dataclass(frozen=True)
class FileReport:
    path: str
    size: int
    sha256: str
    magic_ok: bool
    header_ascii: list[dict]
    first_long_zero_run: int | None
    entropy_0_290: float
    entropy_290_66130: float | None
    entropy_66130_eof: float | None
    candidate_periods: list[dict]
    repeated_1280_structure: dict


def shannon_entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    counts = collections.Counter(buf)
    n = len(buf)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def ascii_strings(buf: bytes, minimum: int = 4) -> list[tuple[int, str]]:
    pattern = rb"[\x20-\x7e]{%d,}" % minimum
    return [
        (m.start(), m.group().decode("ascii", errors="replace"))
        for m in re.finditer(pattern, buf)
    ]


def first_zero_run(buf: bytes, minimum: int = 1024) -> int | None:
    match = re.search(rb"\x00{%d,}" % minimum, buf)
    return match.start() if match else None


def xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) != len(right):
        raise ValueError("xor_bytes requires equal-sized buffers")
    return bytes(a ^ b for a, b in zip(left, right))


def periodic_match_ratio(buf: bytes, period: int, start: int, end: int) -> float:
    end = min(end, len(buf))
    usable = end - start - period
    if usable <= 0:
        return 0.0
    left = memoryview(buf)[start:start + usable]
    right = memoryview(buf)[start + period:start + period + usable]
    return sum(a == b for a, b in zip(left, right)) / usable


def scan_candidate_periods(
    buf: bytes,
    start: int = RECORD_START,
    end: int = 0x10220,
    periods: Sequence[int] = PERIOD_CANDIDATES,
) -> list[dict]:
    rows = [
        {"period": p, "ratio": periodic_match_ratio(buf, p, start, end)}
        for p in periods
    ]
    return sorted(rows, key=lambda row: row["ratio"], reverse=True)


def split_records(
    buf: bytes,
    start: int = RECORD_START,
    end: int = RECORD_SCAN_END,
    record_size: int = RECORD_SIZE,
) -> list[bytes]:
    end = min(end, len(buf))
    return [
        buf[i:min(i + record_size, end)]
        for i in range(start, end, record_size)
    ]


def summarize_repeated_chunks(buf: bytes) -> dict:
    chunks = split_records(buf)
    hashes = [hashlib.sha256(chunk).hexdigest() for chunk in chunks]
    labels_by_hash: dict[str, str] = {}
    labels: list[str] = []
    for digest in hashes:
        if digest not in labels_by_hash:
            labels_by_hash[digest] = chr(ord("A") + len(labels_by_hash))
        labels.append(labels_by_hash[digest])
    return {
        "start": RECORD_START,
        "end_exclusive": min(RECORD_SCAN_END, len(buf)),
        "record_size": RECORD_SIZE,
        "chunk_count": len(chunks),
        "pattern": "".join(labels),
        "counts": dict(collections.Counter(labels)),
        "top_hashes": collections.Counter(hashes).most_common(8),
    }


def contiguous_runs(indices: Iterable[int]) -> list[dict]:
    values = list(indices)
    if not values:
        return []
    out = []
    start = prev = values[0]
    for value in values[1:]:
        if value != prev + 1:
            out.append(
                {"start": start, "end": prev, "length": prev - start + 1}
            )
            start = value
        prev = value
    out.append({"start": start, "end": prev, "length": prev - start + 1})
    return out


def nonzero_runs(buf: bytes) -> list[dict]:
    rows = contiguous_runs(i for i, value in enumerate(buf) if value)
    for row in rows:
        row["xor_hex"] = buf[row["start"]:row["end"] + 1].hex()
    return rows


def xor_period_is_exact(buf: bytes, period: int) -> bool:
    if period <= 0 or len(buf) <= period:
        return False
    return all(buf[i] == buf[i % period] for i in range(len(buf)))


def cancel_periodic_transform(
    data: bytes,
    active_record_index: int,
    reference_record_index: int,
) -> bytes:
    """Empirically cancel a same-phase XOR layer using an aligned reference."""
    records = split_records(data)
    try:
        active = records[active_record_index]
        reference = records[reference_record_index]
    except IndexError as exc:
        raise ValueError("record index outside scanned PDW record area") from exc
    if len(active) != len(reference):
        raise ValueError("records must have equal size")
    return xor_bytes(active, reference)


def derive_program_xor_key(
    data: bytes,
    reference_record_index: int = PROGRAM_REFERENCE_RECORD_INDEX,
    erased_byte: int = ERASED_BYTE,
) -> bytes:
    """Derive the repeating transform from an assumed 0xFF erased record."""
    if not 0 <= erased_byte <= 0xFF:
        raise ValueError("erased_byte must be in range 0..255")
    records = split_records(data)
    if len(records) < PROGRAM_RECORD_COUNT:
        raise ValueError("PDW is too short for the 32-record candidate program area")
    reference = records[reference_record_index]
    if len(reference) != RECORD_SIZE:
        raise ValueError("reference record is incomplete")
    return bytes(value ^ erased_byte for value in reference)


def recover_program_candidate(data: bytes) -> bytes:
    """Recover the 20K-word candidate program region under the 0xFF premise."""
    records = split_records(data)
    if len(records) < PROGRAM_RECORD_COUNT:
        raise ValueError("PDW is too short for the candidate program area")
    key = derive_program_xor_key(data)
    recovered = bytearray()
    for record in records[:PROGRAM_RECORD_COUNT]:
        if len(record) != RECORD_SIZE:
            raise ValueError("incomplete record in candidate program area")
        recovered.extend(xor_bytes(record, key))
    if len(recovered) != PROGRAM_BYTES:
        raise AssertionError("candidate program recovery produced wrong size")
    return bytes(recovered)


def words_le(buf: bytes) -> list[int]:
    usable = len(buf) - (len(buf) % 2)
    if not usable:
        return []
    return list(struct.unpack("<" + "H" * (usable // 2), buf[:usable]))


def decode_sequential_word(word: int) -> dict | None:
    opcode = word & 0xFF
    index = (word >> 8) & 0xFF
    known = KNOWN_LOW_OPCODES.get(opcode)
    if known is None:
        return None
    mnemonic, family, evidence = known
    return {
        "word": word,
        "hex_word": f"0x{word:04X}",
        "opcode_low": opcode,
        "device_index": index,
        "mnemonic": mnemonic,
        "operand": f"{family}{index}",
        "text": f"{mnemonic} {family}{index}",
        "evidence": evidence,
    }


def semantic_program_sha256(recovered: bytes) -> str:
    """Fingerprint program content while ignoring the 2-byte save-variant field."""
    normalized = bytearray(recovered)
    if len(normalized) >= 2:
        normalized[0:2] = b"\x00\x00"
    return hashlib.sha256(normalized).hexdigest()


def minimal_rung_words(x_index: int, y_index: int, nc: bool = False) -> tuple[int, int, int]:
    """Encode the confirmed minimal ORG/ORG NOT + OUT family."""
    if not 0 <= x_index <= 0xFF:
        raise ValueError("x_index must be in range 0..255")
    if not 0 <= y_index <= 0xFF:
        raise ValueError("y_index must be in range 0..255")
    contact = (x_index << 8) | (0x50 if nc else 0x40)
    output = (y_index << 8) | 0xC1
    checksum = (contact + output - 1) & 0xFFFF
    return contact, output, checksum


def validate_minimal_template(recovered: bytes) -> None:
    """Refuse templates whose program area is more complex than our proven family."""
    words = words_le(recovered)
    if len(words) != PROGRAM_WORDS:
        raise ValueError("unexpected recovered program size")
    if recovered[0x1FE:0x200] != b"\x55\xAA":
        raise ValueError("expected 55 AA program marker not found")
    tail = words[PROGRAM_CODE_START_WORD:]
    non_erased = [i for i, word in enumerate(tail) if word != 0xFFFF]
    if not non_erased:
        return
    if non_erased != [0, 1]:
        raise ValueError(
            "template contains more than one proven 2-word minimal rung; refusing write"
        )


def patch_minimal_rung_plaintext(
    record: bytearray,
    x_index: int,
    y_index: int,
    nc: bool = False,
) -> tuple[int, int, int]:
    """Patch one recovered active record using fields proven by the controlled corpus."""
    if len(record) != RECORD_SIZE:
        raise ValueError("active record must be exactly 1280 bytes")
    contact, output, checksum = minimal_rung_words(x_index, y_index, nc)

    # Proven constant/control fields for the current 2-word rung family.
    record[0xCA] = 0x2B
    record[0xCB] = 0xFF
    record[0xCC] = checksum & 0xFF
    record[0xCD] = (checksum >> 8) & 0xFF
    record[0x103] = 0x00
    record[0x108] = 0x02
    record[0x10A] = 0xFD
    record[0x10E] = 0x06
    record[0x110] = 0x06

    record[0x202] = contact & 0xFF
    record[0x203] = (contact >> 8) & 0xFF
    record[0x204] = output & 0xFF
    record[0x205] = (output >> 8) & 0xFF
    return contact, output, checksum


def write_minimal_rung(
    template: Path,
    output_path: Path,
    x_index: int,
    y_index: int,
    nc: bool = False,
    force: bool = False,
    allow_unconfirmed_index: bool = False,
) -> dict:
    """Create a derived PDW using a validated empty/minimal template."""
    if template.resolve() == output_path.resolve():
        raise ValueError("output must be different from template")
    if output_path.exists() and not force:
        raise FileExistsError(f"output already exists: {output_path}")
    if (x_index > 2 or y_index > 2) and not allow_unconfirmed_index:
        raise ValueError(
            "indices above 2 are not fixture-confirmed yet; pass "
            "--allow-unconfirmed-index for an explicit experiment"
        )

    data = bytearray(template.read_bytes())
    if not data.startswith(MAGIC):
        raise ValueError("template is not a recognized WinProLadder PDW")

    recovered = recover_program_candidate(bytes(data))
    validate_minimal_template(recovered)

    records = split_records(bytes(data))
    key = derive_program_xor_key(bytes(data))
    active_plain = bytearray(xor_bytes(records[0], key))
    contact, output, checksum = patch_minimal_rung_plaintext(
        active_plain, x_index, y_index, nc
    )
    encrypted = xor_bytes(bytes(active_plain), key)
    data[RECORD_START:RECORD_START + RECORD_SIZE] = encrypted

    output_path.write_bytes(data)
    verify = recover_program_candidate(bytes(data))
    verify_words = words_le(verify)
    if verify_words[PROGRAM_CODE_START_WORD:PROGRAM_CODE_START_WORD + 2] != [
        contact, output
    ]:
        output_path.unlink(missing_ok=True)
        raise AssertionError("post-write verification failed")

    return {
        "template": str(template),
        "output": str(output_path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "contact_word": f"0x{contact:04X}",
        "output_word": f"0x{output:04X}",
        "checksum": f"0x{checksum:04X}",
        "ladder": f"{'ORG NOT' if nc else 'ORG'} X{x_index} ; OUT Y{y_index}",
        "scope": (
            "fixture-confirmed" if x_index <= 2 and y_index <= 2
            else "experimental-unconfirmed-index"
        ),
    }


def summarize_program_metadata(recovered: bytes) -> dict:
    """Summarize control fields now tied to the recovered code stream."""
    words = words_le(recovered)
    count = int.from_bytes(recovered[0x108:0x10A], "little")
    code_start = PROGRAM_CODE_START_WORD
    code = words[code_start:code_start + count]
    checksum = int.from_bytes(recovered[0xCC:0xCE], "little")
    complement = int.from_bytes(recovered[0x10A:0x10C], "little")
    end_a = int.from_bytes(recovered[0x10E:0x110], "little")
    end_b = int.from_bytes(recovered[0x110:0x112], "little")
    expected_checksum = (sum(code) - 1) & 0xFFFF
    expected_complement = (0x4EFF - count) & 0xFFFF
    expected_end = 0x202 + 2 * count
    expected_ca_low = (0x23 + 4 * count) & 0xFF
    return {
        "code_word_count": count,
        "code_word_count_field_offset": "0x108",
        "code_words_hex": [f"0x{word:04X}" for word in code],
        "checksum_field_offset": "0x0CC",
        "checksum": f"0x{checksum:04X}",
        "expected_sum_words_minus_one": f"0x{expected_checksum:04X}",
        "checksum_matches": checksum == expected_checksum,
        "count_complement_field_offset": "0x10A",
        "count_complement": f"0x{complement:04X}",
        "expected_count_complement": f"0x{expected_complement:04X}",
        "count_complement_matches": complement == expected_complement,
        "code_end_a_field_offset": "0x10E",
        "code_end_b_field_offset": "0x110",
        "code_end_a": f"0x{end_a:04X}",
        "code_end_b": f"0x{end_b:04X}",
        "expected_code_end": f"0x{expected_end:04X}",
        "code_end_matches": end_a == expected_end and end_b == expected_end,
        "length_derived_byte_0xCA": recovered[0xCA],
        "expected_length_derived_byte_0xCA": expected_ca_low,
        "length_derived_byte_0xCA_matches": recovered[0xCA] == expected_ca_low,
        "byte_0xCB_unknown": recovered[0xCB],
        "byte_0x103_unknown": recovered[0x103],
    }


def write_sequential_experimental(
    template: Path,
    output_path: Path,
    code_words: Sequence[int],
    force: bool = False,
) -> dict:
    """Write a short sequential program stream using the confirmed metadata rules.

    Scope is deliberately limited to <=55 words so the currently observed
    byte-0xCA length relation does not wrap. This is an experimental writer.
    """
    if template.resolve() == output_path.resolve():
        raise ValueError("output must be different from template")
    if output_path.exists() and not force:
        raise FileExistsError(f"output already exists: {output_path}")
    if not code_words:
        raise ValueError("at least one code word is required")
    if len(code_words) > 55:
        raise ValueError(
            "experimental sequential writer is limited to <=55 words until "
            "the 0xCA/0xCB length fields are mapped beyond the first range"
        )
    if any(not 0 <= word <= 0xFFFF for word in code_words):
        raise ValueError("all code words must be 16-bit values")

    data = bytearray(template.read_bytes())
    if not data.startswith(MAGIC):
        raise ValueError("template is not a recognized WinProLadder PDW")

    recovered = bytearray(recover_program_candidate(bytes(data)))
    key = derive_program_xor_key(bytes(data))

    # Preserve the template's save-state/header words, but reconstruct the
    # sequential code region and the metadata proven by 0/2/13/36-word fixtures.
    recovered[0x202:] = bytes([ERASED_BYTE]) * (len(recovered) - 0x202)
    n = len(code_words)
    recovered[0xCA] = (0x23 + 4 * n) & 0xFF
    recovered[0xCB] = 0xFF
    checksum = (sum(code_words) - 1) & 0xFFFF
    recovered[0xCC:0xCE] = checksum.to_bytes(2, "little")
    recovered[0x103] = 0x00
    recovered[0x108:0x10A] = n.to_bytes(2, "little")
    recovered[0x10A:0x10C] = (0x4EFF - n).to_bytes(2, "little")
    code_end = 0x202 + 2 * n
    recovered[0x10E:0x110] = code_end.to_bytes(2, "little")
    recovered[0x110:0x112] = code_end.to_bytes(2, "little")

    for index, word in enumerate(code_words):
        offset = 0x202 + 2 * index
        recovered[offset:offset + 2] = word.to_bytes(2, "little")

    # Reapply the template transform to all 32 program records.
    for index in range(PROGRAM_RECORD_COUNT):
        plain = recovered[index * RECORD_SIZE:(index + 1) * RECORD_SIZE]
        encrypted = xor_bytes(bytes(plain), key)
        start = RECORD_START + index * RECORD_SIZE
        data[start:start + RECORD_SIZE] = encrypted

    output_path.write_bytes(data)

    verify = recover_program_candidate(bytes(data))
    verify_words = words_le(verify)
    if verify_words[PROGRAM_CODE_START_WORD:PROGRAM_CODE_START_WORD + n] != list(code_words):
        output_path.unlink(missing_ok=True)
        raise AssertionError("post-write sequential verification failed")
    metadata = summarize_program_metadata(verify)
    if not (
        metadata["checksum_matches"]
        and metadata["count_complement_matches"]
        and metadata["code_end_matches"]
        and metadata["length_derived_byte_0xCA_matches"]
    ):
        output_path.unlink(missing_ok=True)
        raise AssertionError("post-write metadata verification failed")

    return {
        "template": str(template),
        "output": str(output_path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "code_word_count": n,
        "code_words_hex": [f"0x{word:04X}" for word in code_words],
        "checksum": f"0x{checksum:04X}",
        "code_end": f"0x{code_end:04X}",
        "scope": "experimental-short-sequential-stream",
    }


def summarize_program_candidate(data: bytes, max_words: int = 64) -> dict:
    recovered = recover_program_candidate(data)
    words = words_le(recovered)
    strings = [
        {"offset": off, "hex_offset": f"0x{off:X}", "text": text}
        for off, text in ascii_strings(recovered)
        if off < 0x400
    ]
    marker_offsets = [
        i for i in range(len(recovered) - 1)
        if recovered[i:i + 2] == b"\x55\xAA"
    ]
    tail_words = [
        {
            "word_index": index,
            "byte_offset": index * 2,
            "hex_offset": f"0x{index * 2:X}",
            "value": value,
            "hex_value": f"0x{value:04X}",
        }
        for index, value in enumerate(words[256:], start=256)
        if value != 0xFFFF
    ][:max_words]
    blank_records_after_first = sum(
        recovered[i * RECORD_SIZE:(i + 1) * RECORD_SIZE]
        == bytes([ERASED_BYTE]) * RECORD_SIZE
        for i in range(1, PROGRAM_RECORD_COUNT)
    )
    decoded = []
    for index in range(PROGRAM_CODE_START_WORD, min(len(words), PROGRAM_CODE_START_WORD + max_words)):
        word = words[index]
        if word == 0xFFFF:
            break
        decoded.append({
            "word_index": index,
            "byte_offset": index * 2,
            "hex_offset": f"0x{index * 2:X}",
            "decoded": decode_sequential_word(word),
            "raw_hex": f"0x{word:04X}",
        })

    return {
        "status": "experimental_strong_hypothesis",
        "assumption": (
            "record 1 represents erased program memory filled with 0xFF; "
            "its ciphertext therefore reveals the repeating XOR transform"
        ),
        "source_offset": RECORD_START,
        "source_hex_offset": f"0x{RECORD_START:X}",
        "size_bytes": PROGRAM_BYTES,
        "size_words_16bit": PROGRAM_WORDS,
        "record_count": PROGRAM_RECORD_COUNT,
        "record_size": RECORD_SIZE,
        "reference_record_index": PROGRAM_REFERENCE_RECORD_INDEX,
        "erased_byte": ERASED_BYTE,
        "blank_records_after_first": blank_records_after_first,
        "ascii_strings_below_0x400": strings,
        "marker_55aa_offsets": marker_offsets,
        "non_erased_words_from_word_256": tail_words,
        "recovered_sha256": hashlib.sha256(recovered).hexdigest(),
        "semantic_sha256_ignoring_first_word": semantic_program_sha256(recovered),
        "save_variant_word0": f"0x{words[0]:04X}" if words else None,
        "program_code_start_word": PROGRAM_CODE_START_WORD,
        "minimal_sequential_decode": decoded,
        "program_metadata": summarize_program_metadata(recovered),
    }


def inspect_file(path: Path) -> FileReport:
    data = path.read_bytes()
    strings = ascii_strings(data)
    meaningful = [
        {"offset": offset, "hex_offset": f"0x{offset:X}", "text": text}
        for offset, text in strings
        if offset < 320 or text in {"Main_unit1", "Sub_unit1"}
    ]
    split1 = min(HEADER_STABLE_END, len(data))
    split2 = min(KNOWN_STABLE_TAIL, len(data))
    return FileReport(
        path=str(path),
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        magic_ok=data.startswith(MAGIC),
        header_ascii=meaningful,
        first_long_zero_run=first_zero_run(data),
        entropy_0_290=shannon_entropy(data[:split1]),
        entropy_290_66130=(
            shannon_entropy(data[split1:split2]) if split2 > split1 else None
        ),
        entropy_66130_eof=(
            shannon_entropy(data[split2:]) if len(data) > split2 else None
        ),
        candidate_periods=scan_candidate_periods(data),
        repeated_1280_structure=summarize_repeated_chunks(data),
    )


def compare_files(left: Path, right: Path) -> dict:
    a = left.read_bytes()
    b = right.read_bytes()
    common = min(len(a), len(b))
    changed = [i for i in range(common) if a[i] != b[i]]
    equal = [i for i in range(common) if a[i] == b[i]]
    equal_runs = contiguous_runs(equal)
    records_a = split_records(a)
    records_b = split_records(b)
    record_xor = [
        xor_bytes(ra, rb)
        for ra, rb in zip(records_a, records_b)
        if len(ra) == len(rb)
    ]

    first_delta = second_delta = None
    if len(records_a) > 33 and len(records_b) > 33:
        first_delta = xor_bytes(
            cancel_periodic_transform(a, 0, 1),
            cancel_periodic_transform(b, 0, 1),
        )
        second_delta = xor_bytes(
            cancel_periodic_transform(a, 32, 33),
            cancel_periodic_transform(b, 32, 33),
        )

    return {
        "left": asdict(inspect_file(left)),
        "right": asdict(inspect_file(right)),
        "same_size": len(a) == len(b),
        "changed_bytes_in_common_length": len(changed),
        "changed_ratio": len(changed) / common if common else 0.0,
        "first_changed_offset": changed[0] if changed else None,
        "last_changed_offset": changed[-1] if changed else None,
        "longest_equal_runs": sorted(
            equal_runs, key=lambda row: row["length"], reverse=True
        )[:10],
        "most_common_equal_offsets_mod_256": collections.Counter(
            i % 256 for i in equal if 290 <= i < 66130
        ).most_common(12),
        "record_xor_exact_period_256_indices": [
            i for i, delta in enumerate(record_xor)
            if xor_period_is_exact(delta, 256)
        ],
        "normalized_record_0_delta": {
            "nonzero_bytes": sum(v != 0 for v in first_delta),
            "runs": nonzero_runs(first_delta),
        } if first_delta is not None else None,
        "normalized_record_32_delta": {
            "nonzero_bytes": sum(v != 0 for v in second_delta),
            "runs": nonzero_runs(second_delta),
        } if second_delta is not None else None,
        "program_candidate_left": summarize_program_candidate(a),
        "program_candidate_right": summarize_program_candidate(b),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only structural analysis for FATEK WinProLadder PDW files"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="inspect one PDW file")
    p_inspect.add_argument("file", type=Path)

    p_compare = sub.add_parser("compare", help="compare two PDW files")
    p_compare.add_argument("left", type=Path)
    p_compare.add_argument("right", type=Path)

    p_recover = sub.add_parser(
        "recover-program",
        help=(
            "experimentally recover the 20K-word program candidate under the "
            "documented 0xFF-erased-record assumption"
        ),
    )
    p_recover.add_argument("file", type=Path)
    p_recover.add_argument(
        "--output",
        type=Path,
        help="optional path for the derived 40960-byte candidate image",
    )

    p_write = sub.add_parser(
        "write-minimal",
        help="write a derived 2-word ORG/ORG NOT Xn -> OUT Yn PDW from a safe template",
    )
    p_write.add_argument("template", type=Path)
    p_write.add_argument("output", type=Path)
    p_write.add_argument("--x", type=int, required=True, dest="x_index")
    p_write.add_argument("--y", type=int, required=True, dest="y_index")
    p_write.add_argument("--nc", action="store_true", help="use ORG NOT instead of ORG")
    p_write.add_argument("--force", action="store_true")
    p_write.add_argument(
        "--allow-unconfirmed-index",
        action="store_true",
        help="allow X/Y indices above 2 for explicit experiments",
    )

    p_seq = sub.add_parser(
        "write-sequential-experimental",
        help=(
            "write a short raw sequential-word stream using metadata rules "
            "confirmed by the controlled corpus"
        ),
    )
    p_seq.add_argument("template", type=Path)
    p_seq.add_argument("output", type=Path)
    p_seq.add_argument(
        "words",
        nargs="+",
        help="16-bit words, e.g. 0x1C48 0x1D68 0x40F9",
    )
    p_seq.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.command == "inspect":
        payload = asdict(inspect_file(args.file))
    elif args.command == "compare":
        payload = compare_files(args.left, args.right)
    elif args.command == "recover-program":
        data = args.file.read_bytes()
        recovered = recover_program_candidate(data)
        if args.output is not None:
            args.output.write_bytes(recovered)
        payload = summarize_program_candidate(data)
        payload["output"] = str(args.output) if args.output is not None else None
    elif args.command == "write-minimal":
        payload = write_minimal_rung(
            args.template,
            args.output,
            args.x_index,
            args.y_index,
            nc=args.nc,
            force=args.force,
            allow_unconfirmed_index=args.allow_unconfirmed_index,
        )
    else:
        parsed_words = [int(value, 0) for value in args.words]
        payload = write_sequential_experimental(
            args.template,
            args.output,
            parsed_words,
            force=args.force,
        )

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
