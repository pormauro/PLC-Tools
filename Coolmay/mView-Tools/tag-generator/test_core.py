from mview_tag import TagRecord, build_tag_bytes, parse_tag_bytes, crc16_modbus
import struct
import zlib

records = [
    TagRecord("STATE", "D0", "Estado principal", "900", "0"),
    TagRecord("PEDAL", "X5", "Pedal", "1", "0"),
]

raw = build_tag_bytes(records, "Estampadora")
assert raw[:4] == b"vxtg"

payload = zlib.decompress(raw[4:])
assert struct.unpack_from("<I", payload, 4)[0] == len(payload) - 8
assert struct.unpack_from("<H", payload, len(payload)-2)[0] == crc16_modbus(payload[8:-2])

parsed = parse_tag_bytes(raw)
assert parsed.group_name == "Estampadora"
assert parsed.records == tuple(records)

print("TAG CORE TEST: PASS")
