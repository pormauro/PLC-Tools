
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading, time, re
try:
    import pyautogui
except ImportError:
    pyautogui=None

TITLE='GX Text Writer V3 - Ladder Keys'
DEFAULT_DELAY=280
DEFAULT_START=3

EXAMPLE='''; EJEMPLO V3 - NO USA LD / OUT TEXTUAL
; Usa las teclas rápidas de GX Works:
; [NO M8001] = F5 contacto NA
; [NC M200]  = F6 contacto NC
; [COIL M200] = F7 bobina
; [APP MOV K10 D100] = F8 función/aplicada

[NO M8001]
[COIL M200]

[NC M200]
[COIL M201]

[NO M8001]
[APP MOV K10 D100]

[NO M8001]
[APP FLT D100 D102]

[NO M8001]
[APP DEDIV D102 K10 D104]
'''

TEST='''; TEST SIMPLE V3
; Clic en una celda vacía del ladder y apretar F8 en este programa.

[NO M8001]
[COIL M200]

[NC M200]
[COIL M201]

[NO M8001]
[APP MOV K10 D100]

[NO M8001]
[APP MOV K20 D101]

[NO M8001]
[APP ADD D100 D101 D104]

[NO M8001]
[APP FLT D100 D120]

[NO M8001]
[APP DEDIV D120 K10 D122]

[NO M8001]
[COIL M202]
'''

SYSTEM='''; TEST SISTEMA V3 - SIN LD / OUT TEXTUAL
; M200-M230

[NO M8001]
[COIL M200]

[NC M200]
[COIL M201]

[NO M8001]
[APP MOV K10 D100]

[NO M8001]
[APP MOV K20 D101]

[NO M8001]
[APP MOV D100 D102]

[NO M8001]
[APP ADD D100 D101 D104]

[NO M8001]
[APP SUB D101 D100 D105]

[NO M8001]
[APP MUL D100 D101 D106]

[NO M8001]
[APP DIV D101 D100 D108]

[NO M8001]
[APP FLT D100 D120]

[NO M8001]
[APP FLT D101 D122]

[NO M8001]
[APP DEADD D120 D122 D130]

[NO M8001]
[APP DESUB D122 D120 D132]

[NO M8001]
[APP DEMUL D120 D122 D134]

[NO M8001]
[APP DEDIV D122 D120 D136]

[NO M8001]
[APP INT D136 D140]

[NO M8001]
[APP MOV D8030 D0]

[NO M8001]
[APP FLT D0 D2]

[NO M8001]
[APP DEDIV D2 K250 D4]

[NO M8001]
[APP DEADD D4 K4 D6]

[NO M8001]
[APP EMOV D6 D4]

[NO M8001]
[COIL M230]
'''

