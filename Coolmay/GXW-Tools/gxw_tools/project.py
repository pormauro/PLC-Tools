from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, Mapping

from .cfb import CompoundFile, CFBError
from .comments import (
    CommentTableError, DeviceComment, comments_from_csv, comments_to_csv,
    parse_comment_qcd, serialize_comment_qcd,
)
from .ladder import (
    LadderError,
    compile_bracket_source,
    decode_program,
    program_pou_token_stream,
    replace_program_pou_tokens,
    replace_res_token_copies,
    to_gx_text_writer,
)


class GXWError(ValueError):
    pass


@dataclass(frozen=True)
class LogicalStream:
    projectdata_id: int
    logical_name: str
    stream_path: str
    size: int
    md5_b64: str


class GXWProject:
    """Reader/writer for the GX Works2 ordinary-Ladder layout validated here."""

    def __init__(self, source: bytes | str | Path):
        self.path = Path(source) if isinstance(source, (str, Path)) else None
        self.raw = self.path.read_bytes() if self.path else bytes(source)
        self.outer = CompoundFile(self.raw)
        try:
            self.history_raw = self.outer.read_stream("history.xml")
            self.projectdatalist_raw = self.outer.read_stream("projectdatalist.xml")
            self.hdb_raw = self.outer.read_stream("_hdb")
        except Exception as exc:
            raise GXWError(f"GXW required stream missing: {exc}") from exc
        self.hdb = CompoundFile(self.hdb_raw)
        self.logical = self._resolve_logical_streams()
        self.by_name = {x.logical_name: x for x in self.logical.values()}

    def _resolve_logical_streams(self) -> Dict[int, LogicalStream]:
        try:
            root = ET.fromstring(self.history_raw)
        except ET.ParseError as exc:
            raise GXWError(f"history.xml parse failure: {exc}") from exc
        records: Dict[int, LogicalStream] = {}
        for row in root.iter():
            fields = {child.tag.split("}")[-1]: (child.text or "") for child in list(row)}
            if "iProjectdataID" not in fields or "szProjectdataName" not in fields:
                continue
            try:
                pid = int(fields["iProjectdataID"])
            except ValueError:
                continue
            path = str(pid)
            if path not in self.hdb.paths or self.hdb.paths[path].type != 2:
                continue
            raw = self.hdb.read_stream(path)
            records[pid] = LogicalStream(
                projectdata_id=pid,
                logical_name=fields["szProjectdataName"],
                stream_path=path,
                size=len(raw),
                md5_b64=fields.get("szMD5val", ""),
            )
        if not records:
            raise GXWError("no logical streams resolved from history.xml")
        return records

    @staticmethod
    def md5_b64(data: bytes) -> str:
        return base64.b64encode(hashlib.md5(data).digest()).decode("ascii")

    def logical_bytes(self, logical_name: str) -> bytes:
        if logical_name not in self.by_name:
            raise GXWError(f"logical stream not found: {logical_name}")
        return self.hdb.read_stream(self.by_name[logical_name].stream_path)

    def program_names(self) -> list[str]:
        return sorted(name[: -len(".Program.pou")] for name in self.by_name if name.endswith(".Program.pou"))

    def export_program(self, program: str) -> str:
        logical = program if program.endswith(".Program.pou") else f"{program}.Program.pou"
        tokens = program_pou_token_stream(self.logical_bytes(logical))
        return to_gx_text_writer(decode_program(tokens))

    def inspect_program(self, program: str):
        logical = program if program.endswith(".Program.pou") else f"{program}.Program.pou"
        tokens = program_pou_token_stream(self.logical_bytes(logical))
        return decode_program(tokens)

    def validate(self) -> dict:
        problems: list[str] = []
        checked = 0
        for pid, item in sorted(self.logical.items()):
            raw = self.hdb.read_stream(item.stream_path)
            checked += 1
            if item.size != len(raw):
                problems.append(f"{item.logical_name}: history size {item.size} != stream size {len(raw)}")
            calc = self.md5_b64(raw)
            if item.md5_b64 and item.md5_b64 != calc:
                problems.append(f"{item.logical_name}: history MD5 mismatch")
        for name in self.program_names():
            try:
                pou = self.logical_bytes(f"{name}.Program.pou")
                tokens = program_pou_token_stream(pou)
                decode_program(tokens)
                res_name = f"{name}.res"
                if res_name in self.by_name:
                    res = self.logical_bytes(res_name)
                    if res.count(tokens) != 2:
                        problems.append(f"{name}: .res does not contain exactly two Program.pou token copies")
            except (GXWError, LadderError) as exc:
                problems.append(f"{name}: {exc}")
        if "COMMENT.qcd" in self.by_name:
            try:
                parse_comment_qcd(self.logical_bytes("COMMENT.qcd"))
            except CommentTableError as exc:
                problems.append(f"COMMENT.qcd: {exc}")
        return {
            "ok": not problems,
            "logical_streams_checked": checked,
            "programs_checked": len(self.program_names()),
            "problems": problems,
        }

    def device_comments(self) -> list[DeviceComment]:
        if "COMMENT.qcd" not in self.by_name:
            raise GXWError("COMMENT.qcd not found")
        try:
            return list(parse_comment_qcd(self.logical_bytes("COMMENT.qcd")).comments)
        except CommentTableError as exc:
            raise GXWError(f"COMMENT.qcd parse failure: {exc}") from exc

    def export_device_comments_csv(self) -> str:
        return comments_to_csv(self.device_comments())

    def _replace_logical_payloads(self, changes_by_name: Mapping[str, bytes]) -> bytes:
        if not changes_by_name:
            return self.raw
        missing = [name for name in changes_by_name if name not in self.by_name]
        if missing:
            raise GXWError("logical stream(s) not found: " + ", ".join(missing))
        changes_by_pid = {
            self.by_name[name].projectdata_id: bytes(data) for name, data in changes_by_name.items()
        }
        hdb_replacements = {str(pid): data for pid, data in changes_by_pid.items()}
        new_hdb = self.hdb.rebuild(hdb_replacements)
        new_history = self._patch_history(changes_by_pid)
        new_outer = self.outer.rebuild({"_hdb": new_hdb, "history.xml": new_history})

        check = GXWProject(new_outer)
        report = check.validate()
        if not report["ok"]:
            raise GXWError("generated GXW failed validation: " + "; ".join(report["problems"]))
        changed = set(changes_by_name)
        for name in self.by_name:
            if name in changed:
                continue
            if check.logical_bytes(name) != self.logical_bytes(name):
                raise GXWError(f"unexpected mutation of untouched logical stream: {name}")
        return new_outer

    def replace_device_comments(self, comments: Iterable[DeviceComment]) -> bytes:
        if "COMMENT.qcd" not in self.by_name:
            raise GXWError("COMMENT.qcd not found")
        old = self.logical_bytes("COMMENT.qcd")
        try:
            parsed = parse_comment_qcd(old)
            new_qcd = serialize_comment_qcd(list(comments), template=parsed.header)
            parse_comment_qcd(new_qcd)
        except CommentTableError as exc:
            raise GXWError(f"COMMENT.qcd write failure: {exc}") from exc
        return self._replace_logical_payloads({"COMMENT.qcd": new_qcd})

    def replace_device_comments_csv(self, csv_text: str) -> bytes:
        try:
            comments = comments_from_csv(csv_text)
        except CommentTableError as exc:
            raise GXWError(f"label CSV parse failure: {exc}") from exc
        return self.replace_device_comments(comments)

    def _patch_history(self, changes: Mapping[int, bytes]) -> bytes:
        text = self.history_raw.decode("utf-8")
        for pid, new_data in changes.items():
            item = self.logical[pid]
            matches = []
            for m in re.finditer(r"<D_History\b[^>]*>.*?</D_History>", text, re.S):
                block = m.group(0)
                if (f"<iProjectdataID>{pid}</iProjectdataID>" in block
                        and f"<szProjectdataName>{item.logical_name}</szProjectdataName>" in block):
                    matches.append(m)
            if len(matches) != 1:
                raise GXWError(
                    f"history current row expected once for {item.logical_name}, found {len(matches)}"
                )
            m = matches[0]
            block = m.group(0)
            block2, n1 = re.subn(
                r"<iFileSize>\d+</iFileSize>",
                f"<iFileSize>{len(new_data)}</iFileSize>",
                block,
                count=1,
            )
            md5 = self.md5_b64(new_data)
            block2, n2 = re.subn(
                r"<szMD5val>.*?</szMD5val>|<szMD5val\s*/>",
                f"<szMD5val>{md5}</szMD5val>",
                block2,
                count=1,
                flags=re.S,
            )
            if n1 != 1 or n2 != 1:
                raise GXWError(f"history metadata fields missing/ambiguous for {item.logical_name}")
            text = text[: m.start()] + block2 + text[m.end() :]
        return text.encode("utf-8")

    def replace_program_tokens(self, program: str, new_tokens: bytes, *, update_res: bool = True) -> bytes:
        base = program[:-len(".Program.pou")] if program.endswith(".Program.pou") else program
        pou_name = f"{base}.Program.pou"
        res_name = f"{base}.res"
        if pou_name not in self.by_name:
            raise GXWError(f"program not found: {base}")
        old_pou = self.logical_bytes(pou_name)
        old_tokens = program_pou_token_stream(old_pou)
        new_pou = replace_program_pou_tokens(old_pou, new_tokens)
        changes_by_name: Dict[str, bytes] = {pou_name: new_pou}
        if update_res:
            if res_name not in self.by_name:
                raise GXWError(f"paired compiled resource missing: {res_name}")
            old_res = self.logical_bytes(res_name)
            changes_by_name[res_name] = replace_res_token_copies(old_res, old_tokens, new_tokens)

        return self._replace_logical_payloads(changes_by_name)

    def replace_program_source(self, program: str, bracket_source: str, *, update_res: bool = True) -> bytes:
        tokens = compile_bracket_source(bracket_source, add_end=True)
        return self.replace_program_tokens(program, tokens, update_res=update_res)

    def roundtrip_copy(self) -> bytes:
        """Rebuild both CFB layers without changing any logical payload."""
        new_hdb = self.hdb.rebuild()
        new_outer = self.outer.rebuild({"_hdb": new_hdb})
        check = GXWProject(new_outer)
        for name in self.by_name:
            if check.logical_bytes(name) != self.logical_bytes(name):
                raise GXWError(f"round-trip changed logical stream {name}")
        return new_outer
