from __future__ import annotations

import argparse
from pathlib import Path
import zlib

from sca_core import parse_sca_bytes, read_sca


def test_roundtrip(path: Path):
    project = read_sca(path)
    project.validate()

    rebuilt = project.build()
    parsed = parse_sca_bytes(rebuilt)

    assert parsed.group_name == project.group_name
    assert [s.name for s in parsed.scenes] == [s.name for s in project.scenes]
    assert [len(s.objects) for s in parsed.scenes] == [
        len(s.objects) for s in project.scenes
    ]

    original_payload = zlib.decompress(path.read_bytes()[4:])
    rebuilt_payload = zlib.decompress(rebuilt[4:])
    assert original_payload == rebuilt_payload

    # Prueba de modificación de longitudes.
    changed = project.clone()
    changed.group_name = "Estampadora"
    if changed.scenes:
        changed.scenes[0].name = "ESCENA DE PRUEBA"
    changed.validate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sca", help="Archivo .sca real exportado por mView")
    args = ap.parse_args()
    test_roundtrip(Path(args.sca))
    print("SCA CORE TEST: PASS")
