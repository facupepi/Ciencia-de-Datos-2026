"""
Pipeline GUI — Relevamiento Cuidado de Mascotas
================================================
Interfaz visual simple (Tkinter) que permite:
  1. Seleccionar el archivo CSV de entrada.
  2. Ejecutar el pipeline completo (limpieza + 2 reportes PDF).
  3. Abrir los PDFs generados con el visor predeterminado.

Uso:
    python pipeline_gui.py
"""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# ── Rutas ───────────────────────────────────────────────────────────────────
# El pipeline vive DENTRO de proyecto_mascotas, junto a los scripts y outputs.
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", EXE_DIR)
    PROYECTO_SCRIPTS = BUNDLE_DIR        # scripts extraídos por PyInstaller
    PROYECTO = EXE_DIR                    # outputs junto al .exe
    BASE_DIR = EXE_DIR
    os.makedirs(PROYECTO, exist_ok=True)
else:
    PROYECTO = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = PROYECTO
    PROYECTO_SCRIPTS = PROYECTO

# Python: busca venv en el padre de proyecto_mascotas, sino sys.executable / PATH
_venv_candidato = os.path.join(os.path.dirname(BASE_DIR), "venv", "Scripts", "python.exe")
if os.path.exists(_venv_candidato):
    VENV_PY = _venv_candidato
elif IS_FROZEN:
    VENV_PY = shutil.which("python") or shutil.which("py") or "python"
else:
    VENV_PY = sys.executable

CSV_TARGET = os.path.join(PROYECTO, "Relevamiento Cuidado de Mascotas Actualizado.csv")
LIMPIEZA_PY = os.path.join(PROYECTO_SCRIPTS, "limpieza_mascotas.py")
REPORTE_GEN_PY = os.path.join(PROYECTO_SCRIPTS, "reporte_general_pdf.py")
REPORTE_CD_PY = os.path.join(PROYECTO_SCRIPTS, "reporte_ciencia_datos_pdf.py")
REPORTE_LOOKER_PY = os.path.join(PROYECTO_SCRIPTS, "reporte_looker.py")

PDF_GENERAL = os.path.join(PROYECTO, "reporte_general.pdf")
PDF_CIENCIA = os.path.join(PROYECTO, "reporte_ciencia_datos.pdf")
INFORME_MD = os.path.join(PROYECTO, "informe_limpieza.md")

PIPELINE_STEPS = [
    ("1. Limpieza del dataset", LIMPIEZA_PY),
    ("2. Reporte General (PDF)", REPORTE_GEN_PY),
    ("3. Reporte Ciencia de Datos (PDF)", REPORTE_CD_PY),
    ("4. Reporte Looker Studio (CSVs)", REPORTE_LOOKER_PY),
]


# ── Funciones utilitarias ───────────────────────────────────────────────────
def abrir_archivo(path: str):
    """Abre un archivo con el programa predeterminado del sistema."""
    if not os.path.exists(path):
        messagebox.showwarning("No existe", f"El archivo no existe aún:\n{path}")
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:  # pragma: no cover
        messagebox.showerror("Error", f"No se pudo abrir:\n{e}")


