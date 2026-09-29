from __future__ import annotations

"""Fábrica de objetos mView basada en widgets reales clonados."""

from dataclasses import dataclass

from sca_core import SCAError, SCAObject, SCAProject


@dataclass
class TemplateLibrary:
    nav: SCAObject
    back: SCAObject
    static_text: SCAObject
    numeric_display: SCAObject
    numeric_input: SCAObject
    momentary_button: SCAObject
    bit_indicator: SCAObject

    @classmethod
    def from_old_project(cls, project: SCAProject) -> "TemplateLibrary":
        """
        Adaptador de referencia para el proyecto viejo usado durante la ingeniería inversa.

        Este método conserva índices conocidos del fixture original. El siguiente paso del
        proyecto es detectar widgets por firma estructural en lugar de índices fijos.
        """
        if len(project.scenes) < 4:
            raise SCAError("La plantilla necesita al menos 4 escenas.")

        s1 = project.scenes[0]
        s2 = project.scenes[1]
        s3 = project.scenes[2]
        s4 = project.scenes[3]

        try:
            return cls(
                nav=s2.objects[0].clone(),
                back=s2.objects[1].clone(),
                static_text=s3.objects[1].clone(),
                numeric_display=s4.objects[14].clone(),
                numeric_input=s1.objects[1].clone(),
                momentary_button=s1.objects[8].clone(),
                bit_indicator=s2.objects[5].clone(),
            )
        except IndexError as exc:
            raise SCAError(
                "La plantilla no coincide con la disposición del proyecto de referencia."
            ) from exc

    def nav_button(self, text: str, target: int, rect) -> SCAObject:
        obj = self.nav.clone()
        obj.replace_strings({"Tiempos": text})
        obj.set_rect(rect)
        obj.set_nav_target(target)
        return obj

    def back_button(self, text: str, rect) -> SCAObject:
        obj = self.back.clone()
        obj.replace_strings({"Atrás": text})
        obj.set_rect(rect)
        return obj

    def text(self, text: str, rect) -> SCAObject:
        obj = self.static_text.clone()
        obj.replace_strings({"Tiempo de Corte [mS]": text})
        obj.set_rect(rect)
        return obj

    def display(self, address: str, rect, fmt: str = "####") -> SCAObject:
        obj = self.numeric_display.clone()
        obj.replace_strings({"D0": address, "####": fmt})
        obj.set_rect(rect)
        return obj

    def input(
        self,
        address: str,
        rect,
        *,
        fmt: str = "#####",
        maximum: str = "99999",
        minimum: str = "0",
    ) -> SCAObject:
        obj = self.numeric_input.clone()
        obj.replace_strings({
            "D153": address,
            "####": fmt,
            "9999": maximum,
            "0": minimum,
        })
        obj.set_rect(rect)
        return obj

    def command_button(self, text: str, address: str, rect) -> SCAObject:
        """
        Clona el botón momentáneo de referencia y remapea texto/dirección.
        Confirmar el modo momentáneo una vez dentro de mView para cada versión.
        """
        obj = self.momentary_button.clone()
        obj.replace_strings({"Reset contador": text, "M21": address})
        obj.set_rect(rect)
        return obj

    def indicator(
        self,
        address: str,
        rect,
        *,
        off_text: str = "0",
        on_text: str = "1",
    ) -> SCAObject:
        obj = self.bit_indicator.clone()
        obj.replace_strings({
            "X0": address,
            "0": off_text,
            "1": on_text,
        })
        obj.set_rect(rect)
        return obj
