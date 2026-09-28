from __future__ import annotations

from dataclasses import dataclass
import re
import struct
from typing import Iterable, Sequence


class LadderError(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    offset: int
    raw: bytes


@dataclass(frozen=True)
class Instruction:
    mnemonic: str
    operands: tuple[str, ...]
    raw_tokens: tuple[Token, ...]
    rung_mode: str | None = None


DEVICE_TYPES = {
    0x90: "M",
    0x9C: "X",
    0x9D: "Y",
    0xA8: "D",
    0xC2: "T",
    0xC5: "C",
    0xE8: "K16",
    0xE9: "K32",
    0xEA: "H",
}
TYPE_CODES = {v: k for k, v in DEVICE_TYPES.items()}

BASIC = {
    bytes.fromhex("030003"): ("LD", 1),
    bytes.fromhex("030103"): ("LDI", 1),
    bytes.fromhex("030603"): ("OR", 1),
    bytes.fromhex("030703"): ("ORI", 1),
    bytes.fromhex("030c03"): ("AND", 1),
    bytes.fromhex("030d03"): ("ANDI", 1),
    bytes.fromhex("031803"): ("ORB", 0),
    bytes.fromhex("031903"): ("ANB", 0),
    bytes.fromhex("032003"): ("OUT", 1),
    bytes.fromhex("032303"): ("SET", 1),
    bytes.fromhex("032403"): ("RST", 1),
    bytes.fromhex("033403"): ("END", 0),
    bytes.fromhex("04210304"): ("TCOUT", 2),
    bytes.fromhex("04250204"): ("PLS", 1),
}

APP_HEADERS = {
    bytes.fromhex("054c050005"): ("MOV", 2),
    bytes.fromhex("054c090105"): ("DMOV", 2),
    bytes.fromhex("054c070605"): ("BMOV", 3),
    bytes.fromhex("05490d2905"): ("DADD", 3),
    bytes.fromhex("0553051905"): ("ZRST", 2),
}

COMPARE_SYMBOLS = {0: "=", 1: "<>", 2: ">", 3: ">=", 4: "<", 5: "<="}


def tokenize(raw: bytes) -> list[Token]:
    out: list[Token] = []
    pos = 0
    while pos < len(raw):
        length = raw[pos]
        if length < 3:
            raise LadderError(f"invalid token length {length} at +0x{pos:X}")
        end = pos + length
        if end > len(raw):
            raise LadderError(f"truncated token at +0x{pos:X}")
        token = raw[pos:end]
        if token[-1] != length:
            raise LadderError(
                f"token sentinel mismatch at +0x{pos:X}: first={length}, last={token[-1]}"
            )
        out.append(Token(pos, token))
        pos = end
    return out


def _payload_unsigned(token: bytes) -> int:
    payload = token[2:-1]
    return int.from_bytes(payload, "little", signed=False) if payload else 0


def decode_operand(token: Token) -> str:
    raw = token.raw
    if len(raw) < 4 or raw[1] not in DEVICE_TYPES:
        raise LadderError(f"not a supported operand token at +0x{token.offset:X}: {raw.hex()}")
    kind = DEVICE_TYPES[raw[1]]
    payload = raw[2:-1]
    unsigned = int.from_bytes(payload, "little", signed=False) if payload else 0
    if kind in ("X", "Y"):
        return f"{kind}{unsigned:o}"
    if kind == "K16":
        if len(payload) == 2 and payload[-1] & 0x80:
            value = int.from_bytes(payload, "little", signed=True)
        else:
            value = unsigned
        return f"K{value}"
    if kind == "K32":
        if len(payload) == 4 and payload[-1] & 0x80:
            value = int.from_bytes(payload, "little", signed=True)
        else:
            value = unsigned
        return f"K{value}"
    if kind == "H":
        return f"H{unsigned:X}"
    return f"{kind}{unsigned}"


def decode_program(token_stream: bytes) -> list[Instruction]:
    tokens = tokenize(token_stream)
    out: list[Instruction] = []
    i = 0
    while i < len(tokens):
        head = tokens[i]
        raw = head.raw
        if raw in BASIC:
            mnemonic, argc = BASIC[raw]
            if i + argc >= len(tokens) + 1:
                raise LadderError(f"missing operands after {mnemonic}")
            operands = tuple(decode_operand(tokens[i + j]) for j in range(1, argc + 1))
            if mnemonic == "TCOUT":
                mnemonic = "TIMER" if operands and operands[0].startswith("T") else "COUNTER"
            out.append(Instruction(mnemonic, operands, tuple(tokens[i : i + argc + 1])))
            i += argc + 1
            continue
        if raw in APP_HEADERS:
            mnemonic, argc = APP_HEADERS[raw]
            operands = tuple(decode_operand(tokens[i + j]) for j in range(1, argc + 1))
            out.append(Instruction(mnemonic, operands, tuple(tokens[i : i + argc + 1])))
            i += argc + 1
            continue
        if len(raw) == 6 and raw[1] == 0x40 and raw[-1] == 6:
            width = raw[2]
            op_code = raw[3]
            mode_code = raw[4]
            is_double = width == 0x09
            base = op_code - 6 if is_double else op_code
            if base not in COMPARE_SYMBOLS or mode_code not in (0x10, 0x11):
                raise LadderError(f"unknown compare token at +0x{head.offset:X}: {raw.hex()}")
            symbol = COMPARE_SYMBOLS[base]
            mnemonic = ("D" if is_double else "") + symbol
            operands = (decode_operand(tokens[i + 1]), decode_operand(tokens[i + 2]))
            out.append(
                Instruction(
                    mnemonic,
                    operands,
                    tuple(tokens[i : i + 3]),
                    rung_mode="LD" if mode_code == 0x10 else "AND",
                )
            )
            i += 3
            continue
        raise LadderError(f"unknown instruction token at +0x{head.offset:X}: {raw.hex(' ')}")
    return out


def to_gx_text_writer(instructions: Sequence[Instruction]) -> str:
    lines: list[str] = []
    rung_open = False
    for ins in instructions:
        m = ins.mnemonic
        if m == "END":
            continue
        if m in ("LD", "AND", "OR"):
            lines.append(f"[NO {ins.operands[0]}]")
            rung_open = True
        elif m in ("LDI", "ANDI", "ORI"):
            lines.append(f"[NC {ins.operands[0]}]")
            rung_open = True
        elif m in ("ORB", "ANB"):
            lines.append(f"[APP {m}]")
            rung_open = True
        elif m == "OUT":
            lines.append(f"[COIL {ins.operands[0]}]")
            lines.append("")
            rung_open = False
        elif m in ("TIMER", "COUNTER"):
            lines.append(f"[COIL {' '.join(ins.operands)}]")
            lines.append("")
            rung_open = False
        elif m == "PLS":
            lines.append(f"[APP PLS {ins.operands[0]}]")
            lines.append("")
            rung_open = False
        elif m in ("SET", "RST"):
            lines.append(f"[APP {m} {ins.operands[0]}]")
            lines.append("")
            rung_open = False
        else:
            lines.append(f"[APP {m} {' '.join(ins.operands)}]")
            if m in ("=", "<>", ">", ">=", "<", "<=", "D=", "D<>", "D>", "D>=", "D<", "D<="):
                rung_open = True
            else:
                lines.append("")
                rung_open = False
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")


_DEVICE_RE = re.compile(r"^([MXYDTC])([0-9]+)$", re.I)
_CONST_RE = re.compile(r"^K(-?[0-9]+)$", re.I)
_HEX_RE = re.compile(r"^H([0-9A-F]+)$", re.I)


def _minimal_unsigned(value: int) -> bytes:
    if value < 0:
        raise LadderError("unsigned value cannot be negative")
    n = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(n, "little")


def encode_operand(text: str, semantic_width: int | None = None) -> bytes:
    text = text.strip().upper()
    m = _DEVICE_RE.match(text)
    if m:
        prefix, digits = m.groups()
        value = int(digits, 8 if prefix in ("X", "Y") else 10)
        type_code = TYPE_CODES[prefix]
        payload = _minimal_unsigned(value)
    else:
        m = _CONST_RE.match(text)
        if m:
            value = int(m.group(1), 10)
            width = 32 if semantic_width == 32 else 16
            type_code = TYPE_CODES["K32" if width == 32 else "K16"]
            if value < 0:
                payload = value.to_bytes(width // 8, "little", signed=True)
            else:
                payload = _minimal_unsigned(value)
        else:
            m = _HEX_RE.match(text)
            if not m:
                raise LadderError(f"unsupported operand: {text}")
            value = int(m.group(1), 16)
            type_code = TYPE_CODES["H"]
            payload = _minimal_unsigned(value)
    length = len(payload) + 3
    if length > 255:
        raise LadderError("operand token too large")
    return bytes([length, type_code]) + payload + bytes([length])


def _comparison_header(mnemonic: str, first_condition: bool) -> bytes:
    m = mnemonic.upper()
    double = m.startswith("D")
    symbol = m[1:] if double else m
    inv = {v: k for k, v in COMPARE_SYMBOLS.items()}
    if symbol not in inv:
        raise LadderError(f"unsupported comparison: {mnemonic}")
    op = inv[symbol] + (6 if double else 0)
    width = 0x09 if double else 0x05
    mode = 0x10 if first_condition else 0x11
    return bytes([0x06, 0x40, width, op, mode, 0x06])


def _app_header(mnemonic: str) -> tuple[bytes, tuple[int | None, ...]]:
    m = mnemonic.upper()
    if m == "MOV":
        return bytes.fromhex("054c050005"), (16, 16)
    if m == "DMOV":
        return bytes.fromhex("054c090105"), (32, 32)
    if m == "BMOV":
        return bytes.fromhex("054c070605"), (16, 16, 16)
    if m == "DADD":
        return bytes.fromhex("05490d2905"), (32, 32, 32)
    if m == "ZRST":
        return bytes.fromhex("0553051905"), (16, 16)
    raise LadderError(f"unsupported application instruction for writer: {mnemonic}")


def parse_bracket_source(source: str) -> list[list[tuple[str, tuple[str, ...]]]]:
    rungs: list[list[tuple[str, tuple[str, ...]]]] = []
    current: list[tuple[str, tuple[str, ...]]] = []
    for lineno, raw_line in enumerate(source.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            if current:
                rungs.append(current)
                current = []
            continue
        if line.startswith(";"):
            continue
        if not (line.startswith("[") and line.endswith("]")):
            raise LadderError(f"line {lineno}: expected [..] instruction, got {line!r}")
        parts = line[1:-1].strip().split()
        if not parts:
            continue
        kind = parts[0].upper()
        if kind in ("NO", "NC"):
            if len(parts) != 2:
                raise LadderError(f"line {lineno}: {kind} requires one operand")
            current.append((kind, (parts[1],)))
        elif kind == "COIL":
            if len(parts) not in (2, 3):
                raise LadderError(f"line {lineno}: COIL requires device [preset]")
            current.append(("COIL", tuple(parts[1:])))
        elif kind == "APP":
            if len(parts) < 2:
                raise LadderError(f"line {lineno}: APP requires an instruction")
            current.append((parts[1].upper(), tuple(parts[2:])))
        else:
            raise LadderError(f"line {lineno}: unsupported bracket instruction {kind}")
    if current:
        rungs.append(current)
    return rungs


def compile_bracket_source(source: str, *, add_end: bool = True) -> bytes:
    out = bytearray()
    for rung_index, rung in enumerate(parse_bracket_source(source)):
        condition_index = 0
        terminal_seen = False
        for idx, (kind, operands) in enumerate(rung):
            if terminal_seen:
                raise LadderError(f"rung {rung_index + 1}: instruction after terminal output")
            if kind in ("NO", "NC"):
                opcode = (0x00 if kind == "NO" else 0x01) if condition_index == 0 else (0x0C if kind == "NO" else 0x0D)
                out.extend(bytes([0x03, opcode, 0x03]))
                out.extend(encode_operand(operands[0]))
                condition_index += 1
                continue
            if kind in ("=", "<>", ">", ">=", "<", "<=", "D=", "D<>", "D>", "D>=", "D<", "D<="):
                if len(operands) != 2:
                    raise LadderError(f"rung {rung_index + 1}: {kind} requires two operands")
                out.extend(_comparison_header(kind, condition_index == 0))
                width = 32 if kind.startswith("D") else 16
                out.extend(encode_operand(operands[0], width))
                out.extend(encode_operand(operands[1], width))
                condition_index += 1
                continue
            if kind == "COIL":
                if len(operands) == 1:
                    out.extend(bytes.fromhex("032003"))
                    out.extend(encode_operand(operands[0]))
                elif len(operands) == 2 and operands[0].upper().startswith(("T", "C")):
                    out.extend(bytes.fromhex("04210304"))
                    out.extend(encode_operand(operands[0]))
                    out.extend(encode_operand(operands[1]))
                else:
                    raise LadderError(f"rung {rung_index + 1}: unsupported COIL form")
                terminal_seen = True
                continue
            if kind == "PLS":
                if len(operands) != 1:
                    raise LadderError("PLS requires one operand")
                out.extend(bytes.fromhex("04250204"))
                out.extend(encode_operand(operands[0]))
                terminal_seen = True
                continue
            if kind in ("SET", "RST"):
                if len(operands) != 1:
                    raise LadderError(f"{kind} requires one operand")
                out.extend(bytes.fromhex("032303") if kind == "SET" else bytes.fromhex("032403"))
                out.extend(encode_operand(operands[0]))
                terminal_seen = True
                continue
            if kind in ("MOV", "DMOV", "BMOV", "DADD", "ZRST"):
                header, widths = _app_header(kind)
                if len(operands) != len(widths):
                    raise LadderError(f"{kind} requires {len(widths)} operands")
                out.extend(header)
                for operand, width in zip(operands, widths):
                    out.extend(encode_operand(operand, width))
                terminal_seen = True
                continue
            if kind in ("ORB", "ANB"):
                out.extend(bytes.fromhex("031803") if kind == "ORB" else bytes.fromhex("031903"))
                condition_index += 1
                continue
            raise LadderError(f"unsupported instruction for writer: {kind}")
        if not terminal_seen:
            raise LadderError(f"rung {rung_index + 1}: no terminal output/application instruction")
    if add_end:
        out.extend(bytes.fromhex("033403"))
    return bytes(out)


def program_pou_token_stream(pou: bytes) -> bytes:
    if len(pou) < 0x67:
        raise LadderError("Program.pou too short")
    length_like = struct.unpack_from("<I", pou, 0x37)[0]
    length_like2 = struct.unpack_from("<I", pou, 0x3B)[0]
    if length_like != length_like2 or length_like < 20:
        raise LadderError("unsupported Program.pou header length fields")
    token_length = length_like - 20
    start = 0x4F
    end = start + token_length
    if end + 24 != len(pou):
        raise LadderError(
            f"unsupported Program.pou layout: size={len(pou)}, token_end=0x{end:X}, trailer={len(pou)-end}"
        )
    if pou[end:] != b"\x00" * 24:
        raise LadderError("unexpected Program.pou trailer")
    tokenize(pou[start:end])
    return pou[start:end]


def replace_program_pou_tokens(pou: bytes, token_stream: bytes) -> bytes:
    program_pou_token_stream(pou)
    tokenize(token_stream)
    if not token_stream.endswith(bytes.fromhex("033403")):
        raise LadderError("token stream must end with END")
    length_like = len(token_stream) + 20
    header = bytearray(pou[:0x4F])
    struct.pack_into("<I", header, 0x37, length_like)
    struct.pack_into("<I", header, 0x3B, length_like)
    return bytes(header) + token_stream + b"\x00" * 24


def replace_res_token_copies(res: bytes, old_tokens: bytes, new_tokens: bytes) -> bytes:
    first = res.find(old_tokens)
    if first != 0x3A:
        raise LadderError(f"unexpected first .res token offset: {first}")
    second = res.find(old_tokens, first + len(old_tokens))
    if second < 0 or res.find(old_tokens, second + 1) >= 0:
        raise LadderError(".res must contain exactly two copies of Program.pou token stream")
    if struct.unpack_from("<I", res, 0x36)[0] != len(old_tokens):
        raise LadderError(".res first token length field mismatch")
    gap = res[first + len(old_tokens) : second]
    if len(gap) != 12 or gap[:8] != b"\x00" * 8 or struct.unpack_from("<I", gap, 8)[0] != len(old_tokens):
        raise LadderError("unsupported .res gap between token copies")
    after_second = second + len(old_tokens)
    if res[after_second : after_second + 8] != b"\x00" * 8:
        raise LadderError("unsupported .res trailer after second token copy")
    return (
        res[:0x36]
        + struct.pack("<I", len(new_tokens))
        + new_tokens
        + b"\x00" * 8
        + struct.pack("<I", len(new_tokens))
        + new_tokens
        + res[after_second:]
    )
