import re
from tkinter import messagebox
import gx_text_writer_gui_v3 as base

base.TITLE = 'GX Text Writer V3.1 - Ladder Keys + SET/RST Guard'

_original_start_write = base.App.start_write

def _validate_set_rst(text):
    seen = {'SET': {}, 'RST': {}}
    errors = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        m = re.match(r'^\[APP\s+(SET|RST)\s+([^\]\s]+)\]$', line, re.I)
        if not m:
            continue
        op = m.group(1).upper()
        dev = m.group(2).upper()
        if dev in seen[op]:
            errors.append(f'{op} {dev}: líneas {seen[op][dev]} y {n}')
        else:
            seen[op][dev] = n
    return errors

def _guarded_start_write(self):
    text = self.text.get('1.0', 'end-1c')
    errors = _validate_set_rst(text)
    if errors:
        msg = (
            'Escritura bloqueada. Cada dispositivo puede tener como máximo '
            'un SET y un RST en todo el programa.\n\n'
            + '\n'.join(errors[:30])
        )
        if len(errors) > 30:
            msg += f'\n... y {len(errors)-30} errores más.'
        messagebox.showerror('SET/RST duplicados', msg)
        self.status('Validación fallida: SET/RST duplicados.')
        return
    return _original_start_write(self)

base.App.start_write = _guarded_start_write

if __name__ == '__main__':
    base.main()
