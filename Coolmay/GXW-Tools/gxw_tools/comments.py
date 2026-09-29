from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import struct
from typing import Iterable, Sequence


class CommentTableError(ValueError):
    pass


_DEVICE_TO_QCD = {
    "X": (0x009C, 0, True),
    "Y": (0x009D, 0, True),
    "M": (0x0090, 0, False),
    "D": (0x00A8, 0, False),
    "T": (0x00C2, 200, False),
}
_QCD_TO_DEVICE = {code: (dev, base, octal) for dev, (code, base, octal) in _DEVICE_TO_QCD.items()}

QCD_RANGE_MARKER = 0x0A20
QCD_RANGE_OFFSET = 0x3C
QCD_LENGTH_FIELD_OFFSET = 0x32
QCD_RANGE_MARKER_OFFSET = 0x38
QCD_RANGE_COUNT_OFFSET = 0x3A


@dataclass(frozen=True)
class DeviceComment:
    device: str
    text: str


@dataclass(frozen=True)
class QCDRange:
    type_code: int
    start: int
    count: int


@dataclass(frozen=True)
class CommentTable:
    comments: tuple[DeviceComment, ...]
    ranges: tuple[QCDRange, ...]
    header: bytes


def _device_to_qcd(device: str) -> tuple[int, int]:
    d = device.strip().upper()
    if len(d) < 2:
        raise CommentTableError(f"invalid device: {device!r}")
    kind, number = d[0], d[1:]
    if kind not in _DEVICE_TO_QCD:
        raise CommentTableError(f"unsupported COMMENT.qcd device type: {kind}")
    type_code, base, octal = _DEVICE_TO_QCD[kind]
    try:
        absolute = int(number, 8 if octal else 10)
    except ValueError as exc:
        raise CommentTableError(f"invalid {kind} address: {device!r}") from exc
    index = absolute - base
    if index < 0:
        raise CommentTableError(f"{device!r} is below supported {kind} base {base}")
    return type_code, index


def _qcd_to_device(type_code: int, index: int) -> str:
    if type_code not in _QCD_TO_DEVICE:
        raise CommentTableError(f"unsupported COMMENT.qcd type code 0x{type_code:04X}")
    kind, base, octal = _QCD_TO_DEVICE[type_code]
    absolute = base + index
    return f"{kind}{absolute:o}" if octal else f"{kind}{absolute}"


def parse_comment_qcd(data: bytes) -> CommentTable:
    if len(data) < QCD_RANGE_OFFSET + 4:
        raise CommentTableError("COMMENT.qcd too short")
    stored_length = struct.unpack_from("<I", data, QCD_LENGTH_FIELD_OFFSET)[0]
    if stored_length != len(data) - QCD_LENGTH_FIELD_OFFSET:
        raise CommentTableError(
            f"COMMENT.qcd length field mismatch: {stored_length} != {len(data) - QCD_LENGTH_FIELD_OFFSET}"
        )
    marker = struct.unpack_from("<H", data, QCD_RANGE_MARKER_OFFSET)[0]
    if marker != QCD_RANGE_MARKER:
        raise CommentTableError(f"unexpected COMMENT.qcd range marker 0x{marker:04X}")
    range_count = struct.unpack_from("<H", data, QCD_RANGE_COUNT_OFFSET)[0]
    pos = QCD_RANGE_OFFSET
    ranges: list[QCDRange] = []
    for _ in range(range_count):
        if pos + 10 > len(data):
            raise CommentTableError("truncated COMMENT.qcd range table")
        type_code, start, count = struct.unpack_from("<HII", data, pos)
        ranges.append(QCDRange(type_code, start, count))
        pos += 10

    if pos + 4 > len(data):
        raise CommentTableError("missing COMMENT.qcd text-block prefix")
    text_prefix = struct.unpack_from("<I", data, pos)[0]
    if text_prefix != 0:
        raise CommentTableError(f"unexpected COMMENT.qcd text-block prefix {text_prefix}")
    pos += 4

    total = sum(r.count for r in ranges)
    texts: list[str] = []
    for i in range(total):
        if pos + 4 > len(data):
            raise CommentTableError(f"truncated label length at record {i}")
        char_count = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if char_count < 1:
            raise CommentTableError(f"invalid UTF-16 character count {char_count} at record {i}")
        byte_count = char_count * 2
        if pos + byte_count > len(data):
            raise CommentTableError(f"truncated UTF-16 label at record {i}")
        raw = data[pos : pos + byte_count]
        pos += byte_count
        if raw[-2:] != b"\x00\x00":
            raise CommentTableError(f"label record {i} lacks UTF-16 NUL terminator")
        try:
            text = raw[:-2].decode("utf-16le")
        except UnicodeDecodeError as exc:
            raise CommentTableError(f"invalid UTF-16 label at record {i}") from exc
        texts.append(text)
        if i + 1 < total:
            if pos + 4 > len(data):
                raise CommentTableError(f"missing label separator after record {i}")
            separator = struct.unpack_from("<I", data, pos)[0]
            if separator != 0:
                raise CommentTableError(
                    f"unexpected label separator 0x{separator:08X} after record {i}"
                )
            pos += 4

    if pos != len(data):
        raise CommentTableError(f"unexpected trailing COMMENT.qcd data: {len(data) - pos} bytes")

    comments: list[DeviceComment] = []
    i = 0
    for r in ranges:
        for offset in range(r.count):
            comments.append(DeviceComment(_qcd_to_device(r.type_code, r.start + offset), texts[i]))
            i += 1
    return CommentTable(tuple(comments), tuple(ranges), bytes(data[:QCD_RANGE_OFFSET]))


