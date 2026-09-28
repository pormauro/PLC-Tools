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

    args = parser.parse_args()

    if args.command == "inspect":
        payload = asdict(inspect_file(args.file))
    elif args.command == "compare":
        payload = compare_files(args.left, args.right)
    else:
        data = args.file.read_bytes()
        recovered = recover_program_candidate(data)
        if args.output is not None:
            args.output.write_bytes(recovered)
        payload = summarize_program_candidate(data)
        payload["output"] = str(args.output) if args.output is not None else None

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
