from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from project_builder import build_estampadora
from sca_core import read_sca


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("mView SCA Toolkit")
        root.geometry("1050x700")

        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Abrí un .sca exportado por mView.")
        self.project = None

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Entry(top, textvariable=self.path_var).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(top, text="Abrir .sca…", command=self.open_sca).pack(
            side="left", padx=5
        )
        ttk.Button(
            top,
            text="Generar Estampadora…",
            command=self.generate,
        ).pack(side="left")

        pan = ttk.Panedwindow(root, orient="horizontal")
        pan.pack(fill="both", expand=True, padx=10, pady=5)

        left = ttk.Frame(pan)
        right = ttk.Frame(pan)
        pan.add(left, weight=1)
        pan.add(right, weight=3)

        self.scenes = tk.Listbox(left)
        self.scenes.pack(fill="both", expand=True)
        self.scenes.bind("<<ListboxSelect>>", self.scene_selected)

        cols = ("idx", "type", "rect", "strings")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        for col, width in [
            ("idx", 55),
            ("type", 80),
            ("rect", 170),
            ("strings", 580),
        ]:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=width, anchor="w")

        ys = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")

        ttk.Label(root, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=10, pady=8
        )

    def open_sca(self):
        path = filedialog.askopenfilename(
            filetypes=[("mView scenes", "*.sca"), ("Todos", "*.*")]
        )
        if not path:
            return

        try:
            project = read_sca(path)
            project.validate()
            self.project = project
            self.path_var.set(path)
            self.scenes.delete(0, "end")

            for i, scene in enumerate(project.scenes, start=1):
                self.scenes.insert(
                    "end",
                    f"{i:02d}  {scene.name}  ({len(scene.objects)} objetos)",
                )

            self.status_var.set(
                f"VÁLIDO · grupo={project.group_name} · "
                f"escenas={len(project.scenes)}"
            )

            if project.scenes:
                self.scenes.selection_set(0)
                self.scene_selected()
        except Exception as exc:
            messagebox.showerror("SCA", str(exc))

    def scene_selected(self, _event=None):
        if not self.project:
            return

        selected = self.scenes.curselection()
        if not selected:
            return

        scene = self.project.scenes[selected[0]]
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, obj in enumerate(scene.objects):
            try:
                rect = str(obj.rect)
            except Exception:
                rect = "-"

            self.tree.insert(
                "",
                "end",
                values=(
                    i,
                    f"{obj.header_a},{obj.header_b}",
                    rect,
                    " | ".join(obj.strings),
                ),
            )

    def generate(self):
        template = self.path_var.get().strip()
        if not template:
            messagebox.showwarning(
                "Plantilla",
                "Abrí primero un proyecto .sca base compatible.",
            )
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".sca",
            initialfile="Estampadora_Escenas.sca",
            filetypes=[("mView scenes", "*.sca")],
        )
        if not output:
            return

        try:
            project = build_estampadora(template, output)
            messagebox.showinfo(
                "Generado",
                f"Archivo generado y verificado.\n\n"
                f"Grupo: {project.group_name}\n"
                f"Escenas: {len(project.scenes)}\n"
                f"{output}",
            )
        except Exception as exc:
            messagebox.showerror("Generación", str(exc))


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
