from __future__ import annotations

"""Parser/serializer determinístico para archivos .tag de mView."""

from dataclasses import dataclass
import struct
import zlib
from typing import Iterable

MAGIC = b"vxtg"
VERSION = 0x10000006
FORMAT_MARKER = 0x00000100


class MViewTagError(ValueError):
    pass


@dataclass(frozen=True)
class TagRecord:
    name: str
    address: str
    comment: str = ""
    maximum: str = ""
    minimum: str = ""

    def normalized(self) -> "TagRecord":
        return TagRecord(
            name=str(self.name).strip(),
            address=str(self.address).strip(),
            comment=str(self.comment or "").strip(),
            maximum=str(self.maximum or "").strip(),
            minimum=str(self.minimum or "").strip(),
        )


@dataclass(frozen=True)
class TagFile:
    group_name: str
    records: tuple[TagRecord, ...]
    version: int = VERSION
    format_marker: int = FORMAT_MARKER


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF


def _encode_qstring(text: str) -> bytes:
    value = str(text) + "\x00"
    return struct.pack("<I", len(value)) + value.encode("utf-16le")


def _read_u32(buf: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(buf):
        raise MViewTagError("Fin inesperado leyendo uint32.")
    return struct.unpack_from("<I", buf, offset)[0], offset + 4


def _decode_qstring(buf: bytes, offset: int) -> tuple[str, int]:
    count, offset = _read_u32(buf, offset)
    byte_count = count * 2
    if offset + byte_count > len(buf):
        raise MViewTagError("Fin inesperado leyendo QString.")
    try:
        value = buf[offset:offset+byte_count].decode("utf-16le")
    except UnicodeDecodeError as exc:
        raise MViewTagError("QString UTF-16LE inválida.") from exc
    offset += byte_count
    if value.endswith("\x00"):
        value = value[:-1]
    return value, offset


def validate_records(records: Iterable[TagRecord]) -> tuple[TagRecord, ...]:
    normalized = tuple(r.normalized() for r in records)
    if not normalized:
        raise MViewTagError("No hay tags para exportar.")

    names: dict[str, int] = {}
    for idx, rec in enumerate(normalized, start=1):
        if not rec.name:
            raise MViewTagError(f"Fila {idx}: TAG vacío.")
        if not rec.address:
            raise MViewTagError(f"Fila {idx}: dirección PLC vacía.")
        key = rec.name.casefold()
        if key in names:
            raise MViewTagError(
                f"TAG duplicado: {rec.name!r} en filas {names[key]} y {idx}."
            )
        names[key] = idx
    return normalized


def build_tag_bytes(
    records: Iterable[TagRecord],
    group_name: str = "Estampadora",
    *,
    version: int = VERSION,
    format_marker: int = FORMAT_MARKER,
    compression_level: int = 9,
) -> bytes:
    """Genera el archivo .tag completo listo para guardar."""
    group_name = str(group_name).strip()
    if not group_name:
        raise MViewTagError("El nombre del grupo no puede estar vacío.")

    records = validate_records(records)

    payload = bytearray()
    payload += struct.pack("<I", version)
    payload += b"\x00\x00\x00\x00"
    payload += struct.pack("<I", format_marker)
    payload += struct.pack("<I", 1)
    payload += _encode_qstring(group_name)
    payload += struct.pack("<I", len(records))

    for rec in records:
        payload += _encode_qstring(rec.name)
        payload += _encode_qstring(rec.address)
        payload += _encode_qstring(rec.comment)
        payload += _encode_qstring(rec.maximum)
        payload += _encode_qstring(rec.minimum)

    final_payload_size = len(payload) + 2
    struct.pack_into("<I", payload, 4, final_payload_size - 8)
    payload += struct.pack("<H", crc16_modbus(payload[8:]))

    return MAGIC + zlib.compress(bytes(payload), level=compression_level)


def write_tag(path: str, records: Iterable[TagRecord], group_name: str = "Estampadora") -> None:
    with open(path, "wb") as fh:
        fh.write(build_tag_bytes(records, group_name))


def parse_tag_bytes(data: bytes) -> TagFile:
    if not data.startswith(MAGIC):
        raise MViewTagError("Magic inválido: el archivo no comienza con 'vxtg'.")

    try:
        payload = zlib.decompress(data[len(MAGIC):])
    except zlib.error as exc:
        raise MViewTagError("Payload zlib inválido.") from exc

    if len(payload) < 18:
        raise MViewTagError("Payload demasiado corto.")

    version = struct.unpack_from("<I", payload, 0)[0]
    stored_size = struct.unpack_from("<I", payload, 4)[0]
    marker = struct.unpack_from("<I", payload, 8)[0]
    group_count = struct.unpack_from("<I", payload, 12)[0]

    if stored_size != len(payload) - 8:
        raise MViewTagError(
            f"Size inválido: archivo={stored_size}, calculado={len(payload)-8}."
        )

    stored_crc = struct.unpack_from("<H", payload, len(payload)-2)[0]
    calculated_crc = crc16_modbus(payload[8:-2])
    if stored_crc != calculated_crc:
        raise MViewTagError(
            f"CRC inválido: archivo=0x{stored_crc:04X}, calculado=0x{calculated_crc:04X}."
        )

    if group_count != 1:
        raise MViewTagError(
            f"Esta versión espera exactamente 1 grupo; archivo={group_count}."
        )

    offset = 16
    group_name, offset = _decode_qstring(payload, offset)
    count, offset = _read_u32(payload, offset)

    records: list[TagRecord] = []
    for _ in range(count):
        name, offset = _decode_qstring(payload, offset)
        address, offset = _decode_qstring(payload, offset)
        comment, offset = _decode_qstring(payload, offset)
        maximum, offset = _decode_qstring(payload, offset)
        minimum, offset = _decode_qstring(payload, offset)
        records.append(TagRecord(name, address, comment, maximum, minimum))

    if offset != len(payload) - 2:
        raise MViewTagError(
            f"Quedaron {len(payload)-2-offset} bytes sin interpretar antes del CRC."
        )

    return TagFile(
        group_name=group_name,
        records=tuple(records),
        version=version,
        format_marker=marker,
    )


def read_tag(path: str) -> TagFile:
    with open(path, "rb") as fh:
        return parse_tag_bytes(fh.read())


if __name__ == "__main__":
    sample = [
        TagRecord("STATE", "D0", "Estado principal", "900", "0"),
        TagRecord("READY", "M10", "Listo", "1", "0"),
    ]
    decoded = parse_tag_bytes(build_tag_bytes(sample, "Estampadora"))
    assert decoded.records == tuple(sample)
    print("mview_tag.py self-test: PASS")
