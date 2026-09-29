from __future__ import annotations

"""Parser/serializer del formato .sca de mView."""

from dataclasses import dataclass, field
import copy
from pathlib import Path
import struct
import zlib

MAGIC = b"vxsa"


class SCAError(ValueError):
    pass


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF


def encode_qstring(text: str) -> bytes:
    value = str(text) + "\x00"
    return struct.pack("<I", len(value)) + value.encode("utf-16le")


def decode_qstring(buf: bytes, offset: int) -> tuple[str, int]:
    if offset + 4 > len(buf):
        raise SCAError("Fin inesperado leyendo longitud QString.")
    count = struct.unpack_from("<I", buf, offset)[0]
    offset += 4
    nbytes = count * 2
    if offset + nbytes > len(buf):
        raise SCAError("Fin inesperado leyendo QString.")
    try:
        value = buf[offset:offset+nbytes].decode("utf-16le")
    except UnicodeDecodeError as exc:
        raise SCAError("QString UTF-16LE inválida.") from exc
    offset += nbytes
    if value.endswith("\x00"):
        value = value[:-1]
    return value, offset


def scan_qstrings(buf: bytes, *, max_chars: int = 512) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for off in range(0, max(0, len(buf) - 6)):
        count = struct.unpack_from("<I", buf, off)[0]
        if not (1 <= count <= max_chars):
            continue
        end = off + 4 + count * 2
        if end > len(buf):
            continue
        raw = buf[off+4:end]
        if not raw.endswith(b"\x00\x00"):
            continue
        try:
            text = raw.decode("utf-16le")[:-1]
        except UnicodeDecodeError:
            continue
        if text and all(ch.isprintable() or ch in "\t\r\n" for ch in text):
            out.append((off, count, text))
    return out


def replace_qstrings(buf: bytes, replacements: dict[str, str]) -> bytes:
    hits = [
        (off, count, text)
        for off, count, text in scan_qstrings(buf)
        if text in replacements
    ]
    result = bytearray(buf)
    for off, count, old in sorted(hits, reverse=True):
        old_end = off + 4 + count * 2
        result[off:old_end] = encode_qstring(replacements[old])
    return bytes(result)


def set_rect(body: bytes, rect: tuple[int, int, int, int]) -> bytes:
    if len(body) < 20:
        raise SCAError("Objeto demasiado corto para contener rectángulo.")
    out = bytearray(body)
    struct.pack_into("<iiii", out, 4, *rect)
    return bytes(out)


def get_rect(body: bytes) -> tuple[int, int, int, int]:
    if len(body) < 20:
        raise SCAError("Objeto demasiado corto para contener rectángulo.")
    return struct.unpack_from("<iiii", body, 4)


@dataclass
class SCAObject:
    header_a: int
    header_b: int
    body: bytes

    def clone(self) -> "SCAObject":
        return copy.deepcopy(self)

    @property
    def strings(self) -> list[str]:
        return [text for _, _, text in scan_qstrings(self.body)]

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return get_rect(self.body)

    def set_rect(self, rect: tuple[int, int, int, int]) -> "SCAObject":
        self.body = set_rect(self.body, rect)
        return self

    def replace_strings(self, mapping: dict[str, str]) -> "SCAObject":
        self.body = replace_qstrings(self.body, mapping)
        return self

    def set_nav_target(self, scene_number_1_based: int) -> "SCAObject":
        if self.header_a != 1 or self.header_b != 2:
            raise SCAError("set_nav_target sólo es válido para botón de escena (1,2).")
        if len(self.body) < 4:
            raise SCAError("Objeto de navegación demasiado corto.")
        out = bytearray(self.body)
        struct.pack_into("<I", out, len(out)-4, int(scene_number_1_based))
        self.body = bytes(out)
        return self

    def to_bytes(self) -> bytes:
        payload = self.body + struct.pack("<H", crc16_modbus(self.body))
        return struct.pack("<HHI", self.header_a, self.header_b, len(payload)) + payload


@dataclass
class SCAScene:
    name: str
    meta: bytes
    objects: list[SCAObject] = field(default_factory=list)

    def clone(self) -> "SCAScene":
        return copy.deepcopy(self)

    def block_bytes(self) -> bytes:
        block = bytearray(struct.pack("<I", len(self.objects)))
        for obj in self.objects:
            block += obj.to_bytes()
        block += struct.pack("<H", crc16_modbus(block))
        return bytes(block)

    def to_bytes(self) -> bytes:
        block = self.block_bytes()
        return encode_qstring(self.name) + self.meta + struct.pack("<I", len(block)) + block