# ── GUI ─────────────────────────────────────────────────────────────────────
class PipelineApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pipeline Mascotas — Facundo Pepino")
        self.geometry("820x620")
        self.configure(bg="#f4f4f8")

        self.csv_seleccionado = tk.StringVar(value="")
        self.en_ejecucion = False

        self._build_ui()
        self._autodetectar_csv()

    # ───────────────── UI ─────────────────
    def _build_ui(self):
        header = tk.Frame(self, bg="#2b5876", pady=14)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Pipeline de Análisis — Cuidado de Mascotas",
            font=("Segoe UI", 16, "bold"),
            fg="white", bg="#2b5876",
        ).pack()
        tk.Label(
            header,
            text="Limpieza de datos + 2 reportes PDF",
            font=("Segoe UI", 10),
            fg="#d6e2ef", bg="#2b5876",
        ).pack()

        # Selección de CSV
        sel = tk.LabelFrame(self, text="  Archivo CSV de entrada  ",
                            font=("Segoe UI", 10, "bold"),
                            bg="#f4f4f8", padx=10, pady=10)
        sel.pack(fill="x", padx=16, pady=(14, 6))

        row = tk.Frame(sel, bg="#f4f4f8")
        row.pack(fill="x")
        tk.Entry(row, textvariable=self.csv_seleccionado, width=70).pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(row, text="📂 Elegir CSV…",
                  command=self._elegir_csv,
                  bg="#2b5876", fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=4).pack(side="right")

        # Botones de acción
        acc = tk.Frame(self, bg="#f4f4f8")
        acc.pack(fill="x", padx=16, pady=(6, 6))

        self.btn_run = tk.Button(
            acc, text="▶  Ejecutar pipeline completo",
            command=self._ejecutar_pipeline,
            bg="#2ecc71", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=14, pady=8,
        )
        self.btn_run.pack(side="left", padx=(0, 8))

        tk.Button(
            acc, text="📄 Abrir Reporte General",
            command=lambda: abrir_archivo(PDF_GENERAL),
            bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=4)

        tk.Button(
            acc, text="📊 Abrir Reporte Ciencia Datos",
            command=lambda: abrir_archivo(PDF_CIENCIA),
            bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=4)

        tk.Button(
            acc, text="📝 Informe limpieza",
            command=lambda: abrir_archivo(INFORME_MD),
            bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=4)

        tk.Button(
            acc, text="📁 Carpeta",
            command=lambda: abrir_archivo(PROYECTO),
            bg="#95a5a6", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=4)

        # Progreso
        prog = tk.LabelFrame(self, text="  Progreso  ",
                             font=("Segoe UI", 10, "bold"),
                             bg="#f4f4f8", padx=10, pady=10)
        prog.pack(fill="x", padx=16, pady=(6, 6))
        self.progress = ttk.Progressbar(prog, length=760, mode="determinate",
                                        maximum=len(PIPELINE_STEPS))
        self.progress.pack(fill="x")
        self.lbl_step = tk.Label(prog, text="Esperando…",
                                 font=("Segoe UI", 9),
                                 bg="#f4f4f8", anchor="w")
        self.lbl_step.pack(fill="x", pady=(6, 0))

        # Log
        log_frame = tk.LabelFrame(self, text="  Log de ejecución  ",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#f4f4f8", padx=4, pady=4)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(6, 10))

        self.txt = tk.Text(log_frame, bg="#1e1e1e", fg="#dcdcdc",
                           font=("Consolas", 9), wrap="word",
                           insertbackground="white")
        self.txt.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(log_frame, command=self.txt.yview)
        sb.pack(side="right", fill="y")
        self.txt.config(yscrollcommand=sb.set)

        # Footer
        tk.Label(self, text="Facundo Pepino",
                 font=("Segoe UI", 8, "italic"),
                 fg="#777", bg="#f4f4f8").pack(anchor="e", padx=18, pady=(0, 6))

    # ───────────────── Lógica ─────────────────
    def _autodetectar_csv(self):
        """Si existe el CSV en la ubicación por defecto, lo carga."""
        if os.path.exists(CSV_TARGET):
            self.csv_seleccionado.set(CSV_TARGET)
            self._log(f"✔ CSV detectado: {CSV_TARGET}\n")
        else:
            self._log("ℹ Seleccioná un archivo CSV para comenzar.\n")

    def _elegir_csv(self):
        path = filedialog.askopenfilename(
            title="Seleccionar CSV del relevamiento",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")],
            initialdir=PROYECTO,
        )
        if path:
            self.csv_seleccionado.set(path)
            self._log(f"✔ CSV seleccionado: {path}\n")

    def _log(self, texto: str):
        self.txt.insert("end", texto)
        self.txt.see("end")
        self.txt.update_idletasks()

    def _set_step(self, step_idx: int, label: str):
        self.progress["value"] = step_idx
        self.lbl_step.config(text=label)
        self.update_idletasks()

    def _ejecutar_pipeline(self):
        if self.en_ejecucion:
            return
        csv = self.csv_seleccionado.get().strip()
        if not csv or not os.path.exists(csv):
            messagebox.showerror("Falta CSV",
                                 "Seleccioná un archivo CSV válido primero.")
            return

        # Lanzar en hilo para no congelar la UI
        self.en_ejecucion = True
        self.btn_run.config(state="disabled", text="⏳ Ejecutando…")
        self.txt.delete("1.0", "end")
        self.progress["value"] = 0
        t = threading.Thread(target=self._worker, args=(csv,), daemon=True)
        t.start()

    def _worker(self, csv: str):
        try:
            # 0) Si corre como .exe, copiar los scripts bundleados junto al exe
            #    para que los outputs queden al lado del ejecutable.
            scripts_runtime = []
            if IS_FROZEN:
                self._log("📦 Preparando scripts…\n")
                for _, script in PIPELINE_STEPS:
                    dest = os.path.join(PROYECTO, os.path.basename(script))
                    if (not os.path.exists(dest)
                            or os.path.getmtime(script) > os.path.getmtime(dest)):
                        shutil.copy2(script, dest)
                    scripts_runtime.append(dest)
                self._log("   ✔ Scripts listos.\n\n")
            else:
                scripts_runtime = [s for _, s in PIPELINE_STEPS]

            # 1) Copiar CSV al destino esperado por los scripts
            if os.path.abspath(csv) != os.path.abspath(CSV_TARGET):
                self._log(f"📋 Copiando CSV a {CSV_TARGET}…\n")
                os.makedirs(PROYECTO, exist_ok=True)
                shutil.copy2(csv, CSV_TARGET)
                self._log("   ✔ Copia lista.\n\n")
            else:
                self._log("ℹ CSV ya está en la ubicación esperada.\n\n")

            # 2) Ejecutar cada script
            for i, ((label, _), script) in enumerate(
                    zip(PIPELINE_STEPS, scripts_runtime), start=1):
                self._set_step(i - 1, f"Ejecutando: {label}")
                self._log(f"▶ {label}\n")
                self._log(f"   $ {os.path.basename(script)}\n")

                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                # Limpiar variables que PyInstaller inyecta en el entorno;
                # si las hereda el Python del venv, se confunde y crashea
                # al importar librerías como matplotlib.
                for _k in list(env.keys()):
                    if _k.startswith("_PYI") or _k.startswith("_MEI"):
                        env.pop(_k, None)
                for _k in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
                    env.pop(_k, None)

                # Evitar que aparezca ventana de consola del subprocess
                _creationflags = 0
                if sys.platform.startswith("win"):
                    _creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

                proc = subprocess.Popen(
                    [VENV_PY, script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    cwd=BASE_DIR,
                    creationflags=_creationflags,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._log("   " + line)
                proc.wait()

                if proc.returncode != 0:
                    self._log(f"\n❌ Falló: {label} (exit {proc.returncode})\n")
                    self._set_step(i, f"Error en: {label}")
                    messagebox.showerror(
                        "Error en pipeline",
                        f"Falló el paso:\n{label}\n\nRevisá el log.")
                    return
                self._log(f"   ✔ OK\n\n")
                self._set_step(i, f"Completado: {label}")

            # 3) Final
            self._log("🎉 Pipeline completo. PDFs listos.\n")
            if messagebox.askyesno(
                    "Listo",
                    "Pipeline ejecutado con éxito.\n\n"
                    "¿Querés abrir ahora el Reporte de Ciencia de Datos?"):
                abrir_archivo(PDF_CIENCIA)

        except Exception as e:  # pragma: no cover
            self._log(f"\n❌ Excepción: {e}\n")
            messagebox.showerror("Error", str(e))
        finally:
            self.en_ejecucion = False
            self.btn_run.config(state="normal",
                                text="▶  Ejecutar pipeline completo")


if __name__ == "__main__":
    app = PipelineApp()
    app.mainloop()
