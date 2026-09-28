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

KNOWN_LOW_OPCODES = {
    0x40: ("ORG", "X", "confirmed for X0/X1"),
    0x50: ("ORG NOT", "X", "confirmed for X0; index layout inferred"),
    0xC1: ("OUT", "Y", "confirmed for Y0/Y1"),
}


def c_string(block: bytes) -> str:
    return block.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def decode_word(word: int) -> dict | None:
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


def inspect_ldr(path: Path) -> dict:
    data = path.read_bytes()
    payload = data[PAYLOAD_OFFSET:] if len(data) >= PAYLOAD_OFFSET else b""
    words = []
    for rel in range(0, len(payload) - 1, 2):
        word = struct.unpack_from("<H", payload, rel)[0]
        decoded = decode_word(word)
        words.append({
            "payload_offset": rel,
            "file_offset": PAYLOAD_OFFSET + rel,
            "hex_file_offset": f"0x{PAYLOAD_OFFSET + rel:X}",
            "word": word,
            "hex_word": f"0x{word:04X}",
            "decoded": decoded,
        })

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
        "payload_hex": payload.hex(),
        "words": words,
        "known_decoded_words": [
            item for item in words if item["decoded"] is not None
        ],
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