@dataclass
class SCAProject:
    prefix32: bytes
    group_name: str
    group_tail10: bytes
    scenes: list[SCAScene]

    def clone(self) -> "SCAProject":
        return copy.deepcopy(self)

    def payload_bytes(self) -> bytes:
        if len(self.prefix32) != 32:
            raise SCAError("prefix32 debe tener exactamente 32 bytes.")
        if len(self.group_tail10) != 10:
            raise SCAError("group_tail10 debe tener exactamente 10 bytes.")

        payload = bytearray(self.prefix32)
        payload += encode_qstring(self.group_name)
        payload += self.group_tail10
        payload += struct.pack("<I", len(self.scenes))
        for scene in self.scenes:
            payload += scene.to_bytes()

        final_len = len(payload) + 2
        struct.pack_into("<I", payload, 4, final_len - 8)
        payload += struct.pack("<H", crc16_modbus(payload[8:]))
        return bytes(payload)

    def build(self, *, compression_level: int = 6) -> bytes:
        return MAGIC + zlib.compress(self.payload_bytes(), level=compression_level)

    def write(self, path: str | Path) -> None:
        Path(path).write_bytes(self.build())

    def validate(self) -> None:
        parsed = parse_sca_bytes(self.build())
        if parsed.group_name != self.group_name:
            raise SCAError("Round-trip: group_name inconsistente.")
        if len(parsed.scenes) != len(self.scenes):
            raise SCAError("Round-trip: cantidad de escenas inconsistente.")


def parse_sca_bytes(raw: bytes) -> SCAProject:
    if not raw.startswith(MAGIC):
        raise SCAError("Magic inválido: el archivo no empieza con vxsa.")

    try:
        payload = zlib.decompress(raw[4:])
    except zlib.error as exc:
        raise SCAError("Stream zlib inválido.") from exc

    if len(payload) < 40:
        raise SCAError("Payload demasiado corto.")

    stored_size = struct.unpack_from("<I", payload, 4)[0]
    if stored_size != len(payload) - 8:
        raise SCAError(
            f"Size global inválido: guardado={stored_size}, calculado={len(payload)-8}."
        )

    stored_crc = struct.unpack_from("<H", payload, len(payload)-2)[0]
    calc_crc = crc16_modbus(payload[8:-2])
    if stored_crc != calc_crc:
        raise SCAError(
            f"CRC global inválido: guardado=0x{stored_crc:04X}, calculado=0x{calc_crc:04X}."
        )

    prefix32 = payload[:32]
    group_name, offset = decode_qstring(payload, 32)

    if offset + 14 > len(payload)-2:
        raise SCAError("Cabecera de grupo incompleta.")

    group_tail10 = payload[offset:offset+10]
    offset += 10
    scene_count = struct.unpack_from("<I", payload, offset)[0]
    offset += 4

    scenes: list[SCAScene] = []

    for scene_idx in range(scene_count):
        name, offset = decode_qstring(payload, offset)

        if offset + 38 > len(payload)-2:
            raise SCAError(f"Escena {scene_idx+1}: cabecera incompleta.")

        meta = payload[offset:offset+34]
        offset += 34
        block_size = struct.unpack_from("<I", payload, offset)[0]
        offset += 4

        if offset + block_size > len(payload)-2:
            raise SCAError(f"Escena {scene_idx+1}: block_size fuera de rango.")

        block = payload[offset:offset+block_size]
        offset += block_size

        if len(block) < 6:
            raise SCAError(f"Escena {scene_idx+1}: bloque demasiado corto.")

        scene_crc = struct.unpack_from("<H", block, len(block)-2)[0]
        scene_calc = crc16_modbus(block[:-2])
        if scene_crc != scene_calc:
            raise SCAError(
                f"Escena {scene_idx+1}: CRC inválido "
                f"(0x{scene_crc:04X} != 0x{scene_calc:04X})."
            )

        object_count = struct.unpack_from("<I", block, 0)[0]
        boff = 4
        objects: list[SCAObject] = []

        for obj_idx in range(object_count):
            if boff + 8 > len(block)-2:
                raise SCAError(
                    f"Escena {scene_idx+1}, objeto {obj_idx+1}: header incompleto."
                )
            a, b, object_size = struct.unpack_from("<HHI", block, boff)
            boff += 8

            if boff + object_size > len(block)-2:
                raise SCAError(
                    f"Escena {scene_idx+1}, objeto {obj_idx+1}: size fuera de rango."
                )

            obj_payload = block[boff:boff+object_size]
            boff += object_size

            if len(obj_payload) < 2:
                raise SCAError("Objeto sin CRC.")

            obj_crc = struct.unpack_from("<H", obj_payload, len(obj_payload)-2)[0]
            obj_body = obj_payload[:-2]
            obj_calc = crc16_modbus(obj_body)

            if obj_crc != obj_calc:
                raise SCAError(
                    f"Escena {scene_idx+1}, objeto {obj_idx+1}: CRC inválido "
                    f"(0x{obj_crc:04X} != 0x{obj_calc:04X})."
                )

            objects.append(SCAObject(a, b, obj_body))

        if boff != len(block)-2:
            raise SCAError(
                f"Escena {scene_idx+1}: quedaron {len(block)-2-boff} bytes "
                f"sin interpretar antes del CRC."
            )

        scenes.append(SCAScene(name, meta, objects))

    if offset != len(payload)-2:
        raise SCAError(
            f"Quedaron {len(payload)-2-offset} bytes sin interpretar antes del CRC global."
        )

    return SCAProject(prefix32, group_name, group_tail10, scenes)


def read_sca(path: str | Path) -> SCAProject:
    return parse_sca_bytes(Path(path).read_bytes())
