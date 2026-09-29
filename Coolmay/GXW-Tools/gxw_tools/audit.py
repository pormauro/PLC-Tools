from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable, Mapping, Sequence

from .ladder import Instruction

_DEVICE_RE = re.compile(r"^[MXYDTC]\\d+$", re.IGNORECASE)
_CONTACT_MNEMONICS = {"LD", "LDI", "AND", "ANDI", "OR", "ORI"}
_COIL_WRITERS = {"OUT", "SET", "RST", "PLS", "TIMER", "COUNTER"}
_DESTINATION_INDEX = {
    "MOV": 1,
    "DMOV": 1,
    "BMOV": 1,
    "DADD": 2,
}


def _is_device(value: str) -> bool:
    return bool(_DEVICE_RE.fullmatch(value))


def _read_operands(ins: Instruction) -> tuple[str, ...]:
    m = ins.mnemonic.upper()
    ops = ins.operands
    if m in _CONTACT_MNEMONICS:
        return tuple(o for o in ops if _is_device(o))
    if m.startswith((
        "LD=", "LD<", "LD>", "LD<>", "LD<=", "LD>=",
        "LDD=", "LDD<", "LDD>", "LDD<>", "LDD<=", "LDD>=",
        "AND=", "AND<", "AND>", "AND<>", "AND<=", "AND>=",
        "ANDD=", "ANDD<", "ANDD>", "ANDD<>", "ANDD<=", "ANDD>=",
    )):
        return tuple(o for o in ops if _is_device(o))
    if m in {"MOV", "DMOV"}:
        return tuple(o for o in ops[:1] if _is_device(o))
    if m == "BMOV":
        return tuple(o for o in (ops[0], ops[2]) if _is_device(o)) if len(ops) >= 3 else ()
    if m == "DADD":
        return tuple(o for o in ops[:2] if _is_device(o))
    return ()


def _written_operand(ins: Instruction) -> str | None:
    m = ins.mnemonic.upper()
    ops = ins.operands
    if not ops:
        return None
    if m in _COIL_WRITERS:
        return ops[0] if _is_device(ops[0]) else None
    if m in _DESTINATION_INDEX:
        i = _DESTINATION_INDEX[m]
        return ops[i] if len(ops) > i and _is_device(ops[i]) else None
    if m == "ZRST":
        # Range write: endpoints are intentionally not treated as reads.
        return None
    return None


def analyze_instructions(
    programs: Mapping[str, Sequence[Instruction]],
    *,
    external_devices: Iterable[str] = (),
    missing_families: Iterable[str] = ("M", "T", "C", "Y"),
) -> dict:
    external = {d.upper() for d in external_devices}
    families = {f.upper() for f in missing_families}
    reads: dict[str, set[str]] = defaultdict(set)
    writes: dict[str, set[str]] = defaultdict(set)
    coil_writes: dict[str, set[str]] = defaultdict(set)

    for program, instructions in programs.items():
        for ins in instructions:
            for dev in _read_operands(ins):
                reads[dev.upper()].add(program)
            w = _written_operand(ins)
            if w:
                w = w.upper()
                writes[w].add(program)
                if ins.mnemonic.upper() in _COIL_WRITERS:
                    coil_writes[w].add(program)

    missing = {
        dev: sorted(progs)
        for dev, progs in sorted(reads.items())
        if dev[0] in families and dev not in writes and dev not in external
    }
    multiple_coil_writers = {
        dev: sorted(progs)
        for dev, progs in sorted(coil_writes.items())
        if len(progs) > 1
    }
    return {
        "programs": len(programs),
        "read_devices": len(reads),
        "written_devices": len(writes),
        "read_without_ladder_writer": missing,
        "multiple_coil_writers": multiple_coil_writers,
        "ok": not missing and not multiple_coil_writers,
    }


def audit_project_devices(project, *, external_devices: Iterable[str] = ()) -> dict:
    programs = {name: project.inspect_program(name) for name in project.program_names()}
    return analyze_instructions(programs, external_devices=external_devices)
