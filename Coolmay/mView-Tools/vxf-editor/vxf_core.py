from __future__ import annotations

"""Safe parser/writer for the outer mView .vxf container.

CRITICAL WRITE INVARIANT
========================
Every mutation inside the variable-length project block identified by marker
0x10000004 MUST rebuild that block as:

    marker (uint32 LE)
    size   (uint32 LE)
    body
    crc16_modbus(body) (uint16 LE)

The stored size includes the trailing 2-byte CRC.

A previous writer bug updated an inner scene/object and its local CRC but left
this outer size/CRC stale. mView 1.39.02 then rejected an otherwise valid
TK6043FH project with the misleading dialog:

    "HMI models are not supported, can't open!"

All variable-length VXF edits must go through mutate_project_block().
Do not splice bytes directly into the decompressed VXF payload.
"""

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib
from typing import Callable

MAGIC = b"vxpm"
SIGNATURE = b"VX-HMI, File Format"
PROJECT_BLOCK_MARKER = 0x10000004
PROJECT_BLOCK_MARKER_BYTES = struct.pack("<I", PROJECT_BLOCK_MARKER)


class VXFError(ValueError):
    pass


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF


@dataclass(frozen=True)
class ProjectBlock:
    marker_offset: int
    content_offset: int
    content_end: int
    stored_size: int
    stored_crc: int

    @property
    def body_end(self) -> int:
        return self.content_end - 2


@dataclass(frozen=True)
class VXFDocument:
    payload: bytes
    project_block: ProjectBlock

    @property
    def project_body(self) -> bytes:
        block = self.project_block
        return self.payload[block.content_offset:block.body_end]

    @property
    def suffix(self) -> bytes:
        return self.payload[self.project_block.content_end:]


def decompress_vxf(raw: bytes) -> bytes:
    if not raw.startswith(MAGIC):
        raise VXFError("invalid VXF magic: expected vxpm")
    try:
        payload = zlib.decompress(raw[len(MAGIC):])
    except zlib.error as exc:
        raise VXFError("invalid VXF zlib stream") from exc
    if not payload.startswith(SIGNATURE):
        raise VXFError("invalid VXF signature: expected 'VX-HMI, File Format'")
    return payload


def _unique_marker_offset(payload: bytes) -> int:
    hits: list[int] = []
    pos = 0
    while True:
        pos = payload.find(PROJECT_BLOCK_MARKER_BYTES, pos)
        if pos < 0:
            break
        hits.append(pos)
        pos += 1
    if len(hits) != 1:
        raise VXFError(
            f"expected exactly one project block marker "
            f"0x{PROJECT_BLOCK_MARKER:08X}, found {len(hits)}"
        )
    return hits[0]


def locate_project_block(payload: bytes, *, verify_crc: bool = True) -> ProjectBlock:
    marker_offset = _unique_marker_offset(payload)
    size_offset = marker_offset + 4
    if size_offset + 4 > len(payload):
        raise VXFError("truncated VXF project block size")

    stored_size = struct.unpack_from("<I", payload, size_offset)[0]
    if stored_size < 2:
        raise VXFError(f"invalid VXF project block size: {stored_size}")

    content_offset = marker_offset + 8
    content_end = content_offset + stored_size
    if content_end > len(payload):
        raise VXFError(
            f"project block exceeds payload: end={content_end}, "
            f"payload={len(payload)}"
        )

    stored_crc = struct.unpack_from("<H", payload, content_end - 2)[0]
    if verify_crc:
        calculated_crc = crc16_modbus(payload[content_offset:content_end - 2])
        if stored_crc != calculated_crc:
            raise VXFError(
                "project block CRC mismatch: "
                f"stored=0x{stored_crc:04X}, "
                f"calculated=0x{calculated_crc:04X}"
            )

    return ProjectBlock(
        marker_offset=marker_offset,
        content_offset=content_offset,
        content_end=content_end,
        stored_size=stored_size,
        stored_crc=stored_crc,
    )


def parse_vxf(raw: bytes, *, verify_crc: bool = True) -> VXFDocument:
    payload = decompress_vxf(raw)
    block = locate_project_block(payload, verify_crc=verify_crc)
    return VXFDocument(payload=payload, project_block=block)


def build_project_block(body: bytes) -> bytes:
    """Serialize marker + size + body + CRC.

    The stored size includes the trailing CRC. This matches the mView 1.39.02
    TK6043FH projects used to validate the editor.
    """
    body = bytes(body)
    crc = crc16_modbus(body)
    content = body + struct.pack("<H", crc)
    return (
        PROJECT_BLOCK_MARKER_BYTES
        + struct.pack("<I", len(content))
        + content
    )


def replace_project_body(payload: bytes, new_body: bytes) -> bytes:
    """Replace the 0x10000004 body and repair outer size/CRC automatically."""
    block = locate_project_block(payload, verify_crc=True)
    return (
        payload[:block.marker_offset]
        + build_project_block(bytes(new_body))
        + payload[block.content_end:]
    )


def mutate_project_block(
    raw: bytes,
    mutator: Callable[[bytes], bytes],
    *,
    compression_level: int = 6,
) -> bytes:
    """Safely mutate the variable-length mView project block.

    The callback receives the project block body WITHOUT its trailing CRC and
    must return the new body. The writer then recalculates:

    - 0x10000004 stored size;
    - 0x10000004 CRC16/MODBUS;
    - zlib stream of the complete VXF.

    This is the mandatory write path for scene/object edits.
    """
    doc = parse_vxf(raw, verify_crc=True)
    new_body = mutator(doc.project_body)
    if not isinstance(new_body, (bytes, bytearray)):
        raise TypeError("VXF mutator must return bytes")

    new_payload = replace_project_body(doc.payload, bytes(new_body))

    # Fail closed before emitting a VXF.
    locate_project_block(new_payload, verify_crc=True)

    result = MAGIC + zlib.compress(new_payload, level=compression_level)

    # Reopen exactly what we are about to return.
    parse_vxf(result, verify_crc=True)
    return result


def validate_vxf(raw: bytes) -> ProjectBlock:
    """Validate VXF magic/zlib/signature and the 0x10000004 size/CRC."""
    return parse_vxf(raw, verify_crc=True).project_block


def read_vxf(path: str | Path) -> VXFDocument:
    return parse_vxf(Path(path).read_bytes(), verify_crc=True)


def write_mutated_vxf(
    source: str | Path,
    destination: str | Path,
    mutator: Callable[[bytes], bytes],
    *,
    compression_level: int = 6,
) -> None:
    source = Path(source)
    destination = Path(destination)
    destination.write_bytes(
        mutate_project_block(
            source.read_bytes(),
            mutator,
            compression_level=compression_level,
        )
    )
    validate_vxf(destination.read_bytes())


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate mView VXF outer container")
    parser.add_argument("file")
    args = parser.parse_args()

    path = Path(args.file)
    block = validate_vxf(path.read_bytes())
    print(
        "OK "
        f"file={path} "
        f"project_block_offset=0x{block.marker_offset:X} "
        f"size={block.stored_size} "
        f"crc=0x{block.stored_crc:04X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
