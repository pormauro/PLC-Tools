from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from excel_reader import (
    detect_header_row,
    list_sheets,
    read_headers,
    records_from_excel,
)
from mview_tag import read_tag, validate_records, write_tag


TITLE = "mView Tag Generator"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(TITLE)
        self.root.geometry("1180x760")
        self.root.minsize(920, 620)

        self.file_var = tk.StringVar()
        self.sheet_var = tk.StringVar()
        self.header_row_var = tk.IntVar(value=1)
        self.group_var = tk.StringVar(value="Estampadora")
        self.status_var = tk.StringVar(value="Seleccioná un Excel.")

        self.column_vars = {
            "tag": tk.StringVar(),
            "address": tk.StringVar(),
            "comment": tk.StringVar(),
            "maximum": tk.StringVar(),
            "minimum": tk.StringVar(),
        }
        self.column_combos = {}
        self.headers: list[str] = []
        self.records = []

        self._build()

    def _build(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        box = ttk.LabelFrame(main, text="1. Excel de origen", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Archivo:").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.file_var).grid(
            row=0, column=1, sticky="ew", padx=6
        )
        ttk.Button(box, text="Abrir Excel…", command=self.choose_excel).grid(
            row=0, column=2, padx=4
        )

        ttk.Label(box, text="Hoja:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.sheet_combo = ttk.Combobox(
            box, textvariable=self.sheet_var, state="readonly", width=32
        )
        self.sheet_combo.grid(row=1, column=1, sticky="w", padx=6, pady=(8, 0))
        self.sheet_combo.bind("<<ComboboxSelected>>", lambda _e: self.auto_detect())

        ttk.Label(box, text="Fila encabezado:").grid(
            row=1, column=1, sticky="e", padx=(0, 180), pady=(8, 0)
        )
        self.header_spin = ttk.Spinbox(
            box,
            from_=1,
            to=999,
            textvariable=self.header_row_var,
            width=7,
            command=self.refresh_headers,
        )
        self.header_spin.grid(
            row=1, column=1, sticky="e", padx=(0, 96), pady=(8, 0)
        )
        ttk.Button(box, text="Autodetectar", command=self.auto_detect).grid(
            row=1, column=2, padx=4, pady=(8, 0)
        )
        box.columnconfigure(1, weight=1)

        mapbox = ttk.LabelFrame(main, text="2. Mapeo de columnas", padding=10)
        mapbox.pack(fill="x", pady=(10, 0))

        fields = [
            ("tag", "TAG *"),
            ("address", "Dirección PLC *"),
            ("comment", "Comentario"),
            ("maximum", "Máximo"),
            ("minimum", "Mínimo"),
        ]
        for col, (key, label) in enumerate(fields):
            ttk.Label(mapbox, text=label).grid(row=0, column=col, sticky="w")
            cb = ttk.Combobox(
                mapbox,
                textvariable=self.column_vars[key],
                state="readonly",
                width=24,
            )
            cb.grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))
            mapbox.columnconfigure(col, weight=1)
            self.column_combos[key] = cb

        actions = ttk.LabelFrame(main, text="3. Generación .tag", padding=10)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Label(actions, text="Grupo mView:").pack(side="left")
        ttk.Entry(actions, textvariable=self.group_var, width=26).pack(
            side="left", padx=(6, 14)
        )
        ttk.Button(
            actions, text="Cargar / previsualizar", command=self.load_preview
        ).pack(side="left", padx=4)
        ttk.Button(actions, text="GENERAR .TAG", command=self.generate).pack(
            side="left", padx=4
        )
        ttk.Button(actions, text="Verificar .TAG…", command=self.verify_tag).pack(
            side="left", padx=4
        )

        pbox = ttk.LabelFrame(main, text="Vista previa", padding=8)
        pbox.pack(fill="both", expand=True, pady=(10, 0))

        cols = ("n", "tag", "address", "comment", "max", "min")
        self.tree = ttk.Treeview(pbox, columns=cols, show="headings", height=18)
        headings = {
            "n": "#",
            "tag": "TAG",
            "address": "Dirección",
            "comment": "Comentario",
            "max": "Máx",
            "min": "Mín",
        }
        widths = {
            "n": 55,
            "tag": 220,
            "address": 140,
            "comment": 520,
            "max": 90,
            "min": 90,
        }
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w")

        ys = ttk.Scrollbar(pbox, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(pbox, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        pbox.rowconfigure(0, weight=1)
        pbox.columnconfigure(0, weight=1)

        ttk.Label(main, textvariable=self.status_var, anchor="w").pack(
            fill="x", pady=(8, 0)
        )

    def set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def choose_excel(self):
        path = filedialog.askopenfilename(
            title="Seleccionar Excel",
            filetypes=[("Excel", "*.xlsx *.xlsm"), ("Todos", "*.*")],
        )
        if not path:
            return

        self.file_var.set(path)
        try:
            names = [s.name for s in list_sheets(path)]
            self.sheet_combo["values"] = names
            preferred = "11_TAG_EXPORT" if "11_TAG_EXPORT" in names else names[0]
            self.sheet_var.set(preferred)
            self.auto_detect()
        except Exception as exc:
            messagebox.showerror("Excel", str(exc))

    def auto_detect(self):
        path = self.file_var.get().strip()
        sheet = self.sheet_var.get().strip()
        if not path or not sheet:
            return

        try:
            row, mapping = detect_header_row(path, sheet)
            self.header_row_var.set(row)
            self.refresh_headers()

            for field, idx in mapping.items():
                if idx < len(self.headers):
                    self.column_vars[field].set(self.headers[idx])

            for field in ("comment", "maximum", "minimum"):
                if field not in mapping:
                    self.column_vars[field].set("")

            self.set_status(
                f"Encabezado detectado en fila {row}. Revisá el mapeo."
            )
        except Exception as exc:
            self.set_status(f"Autodetección: {exc}")
            try:
                self.refresh_headers()
            except Exception:
                pass

    def refresh_headers(self):
        path = self.file_var.get().strip()
        sheet = self.sheet_var.get().strip()
        if not path or not sheet:
            return

        self.headers = read_headers(path, sheet, int(self.header_row_var.get()))
        values = [""] + self.headers
        for cb in self.column_combos.values():
            cb["values"] = values

    def _column_indexes(self):
        result = {}
        for key, var in self.column_vars.items():
            value = var.get()
            if not value:
                result[key] = None
                continue
            try:
                result[key] = self.headers.index(value)
            except ValueError:
                result[key] = None
        return result

    def load_preview(self):
        path = self.file_var.get().strip()
        sheet = self.sheet_var.get().strip()
        if not path or not sheet:
            messagebox.showwarning("Falta Excel", "Seleccioná archivo y hoja.")
            return

        try:
            self.refresh_headers()
            records = records_from_excel(
                path,
                sheet,
                int(self.header_row_var.get()),
                self._column_indexes(),
            )
            self.records = list(validate_records(records))

            for item in self.tree.get_children():
                self.tree.delete(item)

            for i, rec in enumerate(self.records, start=1):
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        i,
                        rec.name,
                        rec.address,
                        rec.comment,
                        rec.maximum,
                        rec.minimum,
                    ),
                )

            self.set_status(
                f"{len(self.records)} tags válidos · "
                f"grupo={self.group_var.get().strip() or '(vacío)'}"
            )
        except Exception as exc:
            self.records = []
            messagebox.showerror("Validación", str(exc))

    def generate(self):
        if not self.records:
            self.load_preview()
            if not self.records:
                return

        group = self.group_var.get().strip()
        if not group:
            messagebox.showwarning("Grupo", "Ingresá un nombre de grupo.")
            return

        path = filedialog.asksaveasfilename(
            title="Guardar archivo .tag",
            defaultextension=".tag",
            initialfile=f"{group.lower().replace(' ', '_')}_tags.tag",
            filetypes=[("mView tag", "*.tag"), ("Todos", "*.*")],
        )
        if not path:
            return

        try:
            write_tag(path, self.records, group)
            parsed = read_tag(path)
            if len(parsed.records) != len(self.records):
                raise ValueError("Verificación: cantidad de tags inconsistente.")

            self.set_status(
                f"Generado y verificado: {path} · tags={len(parsed.records)}"
            )
            messagebox.showinfo(
                "Listo",
                f"Grupo: {parsed.group_name}\n"
                f"Tags: {len(parsed.records)}\n\n{path}",
            )
        except Exception as exc:
            messagebox.showerror("Generación .tag", str(exc))

    def verify_tag(self):
        path = filedialog.askopenfilename(
            title="Verificar archivo .tag",
            filetypes=[("mView tag", "*.tag"), ("Todos", "*.*")],
        )
        if not path:
            return

        try:
            parsed = read_tag(path)
            messagebox.showinfo(
                "TAG válido",
                f"Grupo: {parsed.group_name}\n"
                f"Tags: {len(parsed.records)}\n"
                f"Versión: 0x{parsed.version:08X}\n"
                f"Marker: 0x{parsed.format_marker:08X}",
            )
        except Exception as exc:
            messagebox.showerror("TAG inválido", str(exc))


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
