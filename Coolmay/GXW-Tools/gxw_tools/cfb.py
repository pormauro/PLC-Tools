from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Dict, Iterable, Mapping

MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
FREE = 0xFFFFFFFF
END = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
DIFSECT = 0xFFFFFFFC
NOSTREAM = 0xFFFFFFFF


class CFBError(ValueError):
    pass


@dataclass
class DirectoryEntry:
    id: int
    name: str
    type: int
    color: int
    left: int
    right: int
    child: int
    clsid: bytes
    state: int
    ctime: int
    mtime: int
    start: int
    size: int
    raw: bytes


class CompoundFile:
    """Minimal CFB/OLE reader plus deterministic rebuild writer.

    The writer preserves the original directory entries/tree and metadata, and
    only reallocates stream payloads. This is intentionally narrower than a
    general-purpose OLE editor, but it is ideal for GXW because we do not add or
    remove logical streams while patching a project.
    """

    def __init__(self, source: bytes | bytearray | memoryview | str | Path):
        if isinstance(source, (str, Path)):
            self.data = Path(source).read_bytes()
        else:
            self.data = bytes(source)
        if len(self.data) < 512 or self.data[:8] != MAGIC:
            raise CFBError("not a CFB/OLE compound file")

        self.header = bytearray(self.data[:512])
        h = self.header
        self.minor, self.major = struct.unpack_from("<HH", h, 0x18)
        self.byte_order = struct.unpack_from("<H", h, 0x1C)[0]
        self.sector_shift = struct.unpack_from("<H", h, 0x1E)[0]
        self.mini_sector_shift = struct.unpack_from("<H", h, 0x20)[0]
        self.sector_size = 1 << self.sector_shift
        self.mini_sector_size = 1 << self.mini_sector_shift
        if self.major != 3 or self.sector_size != 512:
            raise CFBError(
                f"writer currently supports CFB v3/512-byte sectors; got v{self.major}/{self.sector_size}"
            )
        if self.byte_order != 0xFFFE:
            raise CFBError("unsupported CFB byte order")

        self.num_dir_sectors = struct.unpack_from("<I", h, 0x28)[0]
        self.num_fat_sectors = struct.unpack_from("<I", h, 0x2C)[0]
        self.first_dir_sector = struct.unpack_from("<I", h, 0x30)[0]
        self.mini_cutoff = struct.unpack_from("<I", h, 0x38)[0]
        self.first_mini_fat_sector = struct.unpack_from("<I", h, 0x3C)[0]
        self.num_mini_fat_sectors = struct.unpack_from("<I", h, 0x40)[0]
        self.first_difat_sector = struct.unpack_from("<I", h, 0x44)[0]
        self.num_difat_sectors = struct.unpack_from("<I", h, 0x48)[0]

        difat = list(struct.unpack_from("<109I", h, 0x4C))
        fat_ids = [x for x in difat if x != FREE]
        cur = self.first_difat_sector
        for _ in range(self.num_difat_sectors):
            if cur in (END, FREE) or cur >= self.sector_count:
                raise CFBError("broken DIFAT chain")
            vals = struct.unpack("<128I", self.sector(cur))
            fat_ids.extend(x for x in vals[:-1] if x != FREE)
            cur = vals[-1]
        self.fat_sector_ids = fat_ids[: self.num_fat_sectors]
        self.fat: list[int] = []
        for sid in self.fat_sector_ids:
            self.fat.extend(struct.unpack("<128I", self.sector(sid)))

        dir_bytes = self.read_chain(self.first_dir_sector)
        self.directory_raw_size = len(dir_bytes)
        self.dir: list[DirectoryEntry] = []
        for i in range(0, len(dir_bytes), 128):
            raw = dir_bytes[i : i + 128]
            if len(raw) < 128:
                break
            nlen = struct.unpack_from("<H", raw, 64)[0]
            name = raw[: max(0, nlen - 2)].decode("utf-16le", "replace") if nlen >= 2 else ""
            size = struct.unpack_from("<Q", raw, 120)[0] & 0xFFFFFFFF
            self.dir.append(
                DirectoryEntry(
                    id=i // 128,
                    name=name,
                    type=raw[66],
                    color=raw[67],
                    left=struct.unpack_from("<I", raw, 68)[0],
                    right=struct.unpack_from("<I", raw, 72)[0],
                    child=struct.unpack_from("<I", raw, 76)[0],
                    clsid=raw[80:96],
                    state=struct.unpack_from("<I", raw, 96)[0],
                    ctime=struct.unpack_from("<Q", raw, 100)[0],
                    mtime=struct.unpack_from("<Q", raw, 108)[0],
                    start=struct.unpack_from("<I", raw, 116)[0],
                    size=size,
                    raw=raw,
                )
            )
        self.root = next((e for e in self.dir if e.type == 5), None)
        if self.root is None:
            raise CFBError("missing root storage")

        self.minifat: list[int] = []
        if self.num_mini_fat_sectors and self.first_mini_fat_sector not in (FREE, END):
            mf_bytes = self.read_chain(
                self.first_mini_fat_sector, maxsectors=self.num_mini_fat_sectors
            )
            self.minifat = list(struct.unpack(f"<{len(mf_bytes)//4}I", mf_bytes))

        self.ministream = b""
        if self.root.size:
            self.ministream = self.read_chain(self.root.start)[: self.root.size]

        self.paths: Dict[str, DirectoryEntry] = {}
        self._walk_tree(self.root.child, "", set())

    @property
    def sector_count(self) -> int:
        return max(0, (len(self.data) - 512) // self.sector_size)

    def sector(self, sid: int) -> bytes:
        if sid < 0 or sid >= self.sector_count:
            raise CFBError(f"sector out of range: {sid}")
        off = (sid + 1) * self.sector_size
        return self.data[off : off + self.sector_size]

    @staticmethod
    def _chain_ids(start: int, fat: list[int], maxsectors: int | None = None) -> list[int]:
        if start in (END, FREE):
            return []
        out: list[int] = []
        seen: set[int] = set()
        cur = start
        while cur not in (END, FREE):
            if cur >= len(fat):
                raise CFBError(f"chain references FAT entry {cur}, FAT size={len(fat)}")
            if cur in seen:
                raise CFBError(f"cycle in CFB chain at sector {cur}")
            seen.add(cur)
            out.append(cur)
            if maxsectors is not None and len(out) >= maxsectors:
                break
            cur = fat[cur]
        return out

    def chain_ids(self, start: int, *, mini: bool = False, maxsectors: int | None = None) -> list[int]:
        return self._chain_ids(start, self.minifat if mini else self.fat, maxsectors)

    def read_chain(self, start: int, maxsectors: int | None = None) -> bytes:
        return b"".join(self.sector(i) for i in self.chain_ids(start, maxsectors=maxsectors))

    def read_stream(self, entry_or_path: DirectoryEntry | str) -> bytes:
        e = self.paths[entry_or_path] if isinstance(entry_or_path, str) else entry_or_path
        if e.type != 2:
            raise CFBError(f"{e.name!r} is not a stream")
        if e.size == 0:
            return b""
        if e.size < self.mini_cutoff:
            ids = self.chain_ids(e.start, mini=True)
            raw = b"".join(
                self.ministream[i * self.mini_sector_size : (i + 1) * self.mini_sector_size]
                for i in ids
            )
        else:
            raw = self.read_chain(e.start)
        return raw[: e.size]

    def stream_bytes_by_id(self, entry_id: int) -> bytes:
        return self.read_stream(self.dir[entry_id])

    def _tree_nodes(self, idx: int, seen: set[int]) -> list[int]:
        if idx == NOSTREAM or idx >= len(self.dir):
            return []
        if idx in seen:
            raise CFBError("cycle in directory red/black tree")
        seen.add(idx)
        e = self.dir[idx]
        return self._tree_nodes(e.left, seen) + [idx] + self._tree_nodes(e.right, seen)

    def _walk_tree(self, child: int, prefix: str, seen_storage: set[int]) -> None:
        for idx in self._tree_nodes(child, set()):
            e = self.dir[idx]
            p = (prefix + "/" + e.name).strip("/")
            self.paths[p] = e
            if e.type in (1, 5) and idx not in seen_storage:
                seen_storage.add(idx)
                self._walk_tree(e.child, p, seen_storage)

    def rebuild(self, replacements: Mapping[str | int, bytes] | None = None) -> bytes:
        """Rebuild the CFB while preserving the directory tree and all metadata.

        replacements keys may be stream paths or directory IDs. No streams
        are added/removed, which deliberately keeps GXW logical-object identity
        unchanged.
        """
        replacements = replacements or {}
        replace_by_id: Dict[int, bytes] = {}
        for key, value in replacements.items():
            if isinstance(key, str):
                if key not in self.paths:
                    raise CFBError(f"stream path not found: {key}")
                e = self.paths[key]
                if e.type != 2:
                    raise CFBError(f"path is not a stream: {key}")
                replace_by_id[e.id] = bytes(value)
            else:
                if key < 0 or key >= len(self.dir) or self.dir[key].type != 2:
                    raise CFBError(f"invalid stream directory id: {key}")
                replace_by_id[int(key)] = bytes(value)

        payloads: Dict[int, bytes] = {}
        for e in self.dir:
            if e.type == 2:
                payloads[e.id] = replace_by_id.get(e.id, self.read_stream(e))

        mini_fat: list[int] = []
        mini_blob = bytearray()
        stream_start: Dict[int, int] = {}
        stream_size: Dict[int, int] = {}
        for e in self.dir:
            if e.type != 2:
                continue
            data = payloads[e.id]
            stream_size[e.id] = len(data)
            if not data:
                stream_start[e.id] = END
                continue
            if len(data) < self.mini_cutoff:
                count = (len(data) + self.mini_sector_size - 1) // self.mini_sector_size
                first = len(mini_fat)
                stream_start[e.id] = first
                for j in range(count):
                    mini_fat.append(first + j + 1 if j + 1 < count else END)
                mini_blob.extend(data)
                mini_blob.extend(b"\x00" * (count * self.mini_sector_size - len(data)))

        regular: list[tuple[str, int | None, bytes]] = []
        for e in self.dir:
            if e.type != 2:
                continue
            data = payloads[e.id]
            if len(data) >= self.mini_cutoff:
                regular.append(("stream", e.id, data))
        if mini_blob:
            regular.append(("ministream", None, bytes(mini_blob)))

        dir_len = max(128, len(self.dir) * 128)
        dir_sector_count = (dir_len + self.sector_size - 1) // self.sector_size
        mini_fat_bytes_len = len(mini_fat) * 4
        mini_fat_sector_count = (
            (mini_fat_bytes_len + self.sector_size - 1) // self.sector_size
            if mini_fat_bytes_len
            else 0
        )

        regular_sector_counts = [
            (len(data) + self.sector_size - 1) // self.sector_size for _, _, data in regular
        ]
        nonfat_sectors = sum(regular_sector_counts) + dir_sector_count + mini_fat_sector_count
        fat_sector_count = 0
        while True:
            needed = (nonfat_sectors + fat_sector_count + 127) // 128
            if needed == fat_sector_count:
                break
            fat_sector_count = needed
        if fat_sector_count > 109:
            raise CFBError("rebuild would require DIFAT sectors; not supported by this conservative writer")

        total_sectors = nonfat_sectors + fat_sector_count
        fat = [FREE] * (fat_sector_count * 128)
        sectors = [bytearray(self.sector_size) for _ in range(total_sectors)]
        cursor = 0

        def alloc_chain(data: bytes) -> int:
            nonlocal cursor
            if not data:
                return END
            count = (len(data) + self.sector_size - 1) // self.sector_size
            first = cursor
            for i in range(count):
                sid = cursor + i
                chunk = data[i * self.sector_size : (i + 1) * self.sector_size]
                sectors[sid][: len(chunk)] = chunk
                fat[sid] = sid + 1 if i + 1 < count else END
            cursor += count
            return first

        root_ministream_start = END
        for kind, entry_id, data in regular:
            start = alloc_chain(data)
            if kind == "stream":
                assert entry_id is not None
                stream_start[entry_id] = start
            else:
                root_ministream_start = start

        dir_bytes = bytearray(dir_sector_count * self.sector_size)
        for e in self.dir:
            raw = bytearray(e.raw)
            if e.type == 2:
                struct.pack_into("<I", raw, 116, stream_start.get(e.id, END))
                struct.pack_into("<Q", raw, 120, stream_size.get(e.id, 0))
            elif e.type == 5:
                struct.pack_into("<I", raw, 116, root_ministream_start if mini_blob else END)
                struct.pack_into("<Q", raw, 120, len(mini_blob))
            dir_bytes[e.id * 128 : (e.id + 1) * 128] = raw
        first_dir_sector = alloc_chain(bytes(dir_bytes))

        if mini_fat:
            mf = list(mini_fat)
            mf.extend([FREE] * (mini_fat_sector_count * 128 - len(mf)))
            mf_bytes = struct.pack(f"<{len(mf)}I", *mf)
            first_mini_fat_sector = alloc_chain(mf_bytes)
        else:
            first_mini_fat_sector = END

        fat_sector_ids = list(range(cursor, cursor + fat_sector_count))
        for sid in fat_sector_ids:
            fat[sid] = FATSECT
        cursor += fat_sector_count
        if cursor != total_sectors:
            raise AssertionError((cursor, total_sectors))

        for j, sid in enumerate(fat_sector_ids):
            block = fat[j * 128 : (j + 1) * 128]
            sectors[sid][:] = struct.pack("<128I", *block)

        h = bytearray(self.header)
        struct.pack_into("<I", h, 0x28, 0)
        struct.pack_into("<I", h, 0x2C, fat_sector_count)
        struct.pack_into("<I", h, 0x30, first_dir_sector)
        struct.pack_into("<I", h, 0x38, self.mini_cutoff)
        struct.pack_into("<I", h, 0x3C, first_mini_fat_sector)
        struct.pack_into("<I", h, 0x40, mini_fat_sector_count)
        struct.pack_into("<I", h, 0x44, END)
        struct.pack_into("<I", h, 0x48, 0)
        for i in range(109):
            struct.pack_into("<I", h, 0x4C + 4 * i, fat_sector_ids[i] if i < len(fat_sector_ids) else FREE)

        result = bytes(h) + b"".join(bytes(s) for s in sectors)
        check = CompoundFile(result)
        for path, e in self.paths.items():
            if e.type != 2:
                continue
            expected = payloads[e.id]
            got = check.read_stream(path)
            if got != expected:
                raise CFBError(f"rebuild validation mismatch for stream {path}")
        return result
