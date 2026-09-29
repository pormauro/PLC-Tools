#!/usr/bin/env python3
"""Read-only inspector for FATEK WinProLadder .ldr resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

MAGIC = b"Fatek Resource File Format 1"
PAYLOAD_OFFSET = 0x100
NETWORK_MARKER = b"\x12\x10"
TERMINATOR = b"\xFF\xFF\x00\x00\x00\x00"

KNOWN_LOW_OPCODES = {
    0x40: ("ORG", "X", "index=high byte"),
    0x50: ("ORG NOT", "X", "index=high byte"),
    0x90: ("AND NOT", "X", "index=high byte"),
    0xA1: ("OR", "Y", "index=high byte"),
    0xC1: ("OUT", "Y", "index=high byte"),
}

KNOWN_M_OPCODES = {
    0x48: "ORG",
    0x58: "ORG NOT",
    0xC8: "OUT",
    0xD8: "OUT NOT",
}

KNOWN_EXACT_WORDS = {
    0x41FD: ("FUN87 T.01S", "visual-confirmed; FATEK catalog identifies FUN87 as .01S accumulative timer"),
    0x42FD: ("FUN88 T.1S", "visual-confirmed; FATEK catalog identifies FUN88 as .1S accumulative timer"),
    0xB2F5: ("FUN43 NBM", "visual-confirmed in todooo fixture"),
}

GENERAL_TIMER_BASE = {
    0x80FD: (".01S", "visual-confirmed"),
    0x81FD: (".1S", "visual-confirmed"),
    0x82FD: ("1S", "candidate; prepared probe"),
}


def c_string(block: bytes) -> str:
    return block.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def be_value_from_diagnostic_word(word: int) -> int:
    """Interpret the two raw code bytes as a big-endian immediate value."""
    return int.from_bytes(word.to_bytes(2, "little"), "big")


def decode_word(word: int) -> dict | None:
    exact = KNOWN_EXACT_WORDS.get(word)
    if exact is not None:
        text, evidence = exact
        return {
            "word": word,
            "hex_word": f"0x{word:04X}",
            "mnemonic": text,
            "operand": None,
            "text": text,
            "evidence": evidence,
        }

    opcode = word & 0xFF
    high = (word >> 8) & 0xFF

    known = KNOWN_LOW_OPCODES.get(opcode)
    if known is not None:
        mnemonic, family, evidence = known
        return {
            "word": word,
            "hex_word": f"0x{word:04X}",
            "mnemonic": mnemonic,
            "operand": f"{family}{high}",
            "text": f"{mnemonic} {family}{high}",
            "evidence": evidence,
        }

    if opcode in KNOWN_M_OPCODES and high >= 0x10:
        index = high - 0x10
        mnemonic = KNOWN_M_OPCODES[opcode]
        return {
            "word": word,
            "hex_word": f"0x{word:04X}",
            "mnemonic": mnemonic,
            "operand": f"M{index}",
            "text": f"{mnemonic} M{index}",
            "evidence": "confirmed by varios PDW/LDR + screenshot",
        }

    if word == 0x00EA:
        return {
            "word": word,
            "hex_word": "0x00EA",
            "mnemonic": "TU",
            "operand": None,
            "text": "TU",
            "evidence": "confirmed rising-edge node in varios fixture",
        }
    if word == 0x00E8:
        return {
            "word": word,
            "hex_word": "0x00E8",
            "mnemonic": "TD",
            "operand": None,
            "text": "TD",
            "evidence": "confirmed falling-edge node in varios fixture",
        }
    if word == 0x00E0:
        return {
            "word": word,
            "hex_word": "0x00E0",
            "mnemonic": "EDGE_CONTACT_PREFIX",
            "operand": None,
            "text": "edge-contact prefix",
            "evidence": "observed before ORG TU/TD M contacts",
        }
    return None


def decode_function_pair(word: int, operand_word: int) -> dict | None:
    mapping = {
        0x82FC: ("SET", False),
        0x82F8: ("SET", True),
        0xC4FC: ("RST", False),
        0xC4F8: ("RST", True),
    }
    known = mapping.get(word)
    if known is None:
        return None
    if (operand_word & 0xFF) != 0x08 or ((operand_word >> 8) & 0xFF) < 0x10:
        return None
    index = ((operand_word >> 8) & 0xFF) - 0x10
    mnemonic, pulse = known
    return {
        "words": [f"0x{word:04X}", f"0x{operand_word:04X}"],
        "mnemonic": f"{mnemonic} P" if pulse else mnemonic,
        "operand": f"M{index}",
        "text": f"{mnemonic}{' P' if pulse else ''} M{index}",
        "pulse": pulse,
        "evidence": "confirmed by varios PDW/LDR + screenshot",
    }


def decode_timer_counter_block(words: list[int], index: int) -> tuple[dict, int] | None:
    word = words[index]

    # General timer block body:
    #   base-selector, PV(raw big-endian bytes), T-ref, FC6F
    if word in GENERAL_TIMER_BASE and index + 3 < len(words):
        pv_word = words[index + 1]
        ref_word = words[index + 2]
        trailer = words[index + 3]
        if trailer == 0xFC6F and (ref_word & 0xFF) == 0x03:
            ref_high = (ref_word >> 8) & 0xFF
            timer_index = ref_high - 0x90 if ref_high >= 0x90 else None
            base, base_evidence = GENERAL_TIMER_BASE[word]
            ref_evidence = (
                "T0 visual-confirmed" if timer_index == 0
                else "candidate T index encoding"
            )
            return ({
                "kind": "general_timer",
                "words": [f"0x{w:04X}" for w in words[index:index + 4]],
                "time_base": base,
                "time_base_evidence": base_evidence,
                "pv": be_value_from_diagnostic_word(pv_word),
                "pv_raw_bytes": pv_word.to_bytes(2, "little").hex(),
                "timer_ref_raw": f"0x{ref_word:04X}",
                "timer_index_candidate": timer_index,
                "timer_ref_evidence": ref_evidence,
            }, 4)

    # General C0-family counter block body:
    #   40F9, PV(raw big-endian bytes), C-ref, FC6F
    if word == 0x40F9 and index + 3 < len(words):
        pv_word = words[index + 1]
        ref_word = words[index + 2]
        trailer = words[index + 3]
        if trailer == 0xFC6F and (ref_word & 0xFF) == 0x05:
            ref_high = (ref_word >> 8) & 0xFF
            counter_index = ref_high - 0x90 if ref_high >= 0x90 else None
            ref_evidence = (
                "C0 visual-confirmed" if counter_index == 0
                else "candidate C index encoding"
            )
            return ({
                "kind": "general_counter",
                "words": [f"0x{w:04X}" for w in words[index:index + 4]],
                "pv": be_value_from_diagnostic_word(pv_word),
                "pv_raw_bytes": pv_word.to_bytes(2, "little").hex(),
                "counter_ref_raw": f"0x{ref_word:04X}",
                "counter_index_candidate": counter_index,
                "counter_ref_evidence": ref_evidence,
                "evidence": "0x40F9 visually confirmed for C0 block",
            }, 4)

    return None


def annotate_code(code: bytes) -> list[dict]:
    words = [
        struct.unpack_from("<H", code, off)[0]
        for off in range(0, len(code) - 1, 2)
    ]
    out: list[dict] = []
    i = 0
    while i < len(words):
        word = words[i]

        block = decode_timer_counter_block(words, i)
        if block is not None:
            decoded_block, consumed = block
            out.append({"word_index": i, **decoded_block})
            i += consumed
            continue

        if i + 1 < len(words):
            fn = decode_function_pair(word, words[i + 1])
            if fn is not None:
                out.append({"word_index": i, "kind": "function", **fn})
                i += 2
                continue

        # In the observed fixture, 0x00E0 + ORG M encodes ORG TU M,
        # while 0x00E0 + ORG NOT M encodes ORG TD M.
        if i + 1 < len(words) and word == 0x00E0:
            nxt = words[i + 1]
            low = nxt & 0xFF
            high = (nxt >> 8) & 0xFF
            if high >= 0x10 and low in (0x48, 0x58):
                idx = high - 0x10
                edge = "TU" if low == 0x48 else "TD"
                out.append({
                    "word_index": i,
                    "kind": "edge_contact",
                    "words": [f"0x{word:04X}", f"0x{nxt:04X}"],
                    "text": f"ORG {edge} M{idx}",
                    "evidence": "confirmed by varios PDW/LDR + screenshot",
                })
                i += 2
                continue

        decoded = decode_word(word)
        out.append({
            "word_index": i,
            "kind": "word",
            "raw": f"0x{word:04X}",
            "decoded": decoded,
        })
        i += 1
    return out


def parse_network_records(payload: bytes) -> tuple[list[dict], bytes]:
    records: list[dict] = []
    pos = 0
    while pos + 6 <= len(payload):
        if payload[pos:pos + len(TERMINATOR)] == TERMINATOR:
            break
        if payload[pos:pos + 2] != NETWORK_MARKER:
            break

        envelope_len = struct.unpack_from("<H", payload, pos + 2)[0]
        code_len = struct.unpack_from("<H", payload, pos + 4)[0]
        total_len = 6 + envelope_len
        if envelope_len != code_len + 5:
            raise ValueError(
                f"network record at payload +0x{pos:X}: "
                f"envelope_len={envelope_len}, code_len={code_len}"
            )
        if pos + total_len > len(payload):
            raise ValueError("truncated LDR network record")

        code_start = pos + 6
        code_end = code_start + code_len
        trailer = payload[code_end:pos + total_len]
        code = payload[code_start:code_end]
        records.append({
            "record_index_in_file": len(records),
            "payload_offset": pos,
            "file_offset": PAYLOAD_OFFSET + pos,
            "total_length": total_len,
            "envelope_length_field": envelope_len,
            "code_length_bytes": code_len,
            "code_hex": code.hex(),
            "code_words": [
                f"0x{struct.unpack_from('<H', code, off)[0]:04X}"
                for off in range(0, len(code) - 1, 2)
            ],
            "trailer_hex": trailer.hex(),
            "annotations": annotate_code(code),
        })
        pos += total_len

    count = len(records)
    for i, record in enumerate(records):
        # varios.ldr proves that records are exported in reverse ladder order.
        record["network_number_if_reverse_order"] = count - 1 - i

    return records, payload[pos:]


def inspect_ldr(path: Path) -> dict:
    data = path.read_bytes()
    payload = data[PAYLOAD_OFFSET:] if len(data) >= PAYLOAD_OFFSET else b""
    records, remainder = parse_network_records(payload)

    return {
        "path": str(path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "magic_ok": data.startswith(MAGIC),
        "resource_type": c_string(data[0x80:0x90]) if len(data) >= 0x90 else None,
        "producer": c_string(data[0x90:0xA0]) if len(data) >= 0xA0 else None,
        "plc_model": c_string(data[0xA0:0xB0]) if len(data) >= 0xB0 else None,
        "payload_offset": PAYLOAD_OFFSET,
        "payload_size": len(payload),
        "network_record_count": len(records),
        "network_records": records,
        "payload_remainder_hex": remainder.hex(),
        "terminator_ok": remainder.startswith(TERMINATOR),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only inspector for FATEK WinProLadder LDR resources"
    )
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_ldr(args.file), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