class App:
    def __init__(self, root):
        self.root=root; root.title(TITLE); root.geometry('1060x760'); root.minsize(900,600)
        self.running=False; self.paused=False; self.abort_flag=False
        self.delay=tk.StringVar(value=str(DEFAULT_DELAY)); self.start=tk.StringVar(value=str(DEFAULT_START))
        self.top=tk.BooleanVar(value=True); self.clip=tk.BooleanVar(value=True); self.ignore=tk.BooleanVar(value=True)
        self.build(); self.bind(); root.attributes('-topmost', True); self.text.insert('1.0', EXAMPLE); self.status('Listo V3: usa [NO]/[NC]/[COIL]/[APP], no usa LD textual.')
    def build(self):
        main=ttk.Frame(self.root,padding=10); main.pack(fill='both',expand=True)
        top=ttk.Frame(main); top.pack(fill='x')
        ttk.Label(top,text=TITLE,font=('Segoe UI',14,'bold')).pack(side='left')
        ttk.Checkbutton(top,text='Siempre arriba',variable=self.top,command=lambda:self.root.attributes('-topmost',self.top.get())).pack(side='right')
        c=ttk.LabelFrame(main,text='Controles',padding=10); c.pack(fill='x',pady=(10,8))
        for i,(t,cmd) in enumerate([('Ejemplo V3',self.load_ex),('Test simple',self.load_test),('Test sistema',self.load_sys),('Abrir .txt',self.open),('Guardar .txt',self.save),('Limpiar',self.clear)]):
            ttk.Button(c,text=t,command=cmd).grid(row=0,column=i,padx=4,pady=4,sticky='ew')
        self.bstart=ttk.Button(c,text='ESCRIBIR EN 3s (F8)',command=self.start_write); self.bstart.grid(row=0,column=6,padx=4,pady=4,sticky='ew')
        self.bpause=ttk.Button(c,text='Pausar (F9)',command=self.pause,state='disabled'); self.bpause.grid(row=0,column=7,padx=4,pady=4,sticky='ew')
        self.babort=ttk.Button(c,text='Abortar (ESC)',command=self.abort,state='disabled'); self.babort.grid(row=0,column=8,padx=4,pady=4,sticky='ew')
        for i in range(9): c.columnconfigure(i,weight=1)
        o=ttk.Frame(c); o.grid(row=1,column=0,columnspan=9,sticky='w',pady=(8,0))
        ttk.Label(o,text='Delay acción (ms):').pack(side='left'); ttk.Entry(o,width=8,textvariable=self.delay).pack(side='left',padx=(4,15))
        ttk.Label(o,text='Cuenta regresiva (s):').pack(side='left'); ttk.Entry(o,width=8,textvariable=self.start).pack(side='left',padx=(4,15))
        ttk.Checkbutton(o,text='Pegar texto por portapapeles',variable=self.clip).pack(side='left',padx=(0,15))
        ttk.Checkbutton(o,text='Ignorar comentarios ; y //',variable=self.ignore).pack(side='left')
        h=ttk.LabelFrame(main,text='Comandos V3',padding=8); h.pack(fill='x',pady=(0,8))
        ttk.Label(h,text='[NO M8001]=F5 contacto NA | [NC M200]=F6 contacto NC | [COIL M200]=F7 bobina | [APP MOV K10 D100]=F8 función | [KEY F5] [WAIT 500] [ENTER] [RIGHT] [DOWN]',wraplength=1000).pack(anchor='w')
        ttk.Label(main,text='Si F5/F6/F7/F8 no coinciden con tu GX Works, avisame y lo cambiamos.').pack(fill='x',pady=(0,8))
        tf=ttk.Frame(main); tf.pack(fill='both',expand=True)
        self.text=tk.Text(tf,wrap='none',undo=True,font=('Consolas',11),borderwidth=1,relief='solid')
        ys=ttk.Scrollbar(tf,orient='vertical',command=self.text.yview); xs=ttk.Scrollbar(tf,orient='horizontal',command=self.text.xview)
        self.text.configure(yscrollcommand=ys.set,xscrollcommand=xs.set); self.text.grid(row=0,column=0,sticky='nsew'); ys.grid(row=0,column=1,sticky='ns'); xs.grid(row=1,column=0,sticky='ew')
        tf.rowconfigure(0,weight=1); tf.columnconfigure(0,weight=1)
        b=ttk.Frame(main); b.pack(fill='x',pady=(8,0)); self.svar=tk.StringVar(); self.pvar=tk.StringVar(value='0 líneas')
        ttk.Label(b,textvariable=self.svar).pack(side='left',fill='x',expand=True); ttk.Label(b,textvariable=self.pvar).pack(side='right')
    def bind(self):
        self.root.bind('<F8>',lambda e:self.start_write()); self.root.bind('<F9>',lambda e:self.pause()); self.root.bind('<Escape>',lambda e:self.abort())
    def status(self,msg): self.svar.set(msg); self.root.update_idletasks()
    def set_text(self,txt,msg): self.text.delete('1.0','end'); self.text.insert('1.0',txt); self.status(msg)
    def load_ex(self): self.set_text(EXAMPLE,'Ejemplo V3 cargado.')
    def load_test(self): self.set_text(TEST,'Test simple cargado.')
    def load_sys(self): self.set_text(SYSTEM,'Test sistema cargado.')
    def clear(self):
        if messagebox.askyesno('Limpiar','¿Borrar todo?'): self.set_text('', 'Texto limpiado.')
    def open(self):
        p=filedialog.askopenfilename(filetypes=[('Text files','*.txt'),('All files','*.*')])
        if p:
            try: txt=Path(p).read_text(encoding='utf-8')
            except UnicodeDecodeError: txt=Path(p).read_text(encoding='latin-1')
            self.set_text(txt,f'Archivo abierto: {p}')
    def save(self):
        p=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Text files','*.txt'),('All files','*.*')])
        if p: Path(p).write_text(self.text.get('1.0','end-1c'),encoding='utf-8'); self.status(f'Archivo guardado: {p}')
    def intval(self,var,default):
        try: return max(0,int(var.get().strip()))
        except: return default
    def start_write(self):
        if self.running: return
        if pyautogui is None: messagebox.showerror('Falta pyautogui','Ejecutá: python -m pip install pyautogui'); return
        txt=self.text.get('1.0','end-1c')
        if not txt.strip(): messagebox.showwarning('Sin texto','No hay texto.'); return
        self.running=True; self.paused=False; self.abort_flag=False; self.buttons()
        threading.Thread(target=self.worker,args=(txt,self.intval(self.delay,DEFAULT_DELAY),self.intval(self.start,DEFAULT_START)),daemon=True).start()
    def pause(self):
        if not self.running: return
        self.paused=not self.paused; self.bpause.configure(text='Continuar (F9)' if self.paused else 'Pausar (F9)'); self.status('Pausado.' if self.paused else 'Escribiendo...')
    def abort(self):
        if self.running: self.abort_flag=True; self.paused=False; self.status('Abortando...')
    def buttons(self):
        r=self.running; self.bstart.configure(state='disabled' if r else 'normal'); self.bpause.configure(state='normal' if r else 'disabled',text='Pausar (F9)'); self.babort.configure(state='normal' if r else 'disabled')
    def prep(self,lines):
        out=[]
        for raw in lines:
            line=raw.strip()
            if not line: continue
            if self.ignore.get() and (line.startswith(';') or line.startswith('//')): continue
            out.append(line)
        return out
    def worker(self,txt,delay,start):
        try:
            for sec in range(start,0,-1):
                if self.abort_flag: return
                self.status(f'Empieza en {sec}s. Hacé clic en una celda vacía del ladder...'); time.sleep(1)
            lines=self.prep(txt.splitlines()); total=len(lines); self.pvar.set(f'0 / {total}'); self.status('Escribiendo V3...')
            for i,line in enumerate(lines,1):
                if self.abort_flag: self.status('Abortado.'); return
                while self.paused and not self.abort_flag: time.sleep(.1)
                self.exec_line(line); self.pvar.set(f'{i} / {total}'); time.sleep(delay/1000)
            self.status('Escritura terminada.')
        except Exception as e:
            self.status('Error.'); messagebox.showerror('Error',str(e))
        finally:
            self.running=False; self.paused=False; self.abort_flag=False; self.root.after(0,self.buttons)
    def paste(self,txt):
        if self.clip.get():
            self.root.clipboard_clear(); self.root.clipboard_append(txt); self.root.update(); time.sleep(.05); pyautogui.hotkey('ctrl','v'); time.sleep(.05)
        else: pyautogui.write(txt)
    def gx(self,fkey,arg):
        pyautogui.press(fkey); time.sleep(.10)
        if arg: self.paste(arg); time.sleep(.05)
        pyautogui.press('enter'); time.sleep(.10)
    def exec_line(self,line):
        if line.startswith('[') and line.endswith(']'): return self.cmd(line[1:-1].strip())
        self.paste(line); pyautogui.press('enter')
    def cmd(self,c):
        for pat,fkey in [(r'^(NO|CONTACT|NA)\s+(.+)$','f5'),(r'^(NC|CONTACT_NC)\s+(.+)$','f6'),(r'^(COIL|OUT)\s+(.+)$','f7'),(r'^(APP|FUNC|INST|FUNCTION)\s+(.+)$','f8')]:
            m=re.match(pat,c,re.I)
            if m: return self.gx(fkey,m.group(2).strip())
        m=re.match(r'^KEY\s+(.+)$',c,re.I)
        if m: pyautogui.press(m.group(1).strip().lower()); return
        u=c.upper(); m=re.match(r'^WAIT\s+(\d+)$',u)
        if m: time.sleep(int(m.group(1))/1000); return
        keys={'ENTER':'enter','TAB':'tab','UP':'up','DOWN':'down','LEFT':'left','RIGHT':'right','BACKSPACE':'backspace','DELETE':'delete','ESC':'esc','SPACE':'space','HOME':'home','END':'end','F1':'f1','F2':'f2','F3':'f3','F4':'f4','F5':'f5','F6':'f6','F7':'f7','F8':'f8','F9':'f9','F10':'f10','F11':'f11','F12':'f12'}
        hot={'CTRL+A':('ctrl','a'),'CTRL+C':('ctrl','c'),'CTRL+V':('ctrl','v'),'CTRL+Z':('ctrl','z')}
        if u in keys: pyautogui.press(keys[u]); return
        if u in hot: pyautogui.hotkey(*hot[u]); return
        raise ValueError('Comando no reconocido: ['+c+']')

def main():
    root=tk.Tk(); App(root); root.mainloop()
if __name__=='__main__': main()
