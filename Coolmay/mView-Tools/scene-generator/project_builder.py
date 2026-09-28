from __future__ import annotations

"""Builder de referencia para las pantallas HMI de la estampadora."""

from sca_core import SCAScene, read_sca
from object_factory import TemplateLibrary


def make_scene(base_scene, name, objects):
    return SCAScene(name=name, meta=base_scene.meta, objects=list(objects))


def build_estampadora(template_path: str, output_path: str):
    source = read_sca(template_path)
    lib = TemplateLibrary.from_old_project(source)

    # 1 ESTADO
    estado = [
        lib.text("ESTADO", (10, 5, 160, 32)),
        lib.nav_button("MENU", 2, (390, 5, 470, 42)),
        lib.text("PLC", (10, 42, 85, 67)),
        lib.display("D0", (90, 40, 165, 68), "###"),
        lib.text("FALLA", (175, 42, 250, 67)),
        lib.display("D2", (255, 40, 330, 68), "###"),
        lib.text("ACTUAL", (10, 78, 85, 103)),
        lib.display("D128", (90, 76, 180, 106), "######"),
        lib.text("OBJETIVO", (190, 78, 280, 103)),
        lib.display("D130", (285, 76, 375, 106), "######"),
        lib.text("NUEVO", (10, 115, 85, 140)),
        lib.input("D132", (90, 112, 180, 145), fmt="######", maximum="99999", minimum="0"),
        lib.command_button("NUEVO LOTE", "M103", (190, 112, 310, 150)),
        lib.command_button("CONTINUAR", "M104", (320, 112, 460, 150)),
        lib.text("AUTO", (10, 165, 70, 190)),
        lib.indicator("M4", (75, 162, 110, 192)),
        lib.text("P1A", (120, 165, 165, 190)),
        lib.indicator("M6", (168, 162, 203, 192)),
        lib.text("P1B", (210, 165, 255, 190)),
        lib.indicator("M7", (258, 162, 293, 192)),
        lib.text("P2↓", (300, 165, 345, 190)),
        lib.indicator("M8", (348, 162, 383, 192)),
        lib.text("P3 FIN", (390, 165, 455, 190)),
        lib.indicator("M9", (440, 162, 475, 192)),
        lib.command_button("TECNICO", "M100", (10, 210, 130, 255)),
        lib.text("B1+B4 3s = DETENER / REANUDAR", (145, 218, 465, 248)),
    ]

    # 2 MENU
    menu = [
        lib.text("MENU", (10, 5, 150, 35)),
        lib.nav_button("ESTADO", 1, (20, 55, 140, 110)),
        lib.nav_button("LOTE", 3, (180, 55, 300, 110)),
        lib.nav_button("DIAGNOSTICO", 4, (340, 55, 465, 110)),
        lib.nav_button("CONFIG", 5, (100, 140, 220, 200)),
        lib.nav_button("TECH TEST", 6, (260, 140, 380, 200)),
        lib.text("Seleccionar pantalla", (150, 220, 345, 250)),
    ]

    # 3 LOTE
    lote = [
        lib.text("LOTE", (10, 5, 150, 35)),
        lib.nav_button("ESTADO", 1, (390, 5, 470, 42)),
        lib.text("ACTUAL", (20, 55, 145, 80)),
        lib.display("D128", (160, 52, 280, 84), "######"),
        lib.text("OBJETIVO", (20, 95, 145, 120)),
        lib.display("D130", (160, 92, 280, 124), "######"),
        lib.text("ESTADO LOTE", (20, 135, 145, 160)),
        lib.display("D15", (160, 132, 240, 164), "##"),
        lib.text("NUEVO OBJETIVO", (20, 175, 155, 200)),
        lib.input("D132", (160, 172, 280, 205), fmt="######", maximum="99999", minimum="0"),
        lib.command_button("NUEVO LOTE", "M103", (300, 60, 455, 110)),
        lib.command_button("CONTINUAR", "M104", (300, 125, 455, 175)),
        lib.text("Objetivo 0 = SIN LIMITE", (285, 200, 465, 235)),
    ]

    # 4 DIAGNOSTICO
    diag = [
        lib.text("DIAGNOSTICO", (10, 5, 200, 35)),
        lib.nav_button("MENU", 2, (390, 5, 470, 42)),
    ]
    diag_rows = [
        ("STATE", "D0"), ("FALLA", "D2"), ("P2 POS", "D10"), ("P3 POS", "D11"),
        ("P4 POS", "D12"), ("LOTE", "D15"), ("P1 OK", "D16"), ("CLASE", "D17"),
    ]
    y = 45
    for idx, (label, addr) in enumerate(diag_rows):
        col = 0 if idx < 4 else 1
        yy = y + (idx % 4) * 42
        x0 = 15 if col == 0 else 245
        diag.append(lib.text(label, (x0, yy, x0+95, yy+25)))
        diag.append(lib.display(addr, (x0+100, yy-2, x0+190, yy+28), "####"))

    bits = [
        ("P1 A", "M6"), ("P1 B", "M7"), ("P2 DOWN", "M8"), ("P3 DONE", "M9"),
        ("Y0", "Y0"), ("Y1", "Y1"), ("Y2", "Y2"), ("Y3", "Y3"), ("EV0", "Y4"),
    ]
    x = 15
    yb = 220
    for label, addr in bits:
        diag.append(lib.text(label, (x, yb, x+48, yb+22)))
        diag.append(lib.indicator(addr, (x+50, yb-2, x+78, yb+24)))
        x += 50
        if x > 420:
            break

    # 5 CONFIG
    config = [
        lib.text("CONFIG", (10, 3, 130, 30)),
        lib.nav_button("MENU", 2, (390, 3, 470, 40)),
        lib.text("CFG", (250, 28, 300, 50)),
        lib.text("EFF", (350, 28, 400, 50)),
    ]
    params = [
        ("P1 MAX", "D140", "D50", "6000"),
        ("P2 DOWN", "D141", "D51", "6000"),
        ("P2 UP", "D142", "D52", "6000"),
        ("P3 PRINT", "D143", "D53", "6000"),
        ("P3 RETURN", "D144", "D54", "6000"),
        ("P4", "D145", "D55", "500"),
        ("DEBOUNCE", "D146", "D56", "50"),
        ("AIR SETTLE", "D147", "D57", "500"),
    ]
    y = 52
    for label, cfg, eff, mx in params:
        config.append(lib.text(label, (10, y, 145, y+22)))
        config.append(lib.input(cfg, (150, y-3, 245, y+25), fmt="####", maximum=mx, minimum="1"))
        config.append(lib.display(eff, (275, y-3, 360, y+25), "####"))
        y += 25

    config += [
        lib.text("VALIDA", (370, 62, 430, 84)),
        lib.indicator("M60", (435, 60, 470, 87)),
        lib.command_button("APLICAR", "M102", (370, 100, 470, 145)),
        lib.text("Requiere acceso tecnico", (365, 155, 475, 205)),
    ]

    # 6 TECH TEST
    tech = [
        lib.text("TECH TEST", (10, 3, 160, 30)),
        lib.nav_button("MENU", 2, (390, 3, 470, 40)),
        lib.text("CMD 1..8", (10, 45, 110, 70)),
        lib.input("D3", (115, 42, 190, 74), fmt="#", maximum="8", minimum="1"),
        lib.command_button("EJECUTAR", "M105", (205, 40, 330, 80)),
        lib.command_button("ENTRAR", "M100", (340, 45, 410, 78)),
        lib.command_button("SALIR", "M101", (410, 45, 475, 78)),
        lib.text("STATE", (10, 92, 70, 115)),
        lib.display("D0", (72, 89, 137, 117), "###"),
        lib.text("FALLA", (145, 92, 205, 115)),
        lib.display("D2", (208, 89, 273, 117), "###"),
        lib.text("P2", (280, 92, 310, 115)),
        lib.display("D10", (312, 89, 365, 117), "##"),
        lib.text("P3", (370, 92, 400, 115)),
        lib.display("D11", (402, 89, 455, 117), "##"),
        lib.text("1 P1->A     2 P1->B", (10, 130, 225, 153)),
        lib.text("3 P2 UP     4 P2 DOWN", (245, 130, 470, 153)),
        lib.text("5 P3 RETURN 6 P3 PRINT", (10, 158, 225, 181)),
        lib.text("7 P4 PRINT  8 P4 LOAD", (245, 158, 470, 181)),
        lib.text("P4", (10, 200, 45, 222)),
        lib.display("D12", (50, 197, 105, 225), "##"),
        lib.text("P1 OK", (115, 200, 175, 222)),
        lib.display("D16", (180, 197, 235, 225), "#"),
        lib.text("UNLOCK", (245, 200, 315, 222)),
        lib.indicator("M106", (320, 197, 355, 225)),
        lib.text("MANUAL fisico requerido", (365, 198, 475, 235)),
    ]

    project = source.clone()
    project.group_name = "Estampadora"
    project.scenes = [
        make_scene(source.scenes[0], "ESTADO", estado),
        make_scene(source.scenes[1], "MENU", menu),
        make_scene(source.scenes[2], "LOTE", lote),
        make_scene(source.scenes[3], "DIAGNOSTICO", diag),
        make_scene(source.scenes[4], "CONFIG", config),
        make_scene(source.scenes[5], "TECH TEST", tech),
    ]

    project.validate()
    project.write(output_path)
    return project


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("template", help="Proyecto .sca base con widgets conocidos")
    ap.add_argument("output")
    args = ap.parse_args()

    project = build_estampadora(args.template, args.output)
    print(
        f"OK: {args.output} · grupo={project.group_name} · "
        f"escenas={len(project.scenes)}"
    )