def _ranges_for_comments(comments: Sequence[DeviceComment]) -> tuple[list[QCDRange], list[DeviceComment]]:
    encoded: list[tuple[int, int, DeviceComment]] = []
    for item in comments:
        if not item.text:
            continue
        type_code, index = _device_to_qcd(item.device)
        encoded.append((type_code, index, DeviceComment(item.device.strip().upper(), item.text)))
    if not encoded:
        return [], []

    family_order = {0x009C: 0, 0x009D: 1, 0x0090: 2, 0x00C2: 3, 0x00A8: 4}
    encoded.sort(key=lambda x: (family_order.get(x[0], 99), x[1]))

    seen: set[tuple[int, int]] = set()
    for type_code, index, _ in encoded:
        key = (type_code, index)
        if key in seen:
            raise CommentTableError(f"duplicate comment device {_qcd_to_device(type_code, index)}")
        seen.add(key)

    ranges: list[QCDRange] = []
    ordered: list[DeviceComment] = []
    start_type, start_idx = encoded[0][0], encoded[0][1]
    last_idx = start_idx
    count = 0
    for type_code, index, item in encoded:
        starts_new_range = count > 0 and (type_code != start_type or index != last_idx + 1)
        if starts_new_range:
            ranges.append(QCDRange(start_type, start_idx, count))
            start_type, start_idx, count = type_code, index, 0
        ordered.append(item)
        last_idx = index
        count += 1
    ranges.append(QCDRange(start_type, start_idx, count))
    return ranges, ordered


def serialize_comment_qcd(table: CommentTable | Sequence[DeviceComment], *, template: bytes | None = None) -> bytes:
    if isinstance(table, CommentTable):
        comments = list(table.comments)
        if template is None:
            template = table.header
    else:
        comments = list(table)

    if template is None:
        raise CommentTableError("serialization requires an existing COMMENT.qcd template/header")
    if len(template) < QCD_RANGE_OFFSET:
        raise CommentTableError("COMMENT.qcd template/header too short")

    ranges, ordered = _ranges_for_comments(comments)
    if len(ranges) > 0xFFFF:
        raise CommentTableError("too many COMMENT.qcd ranges")

    header = bytearray(template[:QCD_RANGE_OFFSET])
    struct.pack_into("<H", header, QCD_RANGE_MARKER_OFFSET, QCD_RANGE_MARKER)
    struct.pack_into("<H", header, QCD_RANGE_COUNT_OFFSET, len(ranges))

    body = bytearray()
    for r in ranges:
        body += struct.pack("<HII", r.type_code, r.start, r.count)
    body += struct.pack("<I", 0)
    for i, item in enumerate(ordered):
        raw = item.text.encode("utf-16le") + b"\x00\x00"
        body += struct.pack("<I", len(item.text) + 1)
        body += raw
        if i + 1 < len(ordered):
            body += struct.pack("<I", 0)

    out = header + body
    struct.pack_into("<I", out, QCD_LENGTH_FIELD_OFFSET, len(out) - QCD_LENGTH_FIELD_OFFSET)
    return bytes(out)


def comments_to_csv(comments: Iterable[DeviceComment]) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["TIPO", "DISPOSITIVO", "LABEL", "DESCRIPCION", "USADO"])
    for item in comments:
        device = item.device.upper()
        w.writerow([device[0], device, item.text, "", "SI"])
    return buf.getvalue()


def comments_from_csv(text: str) -> list[DeviceComment]:
    if text.startswith("\ufeff"):
        text = text[1:]
    r = csv.DictReader(io.StringIO(text))
    if not r.fieldnames:
        raise CommentTableError("empty CSV")
    fields = {x.strip().upper(): x for x in r.fieldnames if x is not None}
    if "DISPOSITIVO" not in fields or "LABEL" not in fields:
        raise CommentTableError("CSV requires DISPOSITIVO and LABEL columns")
    out: list[DeviceComment] = []
    for row in r:
        device = (row.get(fields["DISPOSITIVO"]) or "").strip().upper()
        label = (row.get(fields["LABEL"]) or "").strip()
        used = (row.get(fields.get("USADO", "")) or "").strip().upper() if "USADO" in fields else "SI"
        if not device or not label or used in {"NO", "0", "FALSE"}:
            continue
        out.append(DeviceComment(device, label))
    return out
