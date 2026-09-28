from __future__ import annotations

import argparse

from excel_reader import detect_header_row, read_headers, records_from_excel
from mview_tag import validate_records, write_tag


def main():
    p = argparse.ArgumentParser(description="Genera un .tag de mView desde un Excel.")
    p.add_argument("excel")
    p.add_argument("output")
    p.add_argument("--sheet", default="11_TAG_EXPORT")
    p.add_argument("--group", default="Estampadora")
    p.add_argument("--header-row", type=int)
    args = p.parse_args()

    header_row = args.header_row
    mapping = {}
    if header_row is None:
        header_row, mapping = detect_header_row(args.excel, args.sheet)

    headers = read_headers(args.excel, args.sheet, header_row)

    if not mapping:
        normalized = [h.strip().lower() for h in headers]
        aliases = {
            "tag": ["tag", "tag mview"],
            "address": ["dirección plc", "direccion plc", "dispositivo plc"],
            "comment": ["comentario", "descripción", "descripcion"],
            "maximum": ["máx", "max", "máximo", "maximo"],
            "minimum": ["mín", "min", "mínimo", "minimo"],
        }
        for key, opts in aliases.items():
            for opt in opts:
                if opt in normalized:
                    mapping[key] = normalized.index(opt)
                    break

    records = validate_records(
        records_from_excel(args.excel, args.sheet, header_row, mapping)
    )
    write_tag(args.output, records, args.group)
    print(f"OK: {args.output} · grupo={args.group} · tags={len(records)}")


if __name__ == "__main__":
    main()
