from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .project import GXWProject, GXWError
from .ladder import LadderError
from .audit import audit_project_devices


def _write(path: str | Path, data: bytes | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8", newline="\n")
    else:
        p.write_bytes(data)


def cmd_info(args) -> int:
    p = GXWProject(args.gxw)
    report = p.validate()
    obj = {
        "file": str(Path(args.gxw).resolve()),
        "sha256": hashlib.sha256(p.raw).hexdigest(),
        "bytes": len(p.raw),
        "outer_streams": sorted(k for k, e in p.outer.paths.items() if e.type == 2),
        "logical_streams": len(p.logical),
        "programs": p.program_names(),
        "validation": report,
    }
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def cmd_list(args) -> int:
    p = GXWProject(args.gxw)
    for pid, item in sorted(p.logical.items()):
        print(f"{pid:3d}  {item.size:7d}  {item.md5_b64:24s}  {item.logical_name}")
    return 0


def cmd_export(args) -> int:
    p = GXWProject(args.gxw)
    text = p.export_program(args.program)
    if args.output:
        _write(args.output, text)
    else:
        print(text, end="")
    return 0


def cmd_export_all(args) -> int:
    p = GXWProject(args.gxw)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in p.program_names():
        text = p.export_program(name)
        path = out / f"{name}.gxtext.txt"
        _write(path, text)
        manifest[name] = {"file": path.name, "instructions": len(p.inspect_program(name))}
    _write(out / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"exported {len(manifest)} programs to {out}")
    return 0


def cmd_validate(args) -> int:
    p = GXWProject(args.gxw)
    report = p.validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def cmd_rebuild(args) -> int:
    p = GXWProject(args.gxw)
    data = p.roundtrip_copy()
    _write(args.output, data)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "validation": GXWProject(data).validate(),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_replace(args) -> int:
    p = GXWProject(args.gxw)
    source = Path(args.source).read_text(encoding="utf-8")
    data = p.replace_program_source(args.program, source, update_res=not args.pou_only)
    _write(args.output, data)
    check = GXWProject(data)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "program": args.program,
        "updated_res": not args.pou_only,
        "validation": check.validate(),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_export_labels(args) -> int:
    p = GXWProject(args.gxw)
    text = p.export_device_comments_csv()
    if args.output:
        _write(args.output, text)
    else:
        print(text, end="")
    return 0


def cmd_replace_labels(args) -> int:
    p = GXWProject(args.gxw)
    source = Path(args.csv).read_text(encoding="utf-8-sig")
    data = p.replace_device_comments_csv(source)
    _write(args.output, data)
    check = GXWProject(data)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "device_comments": len(check.device_comments()),
        "validation": check.validate(),
    }, ensure_ascii=False, indent=2))
    return 0



def cmd_audit_devices(args) -> int:
    p = GXWProject(args.gxw)
    report = audit_project_devices(p, external_devices=args.external)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 3


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="gxw-tool",
        description="Read, validate, export and conservatively rewrite GX Works2 .gxw ordinary Ladder projects.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="show project/container information")
    p.add_argument("gxw")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("list", help="list resolved logical project streams")
    p.add_argument("gxw")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("export", help="decode one Program.pou to GX-Text-Writer bracket source")
    p.add_argument("gxw")
    p.add_argument("program", help="program base name, e.g. AUTO")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("export-all", help="decode every supported ordinary Ladder program")
    p.add_argument("gxw")
    p.add_argument("output_dir")
    p.set_defaults(func=cmd_export_all)

    p = sub.add_parser("validate", help="validate CFB, history MD5/size, token grammar and .res copies")
    p.add_argument("gxw")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("rebuild", help="losslessly rebuild both CFB layers and verify logical payload identity")
    p.add_argument("gxw")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=cmd_rebuild)

    p = sub.add_parser("replace-program", help="compile supported bracket source and replace one program")
    p.add_argument("gxw")
    p.add_argument("program")
    p.add_argument("source")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--pou-only", action="store_true", help="do not update paired .res token copies")
    p.set_defaults(func=cmd_replace)

    p = sub.add_parser("export-labels", help="export GX Works2 device comments (the table used as labels in this project) to CSV")
    p.add_argument("gxw")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_export_labels)

    p = sub.add_parser("replace-labels", help="replace COMMENT.qcd device-comment table from canonical CSV")
    p.add_argument("gxw")
    p.add_argument("csv", help="CSV with DISPOSITIVO and LABEL columns; Estampadora canonical CSV is accepted")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=cmd_replace_labels)


    p = sub.add_parser("audit-devices", help="audit device reads/writers across all Ladder programs")
    p.add_argument("gxw")
    p.add_argument(
        "--external",
        action="append",
        default=[],
        help="device intentionally written outside Ladder (repeatable), e.g. --external M100",
    )
    p.set_defaults(func=cmd_audit_devices)

    return ap


def main(argv=None) -> int:
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        return args.func(args)
    except (GXWError, LadderError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
