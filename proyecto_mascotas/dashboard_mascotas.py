"""
Dashboard interactivo tipo Looker / Power BI para el dataset de mascotas.

Permite filtrar por Ciudad, Barrio, Tipo de Vivienda y Tipo de Mascota,
y visualizar en tiempo real KPIs y gráficos clave (castración, vacunación,
distribución por barrio, pedidos al municipio, etc.).
"""

import os
import sys
import textwrap
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk

# ── Rutas ───────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_LIMPIO = os.path.join(BASE_DIR, "mascotas_limpio.csv")

# ── Paleta y estilo: Clínica Veterinaria ──────────────────────────────────
# Inspirado en estética sanitaria/veterinaria: blanco clínico + teal médico
BG_DARK = "#eaf2f5"     # fondo principal (gris-azulado muy suave)
BG_PANEL = "#ffffff"    # paneles blancos limpios
BG_CARD = "#f4faf9"     # tarjetas verde-menta muy suave
FG_TEXT = "#1f3a5f"     # texto navy (lectura clínica)
ACCENT = "#2a9d8f"      # teal medicinal (color principal)
GREEN = "#52b788"       # verde sano
RED = "#e63946"         # rojo alerta
YELLOW = "#f4a261"      # naranja-ámbar precaución
PURPLE = "#4895ef"      # azul cielo (datos secundarios)

# Color de bordes y de texto sobre fondos oscuros del accent
BORDER = "#cfd8dc"
TEXT_ON_ACCENT = "#ffffff"

# Mapeo de nombres internos → etiquetas amigables para mostrar al usuario
FRIENDLY_LABELS = {
    "Tipo_Vivienda": "Tipo de vivienda",
    "Tipo_Mascotas": "Tipo de mascotas",
    "Mascota_Castrada": "¿Está castrada?",
    "Castrada": "¿Castrada?",
    "Sabe_Castracion_Gratuita": "¿Sabe que la castración es gratis?",
    "Frecuencia_Callejeros": "Callejeros observados",
    "Humano_Responsable": "¿Humano responsable?",
    "Donde_Castracion": "¿Dónde la castraron?",
    "Como_Viven_Mascotas": "¿Cómo viven las mascotas?",
    "Municipio_Presente": "Presencia del municipio",
    "Marca_Temporal": "Fecha de la encuesta",
    "Total_Mascotas": "Total mascotas",
    "Total_Perros": "Total perros",
    "Total_Gatos": "Total gatos",
    "Perros_Macho": "Perros (machos)",
    "Perros_Hembra": "Perros (hembras)",
    "Gatos_Macho": "Gatos (machos)",
    "Gatos_Hembra": "Gatos (hembras)",
}


def friendly(name: str) -> str:
    """Devuelve una etiqueta amigable para una columna o filtro."""
    if name in FRIENDLY_LABELS:
        return FRIENDLY_LABELS[name]
    # Heurística genérica: quita prefijos técnicos y reemplaza guiones bajos
    s = name
    for pref in ("Mun_", "Vive_", "CastEn_", "Mascota_"):
        if s.startswith(pref):
            s = s[len(pref):]
            break
    return s.replace("_", " ")


class _Tooltip:
    """Tooltip simple para widgets Tk: muestra texto al pasar el mouse."""

    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip = None
        self._after_id = None
        self._bind_recursive(widget)

    def _bind_recursive(self, w):
        w.bind("<Enter>", self._schedule, add="+")
        w.bind("<Leave>", self._maybe_hide, add="+")
        w.bind("<ButtonPress>", self._hide, add="+")
        for child in w.winfo_children():
            self._bind_recursive(child)

    def _maybe_hide(self, event=None):
        # Sólo oculta si el mouse salió realmente del widget contenedor
        # (no por pasar a un hijo del card).
        try:
            x, y = self.widget.winfo_pointerxy()
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            ww = self.widget.winfo_width()
            wh = self.widget.winfo_height()
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                return  # sigue dentro de la tarjeta, no cierra
        except Exception:
            pass
        self._hide()

    def _schedule(self, _=None):
        if self._tip is not None:
            return
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg="#1f3a5f")
        lbl = tk.Label(tw, text=self.text, justify="left",
                       bg="#1f3a5f", fg="#ffffff",
                       font=("Segoe UI", 9), padx=10, pady=6,
                       borderwidth=1, relief="solid")
        lbl.pack()

    def _hide(self, _=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


plt.rcParams.update({
    "axes.facecolor": BG_PANEL,
    "figure.facecolor": BG_PANEL,
    "axes.edgecolor": BORDER,
    "axes.labelcolor": FG_TEXT,
    "text.color": FG_TEXT,
    "xtick.color": FG_TEXT,
    "ytick.color": FG_TEXT,
    "axes.titlecolor": FG_TEXT,
    "axes.titleweight": "bold",
    "font.family": "Segoe UI",
    "font.size": 9,
    "axes.grid": True,
    "grid.color": "#dde6ea",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def _annotate_bars(ax, horizontal=False, fmt="{:.0f}", offset=2.0):
    """Pone valores en cada barra en color navy oscuro para contrastar sobre el panel claro."""
    for p in ax.patches:
        if horizontal:
            w = p.get_width()
            if w == 0:
                continue
            ax.text(w + offset, p.get_y() + p.get_height() / 2,
                    fmt.format(w), va="center", ha="left",
                    color=FG_TEXT, fontsize=8, fontweight="bold")
        else:
            h = p.get_height()
            if h == 0:
                continue
            ax.text(p.get_x() + p.get_width() / 2, h + offset,
                    fmt.format(h), ha="center", va="bottom",
                    color=FG_TEXT, fontsize=8, fontweight="bold")


class Dashboard(tk.Tk):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df_full = df
        self.df = df.copy()

        self.title("Clínica Veterinaria — Dashboard de Cuidado de Mascotas")
        self.geometry("1500x920")
        self.configure(bg=BG_DARK)
        self.minsize(1100, 750)
        # Inicia maximizado (en Windows). Si falla, queda con el geometry anterior.
        try:
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass

        try:
            self._base_tk_scaling = float(self.tk.call("tk", "scaling"))
        except tk.TclError:
            self._base_tk_scaling = 1.333

        self._setup_style()
        self._build_layout()
        self._populate_filters()
        # Mapa de pestañas → función dibujadora (lazy redraw)
        self._drawers = {
            "Resumen": self._draw_resumen,
            "Castración": self._draw_castracion,
            "Geografía": self._draw_geografia,
            "Barrios Prioritarios": self._draw_barrios_prio,
            "Municipio": self._draw_municipio,
            "Cuidado": self._draw_cuidado,
            "Callejeros": self._draw_callejeros,
            "Brecha Informativa": self._draw_brecha,
            "Insights": self._draw_insights,
            "Salud Pública": self._draw_salud,
            "Demografía": self._draw_demografia,
            "Acción Municipal": self._draw_accion_mun,
            "Tabla": self._draw_tabla,
        }
        self._dirty = set(self._drawers.keys())  # pestañas que necesitan redraw
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        # Diferimos el primer dibujado hasta que el layout de la ventana
        # esté asentado: si dibujamos antes, la Figure se renderiza con su
        # figsize por defecto (11×6) y queda más ancha que el viewport real.
        self.after(50, self._refresh_all)

    # ── Estilos ttk ───────────────────────────────────────────────────────
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BG_DARK, foreground=FG_TEXT, fieldbackground=BG_PANEL)
        style.configure("TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_DARK, foreground=ACCENT,
                        font=("Segoe UI", 17, "bold"))
        style.configure("Subtitle.TLabel", background=BG_DARK, foreground=FG_TEXT,
                        font=("Segoe UI", 10, "italic"))
        style.configure("KPI.TLabel", background=BG_CARD, foreground=ACCENT,
                        font=("Segoe UI", 16, "bold"))
        style.configure("KPILabel.TLabel", background=BG_CARD, foreground=FG_TEXT,
                        font=("Segoe UI", 8))
        style.configure("FilterLabel.TLabel", background=BG_PANEL, foreground=FG_TEXT,
                        font=("Segoe UI", 9, "bold"))
        style.configure("TCombobox", fieldbackground=BG_PANEL, background=BG_PANEL,
                        foreground=FG_TEXT, arrowcolor=ACCENT, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_PANEL)],
                  foreground=[("readonly", FG_TEXT)])
        style.configure("Accent.TButton", background=ACCENT, foreground=TEXT_ON_ACCENT,
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(14, 7))
        style.map("Accent.TButton",
                  background=[("active", "#21867a"), ("pressed", "#1f7a6f")])
        style.configure("Toggle.TButton", background=BG_PANEL, foreground=FG_TEXT,
                        font=("Segoe UI", 9), borderwidth=1, padding=(8, 4))
        style.map("Toggle.TButton",
                  background=[("active", "#d6ede9"), ("pressed", ACCENT)])
        style.configure("TNotebook", background=BG_DARK, borderwidth=0, tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_TEXT,
                        padding=(10, 6), font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT), ("active", "#d6ede9")],
                  foreground=[("selected", TEXT_ON_ACCENT)])
        # Treeview clínico (claro)
        style.configure("Treeview",
                        background=BG_PANEL, fieldbackground=BG_PANEL,
                        foreground=FG_TEXT, rowheight=26,
                        borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=ACCENT, foreground=TEXT_ON_ACCENT,
                        font=("Segoe UI", 9, "bold"), relief="flat",
                        padding=(6, 6))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT_ON_ACCENT)])
        style.map("Treeview.Heading",
                  background=[("active", "#21867a")])

    # ── Toggles de paneles (filtros / KPIs) ──────────────────────────────
    def _toggle_filters(self):
        if self.show_filters.get():
            self.filter_frame.pack_forget()
            self.show_filters.set(False)
            self.btn_filters.configure(text="▼ Filtros")
        else:
            # Re-empaqueta antes del frame de KPIs (o del notebook si KPIs ocultos)
            anchor = self.kpi_frame if self.show_kpis.get() else self.notebook
            self.filter_frame.pack(fill="x", padx=15, pady=5, before=anchor)
            self.show_filters.set(True)
            self.btn_filters.configure(text="▲ Filtros")

    def _toggle_kpis(self):
        if self.show_kpis.get():
            self.kpi_frame.pack_forget()
            self.show_kpis.set(False)
            self.btn_kpis.configure(text="▼ Indicadores")
        else:
            self.kpi_frame.pack(fill="x", padx=15, pady=8, before=self.notebook)
            self.show_kpis.set(True)
            self.btn_kpis.configure(text="▲ Indicadores")

    # ── Layout ────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Encabezado
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=15, pady=(12, 2))
        title_box = ttk.Frame(header, style="TFrame")
        title_box.pack(side="left")
        ttk.Label(title_box, text="🐾 Clínica Veterinaria",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box,
                  text="Sistema de análisis del cuidado de mascotas",
                  style="Subtitle.TLabel").pack(anchor="w")
        ttk.Button(header, text="↻ Resetear filtros", style="Accent.TButton",
                   command=self._reset_filters).pack(side="right")

        # Toggles para mostrar/ocultar paneles
        toggles_box = ttk.Frame(header, style="TFrame")
        toggles_box.pack(side="right", padx=(0, 10))
        self.show_filters = tk.BooleanVar(value=True)
        self.show_kpis = tk.BooleanVar(value=True)
        self.btn_filters = ttk.Button(toggles_box, text="▲ Filtros",
                                      style="Toggle.TButton",
                                      command=self._toggle_filters)
        self.btn_filters.pack(side="left", padx=2)
        self.btn_kpis = ttk.Button(toggles_box, text="▲ Indicadores",
                                   style="Toggle.TButton",
                                   command=self._toggle_kpis)
        self.btn_kpis.pack(side="left", padx=2)
        _Tooltip(self.btn_filters, "Mostrar / ocultar barra de filtros")
        _Tooltip(self.btn_kpis, "Mostrar / ocultar panel de indicadores (KPIs)")

        # Botones de zoom de área
        zoom_box = ttk.Frame(header, style="TFrame")
        zoom_box.pack(side="right", padx=(0, 10))
        self.btn_area_zoom = ttk.Button(zoom_box, text="🔍 Zoom área",
                                        style="Toggle.TButton",
                                        command=self._toggle_area_zoom)
        self.btn_area_zoom.pack(side="left", padx=2)
        ttk.Button(zoom_box, text="↺ Reset",
                   style="Toggle.TButton",
                   command=self._reset_area_zoom).pack(side="left", padx=2)
        _Tooltip(self.btn_area_zoom,
                 "Activar y arrastrar un rectángulo sobre el tablero\n"
                 "para ampliar esa región. Reset vuelve al tamaño original.")

        # Panel de filtros
        self.filter_frame = ttk.Frame(self, style="Panel.TFrame", padding=10)
        self.filter_frame.pack(fill="x", padx=15, pady=5)

        # Panel de KPIs
        self.kpi_frame = ttk.Frame(self, style="TFrame")
        self.kpi_frame.pack(fill="x", padx=15, pady=8)

        # Notebook con pestañas de gráficos
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(5, 12))

        self.tabs = {}
        # Para pestañas de gráficos: figura+canvas persistentes (evita parpadeo blanco)
        self.tab_figs = {}
        self.tab_canvases = {}
        # Wrapper info para zoom de área (canvas Tk del scroll + window id)
        self.tab_wrappers = {}
        self.area_zoom_mode = False
        chart_tabs = ["Resumen", "Castración", "Geografía", "Barrios Prioritarios",
                      "Municipio", "Cuidado", "Callejeros", "Brecha Informativa",
                      "Insights", "Salud Pública", "Demografía", "Acción Municipal"]
        for nombre in chart_tabs + ["Tabla"]:
            tab = ttk.Frame(self.notebook, style="Panel.TFrame")
            self.notebook.add(tab, text=nombre)
            self.tabs[nombre] = tab
            if nombre in chart_tabs:
                # Toolbar de matplotlib (zoom, pan, home, guardar) — arriba, fija
                tb_frame = tk.Frame(tab, bg=BG_PANEL, height=32)
                tb_frame.pack(side="top", fill="x")
                # Contenedor scrolleable debajo de la toolbar.
                inner, wrapper = self._make_scrollable(tab)
                fig = Figure(figsize=(11, 6.0), dpi=100, facecolor=BG_PANEL)
                canvas = FigureCanvasTkAgg(fig, master=inner)
                widget = canvas.get_tk_widget()
                widget.configure(bg=BG_PANEL, highlightthickness=0)
                widget.pack(fill="both", expand=True)
                # Crear toolbar y enlazarlo al canvas (el botón "save" funciona igual)
                toolbar = NavigationToolbar2Tk(canvas, tb_frame, pack_toolbar=False)
                try:
                    toolbar.configure(bg=BG_PANEL)  # type: ignore[call-arg]
                except tk.TclError:
                    pass
                for child in toolbar.winfo_children():
                    try:
                        child.configure(bg=BG_PANEL)  # type: ignore[call-arg]
                    except tk.TclError:
                        pass
                toolbar.update()
                toolbar.pack(side="left")
                self.tabs[nombre] = inner
                self.tab_figs[nombre] = fig
                self.tab_canvases[nombre] = canvas
                self.tab_wrappers[nombre] = wrapper
                # IMPORTANTE: usar add="+" para NO pisar el handler interno
                # de matplotlib que redimensiona la Figure al tamaño del
                # widget. Si lo pisáramos, la figura quedaría fija en su
                # figsize inicial y se cortarían los gráficos.
                widget.bind("<Configure>",
                            lambda e, n=nombre: self._on_canvas_resize(n, e.width, e.height),
                            add="+")

    # ── Scroll wrapper ────────────────────────────────────────────────────
    def _make_scrollable(self, parent):
        """Envuelve `parent` con un Canvas + scrollbars y devuelve
        (inner_frame, wrapper_dict). Cuando NO hay zoom el inner se ajusta
        al viewport; el zoom de área hace al inner más grande para que
        las scrollbars permitan recorrer la región ampliada."""
        container = tk.Frame(parent, bg=BG_PANEL)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=BG_PANEL, highlightthickness=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        hbar = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        vbar.pack(side="right", fill="y")
        hbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG_PANEL)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        wrapper = {"canvas": canvas, "win": win, "inner": inner, "zoomed": False}

        def _on_canvas_config(_e):
            # Solo auto-ajustar al viewport si NO hay zoom activo
            if not wrapper["zoomed"]:
                try:
                    cw = canvas.winfo_width()
                    ch = canvas.winfo_height()
                    canvas.itemconfigure(win, width=cw, height=ch)
                    canvas.configure(scrollregion=(0, 0, cw, ch))
                except tk.TclError:
                    pass
        canvas.bind("<Configure>", _on_canvas_config)

        # Scroll con la rueda del mouse cuando el cursor está sobre el área
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def _on_shift_wheel(e):
            canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
        def _bind_wheel(_e):
            canvas.bind_all("<MouseWheel>", _on_wheel)
            canvas.bind_all("<Shift-MouseWheel>", _on_shift_wheel)
        def _unbind_wheel(_e):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Shift-MouseWheel>")
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        inner.bind("<Enter>", _bind_wheel)
        inner.bind("<Leave>", _unbind_wheel)
        return inner, wrapper

    # ── Zoom de área (drag-rectangle) ─────────────────────────────────────
    def _toggle_area_zoom(self):
        """Activa/desactiva el modo selección de área para zoom."""
        self.area_zoom_mode = not self.area_zoom_mode
        for nombre, canvas in self.tab_canvases.items():
            widget = canvas.get_tk_widget()
            try:
                if self.area_zoom_mode:
                    widget.configure(cursor="crosshair")
                    widget.bind("<ButtonPress-1>",
                                lambda e, n=nombre: self._area_press(n, e),
                                add="+")
                    widget.bind("<B1-Motion>",
                                lambda e, n=nombre: self._area_motion(n, e),
                                add="+")
                    widget.bind("<ButtonRelease-1>",
                                lambda e, n=nombre: self._area_release(n, e),
                                add="+")
                else:
                    widget.configure(cursor="")
                    widget.unbind("<ButtonPress-1>")
                    widget.unbind("<B1-Motion>")
                    widget.unbind("<ButtonRelease-1>")
            except tk.TclError:
                pass
        self.btn_area_zoom.configure(
            text="✓ Selecciona área…" if self.area_zoom_mode else "🔍 Zoom área")

    def _area_press(self, nombre, event):
        self._area_start = (event.x, event.y)
        self._area_rect_id = None

    def _area_motion(self, nombre, event):
        widget = self.tab_canvases[nombre].get_tk_widget()
        # FigureCanvasTkAgg.get_tk_widget() es un tk.Canvas → podemos dibujar
        if getattr(self, "_area_rect_id", None) is not None:
            try:
                widget.delete(self._area_rect_id)
            except tk.TclError:
                pass
        x0, y0 = self._area_start
        try:
            self._area_rect_id = widget.create_rectangle(
                x0, y0, event.x, event.y,
                outline=ACCENT, width=2, dash=(5, 3))
        except tk.TclError:
            self._area_rect_id = None

    def _area_release(self, nombre, event):
        widget = self.tab_canvases[nombre].get_tk_widget()
        if getattr(self, "_area_rect_id", None) is not None:
            try:
                widget.delete(self._area_rect_id)
            except tk.TclError:
                pass
            self._area_rect_id = None
        if not getattr(self, "_area_start", None):
            return
        x0, y0 = self._area_start
        x1, y1 = event.x, event.y
        rx0, rx1 = sorted((max(0, x0), max(0, x1)))
        ry0, ry1 = sorted((max(0, y0), max(0, y1)))
        rect_w = rx1 - rx0
        rect_h = ry1 - ry0
        # Selección muy chica → ignorar
        if rect_w < 25 or rect_h < 25:
            self._toggle_area_zoom()
            return
        wrapper = self.tab_wrappers.get(nombre)
        if wrapper is None:
            self._toggle_area_zoom()
            return
        wc = wrapper["canvas"]
        win = wrapper["win"]
        # Dimensión actual del widget (lo que se ve antes del zoom)
        cur_w = widget.winfo_width()
        cur_h = widget.winfo_height()
        if cur_w < 10 or cur_h < 10:
            self._toggle_area_zoom()
            return
        # ── Expandir la selección para no cortar gráficos ────────────────
        # Si el rectángulo cae sobre uno o más Axes, expandimos el rect para
        # incluir el bbox completo de cada Axes tocado (incluye títulos /
        # etiquetas). Coords matplotlib: origen abajo-izq → invertimos Y.
        fig = self.tab_figs[nombre]
        try:
            renderer = fig.canvas.get_renderer()
            ex0, ey0, ex1, ey1 = rx0, ry0, rx1, ry1
            tocados = False
            for ax in fig.axes:
                try:
                    bb = ax.get_tightbbox(renderer)
                except Exception:
                    bb = ax.get_window_extent()
                if bb is None:
                    continue
                ax_x0 = float(bb.x0)
                ax_x1 = float(bb.x1)
                ax_y0 = cur_h - float(bb.y1)
                ax_y1 = cur_h - float(bb.y0)
                # Intersección con el rect del usuario
                if ax_x1 < rx0 or ax_x0 > rx1:
                    continue
                if ax_y1 < ry0 or ax_y0 > ry1:
                    continue
                tocados = True
                if ax_x0 < ex0:
                    ex0 = ax_x0
                if ax_y0 < ey0:
                    ey0 = ax_y0
                if ax_x1 > ex1:
                    ex1 = ax_x1
                if ax_y1 > ey1:
                    ey1 = ax_y1
            if tocados:
                # Pequeño margen para que no quede pegado al borde
                pad = 8
                rx0 = max(0, int(ex0) - pad)
                ry0 = max(0, int(ey0) - pad)
                rx1 = min(cur_w, int(ex1) + pad)
                ry1 = min(cur_h, int(ey1) + pad)
                rect_w = rx1 - rx0
                rect_h = ry1 - ry0
        except Exception:
            pass
        if rect_w < 10 or rect_h < 10:
            self._toggle_area_zoom()
            return
        # Escala para que el rect llene el viewport (mantiene aspecto)
        scale = min(cur_w / rect_w, cur_h / rect_h)
        new_w = int(cur_w * scale)
        new_h = int(cur_h * scale)
        # Aplicar al inner + Figure
        wrapper["zoomed"] = True
        wc.itemconfigure(win, width=new_w, height=new_h)
        wc.configure(scrollregion=(0, 0, new_w, new_h))
        dpi = fig.get_dpi()
        try:
            fig.set_size_inches(new_w / dpi, new_h / dpi, forward=False)
        except Exception:
            pass
        # Redibujar y posicionar el scroll para que la región seleccionada
        # quede visible en la parte superior-izquierda del viewport.
        self._dirty.add(nombre)
        try:
            self._drawers[nombre]()
            self._dirty.discard(nombre)
        except Exception:
            pass
        self.update_idletasks()
        try:
            wc.xview_moveto((rx0 * scale) / new_w)
            wc.yview_moveto((ry0 * scale) / new_h)
        except tk.TclError:
            pass
        # Salir del modo selección automáticamente
        self._toggle_area_zoom()

    def _reset_area_zoom(self):
        """Vuelve todas las pestañas al tamaño que llena el viewport."""
        for nombre, wrapper in self.tab_wrappers.items():
            wrapper["zoomed"] = False
            wc = wrapper["canvas"]
            win = wrapper["win"]
            cw = max(wc.winfo_width(), 1)
            ch = max(wc.winfo_height(), 1)
            try:
                wc.itemconfigure(win, width=cw, height=ch)
                wc.configure(scrollregion=(0, 0, cw, ch))
            except tk.TclError:
                pass
            fig = self.tab_figs.get(nombre)
            if fig is not None:
                dpi = fig.get_dpi()
                try:
                    fig.set_size_inches(cw / dpi, ch / dpi, forward=False)
                except Exception:
                    pass
        self.update_idletasks()
        self._dirty = set(self._drawers.keys())
        try:
            self._on_tab_changed()
        except Exception:
            pass

    # ── Filtros ───────────────────────────────────────────────────────────
    def _populate_filters(self):
        self.filter_vars = {}
        self.filter_defaults = {}
        opciones = {
            "Ciudad": ["(Todas)"] + sorted(self.df_full["Ciudad"].dropna().unique().tolist()),
            "Barrio": ["(Todos)"] + sorted(self.df_full["Barrio"].dropna().unique().tolist()),
            "Tipo_Vivienda": ["(Todas)"] + sorted(self.df_full["Tipo_Vivienda"].dropna().unique().tolist()),
            "Tipo_Mascotas": ["(Todas)", "Perros", "Gatos", "Mixto"],
            "Castrada": ["(Todas)", "Si", "No"],
            "Vacunadas": ["(Todas)", "Si", "No"],
            "Desparasitadas": ["(Todas)", "Si", "No"],
            "Sabe_Castracion_Gratuita": ["(Todas)", "Si", "No"],
        }
        # Distribuir en 2 filas (4 filtros por fila)
        per_row = 4
        for i, (campo, opts) in enumerate(opciones.items()):
            r, c = i // per_row, (i % per_row) * 2
            ttk.Label(self.filter_frame, text=friendly(campo) + ":",
                      style="FilterLabel.TLabel").grid(row=r, column=c, padx=(8, 4), pady=3, sticky="w")
            var = tk.StringVar(value=opts[0])
            cb = ttk.Combobox(self.filter_frame, textvariable=var, values=opts,
                              state="readonly", width=18)
            cb.grid(row=r, column=c+1, padx=(0, 12), pady=3, sticky="w")
            cb.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
            self.filter_vars[campo] = var
            self.filter_defaults[campo] = opts[0]

    def _reset_filters(self):
        for campo, var in self.filter_vars.items():
            var.set(self.filter_defaults[campo])
        self._apply_filters()

    def _apply_filters(self):
        df = self.df_full.copy()
        c = self.filter_vars["Ciudad"].get()
        if not c.startswith("("):
            df = df[df["Ciudad"] == c]
        b = self.filter_vars["Barrio"].get()
        if not b.startswith("("):
            df = df[df["Barrio"] == b]
        v = self.filter_vars["Tipo_Vivienda"].get()
        if not v.startswith("("):
            df = df[df["Tipo_Vivienda"] == v]
        t = self.filter_vars["Tipo_Mascotas"].get()
        if not t.startswith("("):
            if t == "Mixto":
                df = df[df["Tipo_Mascotas"].str.contains(";", na=False)]
            else:
                df = df[(df["Tipo_Mascotas"] == t)]
        cas = self.filter_vars["Castrada"].get()
        if not cas.startswith("("):
            df = df[df["Mascota_Castrada"] == cas]
        vac = self.filter_vars["Vacunadas"].get()
        if not vac.startswith("(") and "Vacunadas" in df.columns:
            df = df[df["Vacunadas"] == vac]
        des = self.filter_vars["Desparasitadas"].get()
        if not des.startswith("(") and "Desparasitadas" in df.columns:
            df = df[df["Desparasitadas"] == des]
        sg = self.filter_vars["Sabe_Castracion_Gratuita"].get()
        if not sg.startswith("(") and "Sabe_Castracion_Gratuita" in df.columns:
            df = df[df["Sabe_Castracion_Gratuita"] == sg]
        self.df = df
        self._refresh_all()

    # ── Refresh ───────────────────────────────────────────────────────────
    def _refresh_all(self):
        """Marca todas las pestañas como sucias y redibuja KPIs + la activa."""
        self._draw_kpis()
        self._dirty = set(self._drawers.keys())
        self._draw_active_tab()

    def _on_tab_changed(self, _event=None):
        self._draw_active_tab()

    def _draw_active_tab(self):
        try:
            idx = self.notebook.index(self.notebook.select())
            nombre = self.notebook.tab(idx, "text")
        except tk.TclError:
            return
        if nombre in self._dirty:
            self._drawers[nombre]()
            self._dirty.discard(nombre)

    def _clear(self, frame):
        for w in frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _redraw_fig(self, nombre, build_fn):
        """Limpia la figura persistente de la pestaña y la rellena con `build_fn(fig)`."""
        fig = self.tab_figs[nombre]
        fig.clear()
        # constrained_layout maneja mejor grids 2×2 con títulos largos, leyendas
        # y colorbars (evita que se corten los ejes). Padding extra para que los
        # títulos no toquen el borde derecho de la figura.
        try:
            fig.set_layout_engine("constrained")
            try:
                fig.get_layout_engine().set(w_pad=0.04, h_pad=0.04,
                                            wspace=0.03, hspace=0.03)
            except Exception:
                pass
        except Exception:
            pass
        build_fn(fig)
        self.tab_canvases[nombre].draw_idle()

    def _on_canvas_resize(self, nombre, w_px, h_px):
        """Cuando cambia el tamaño del widget, programa un redibujado en
        diferido (debounce). El handler interno de matplotlib ya se ocupa
        de redimensionar la Figure al tamaño del widget; nosotros solo
        necesitamos volver a dibujar para que constrained_layout reacomode."""
        if w_px < 50 or h_px < 50:
            return
        prev = getattr(self, "_resize_jobs", {}).get(nombre)
        if prev is not None:
            try:
                self.after_cancel(prev)
            except Exception:
                pass
        if not hasattr(self, "_resize_jobs"):
            self._resize_jobs = {}
        self._resize_jobs[nombre] = self.after(150, lambda: self._do_resize_redraw(nombre))

    def _do_resize_redraw(self, nombre):
        self._dirty.add(nombre)
        try:
            idx = self.notebook.index(self.notebook.select())
            activa = self.notebook.tab(idx, "text")
        except tk.TclError:
            activa = None
        if activa == nombre:
            self._drawers[nombre]()
            self._dirty.discard(nombre)

    # ── KPIs ──────────────────────────────────────────────────────────────
    def _draw_kpis(self):
        self._clear(self.kpi_frame)
        df = self.df
        n = len(df)
        if n == 0:
            ttk.Label(self.kpi_frame, text="⚠ No hay datos con los filtros aplicados",
                      style="Title.TLabel").pack()
            return

        def pct(col):
            return f"{(df[col] == 'Si').mean() * 100:.1f}%" if n > 0 else "—"

        total_perros = pd.to_numeric(df["Perros_Macho"], errors="coerce").fillna(0).sum() + \
                       pd.to_numeric(df["Perros_Hembra"], errors="coerce").fillna(0).sum()
        total_gatos = pd.to_numeric(df["Gatos_Macho"], errors="coerce").fillna(0).sum() + \
                      pd.to_numeric(df["Gatos_Hembra"], errors="coerce").fillna(0).sum()
        total_animales = int(total_perros + total_gatos)

        # Estimación de animales sin castrar: hogares no castrados × prom. mascotas/hogar
        sin_castrar_hog = int((df["Mascota_Castrada"] == "No").sum())
        if sin_castrar_hog > 0:
            tot_no_cast = pd.to_numeric(
                df.loc[df["Mascota_Castrada"] == "No", "Total_Mascotas"],
                errors="coerce").fillna(0).sum()
            animales_sin_cast = int(tot_no_cast)
        else:
            animales_sin_cast = 0

        # % de mascotas sin identificador (col Vive_Tienen_identificador == 1 → con ID)
        col_id = next((c for c in df.columns if c.startswith("Vive_Tienen")), None)
        if col_id:
            sin_id_pct = (1 - pd.to_numeric(df[col_id], errors="coerce").fillna(0).mean()) * 100
            sin_id_str = f"{sin_id_pct:.0f}%"
        else:
            sin_id_str = "—"

        # % de mascotas que salen solas a la calle
        col_solo = next((c for c in df.columns if c.startswith("Vive_Salen_solos")), None)
        if col_solo:
            salen_pct = pd.to_numeric(df[col_solo], errors="coerce").fillna(0).mean() * 100
            salen_str = f"{salen_pct:.0f}%"
        else:
            salen_str = "—"

        kpis = [
            ("Encuestas", f"{n:,}", ACCENT, None),
            ("🐾 Total Animales", f"{total_animales:,}", ACCENT,
             "Suma total de perros + gatos declarados\nen los hogares filtrados."),
            ("🐶 Perros", f"{int(total_perros):,}", GREEN, None),
            ("🐱 Gatos", f"{int(total_gatos):,}", PURPLE, None),
            ("% Castradas", pct("Mascota_Castrada"), YELLOW,
             "Porcentaje de hogares en los que la\nmascota está castrada."),
            ("⚠ Sin Castrar (aprox)", f"{animales_sin_cast:,}", RED,
             "ESTIMACIÓN APROXIMADA.\n\n"
             "El formulario registra castración a nivel HOGAR\n"
             "(Sí / No), no por animal individual.\n\n"
             "Para estimar el volumen, se suma 'Total_Mascotas'\n"
             "de cada hogar que respondió 'No castrada'.\n\n"
             "Es una cota superior: un hogar con 3 perros donde\n"
             "1 sí está castrado y 2 no, igual cuenta como 3."),
            ("% Vacunadas", pct("Vacunadas"), GREEN, None),
            ("% Desparasit.", pct("Desparasitadas"), GREEN, None),
            ("% Sin chapita/microchip", sin_id_str, RED,
             "Porcentaje de hogares cuyas mascotas NO tienen\n"
             "ningún identificador (chapita con datos del dueño,\n"
             "collar identificatorio o microchip).\n\n"
             "Una mascota perdida sin ID suele terminar\n"
             "como callejera."),
            ("% Salen solos a la calle", salen_str, YELLOW,
             "Porcentaje de hogares que dejan que sus\n"
             "mascotas salgan solas a la vía pública."),
            ("% Sabe Cast. Gratis", pct("Sabe_Castracion_Gratuita"), ACCENT,
             "Porcentaje de hogares que sabe que el\n"
             "municipio ofrece castración gratuita."),
        ]
        # Reorganiza en 2 filas para no invadir el área de gráficos
        per_row = (len(kpis) + 1) // 2
        for i, (label, value, color, tip) in enumerate(kpis):
            r, c = i // per_row, i % per_row
            card = ttk.Frame(self.kpi_frame, style="Card.TFrame", padding=8)
            card.grid(row=r, column=c, padx=3, pady=2, sticky="nsew")
            self.kpi_frame.columnconfigure(c, weight=1)
            v = ttk.Label(card, text=value, style="KPI.TLabel")
            v.configure(foreground=color)
            v.pack()
            lbl = ttk.Label(card, text=label, style="KPILabel.TLabel")
            lbl.pack()
            if tip:
                _Tooltip(card, tip)

    # ── Resumen ───────────────────────────────────────────────────────────
    def _draw_resumen(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            ax1 = fig.add_subplot(2, 2, 1)
            df["Tipo_Mascotas"].value_counts().plot(
                kind="barh", ax=ax1, color=ACCENT, edgecolor=BG_DARK)
            ax1.set_title("Tipo de mascotas en el hogar")
            ax1.set_xlabel(""); ax1.set_ylabel("")
            ax1.invert_yaxis()
            _annotate_bars(ax1, horizontal=True)

            ax2 = fig.add_subplot(2, 2, 2)
            df["Tipo_Vivienda"].value_counts().plot(
                kind="bar", ax=ax2, color=PURPLE, edgecolor=BG_DARK)
            ax2.set_title("Tipo de vivienda")
            ax2.set_xlabel(""); ax2.set_ylabel("")
            ax2.tick_params(axis="x", rotation=20)
            _annotate_bars(ax2)

            ax3 = fig.add_subplot(2, 2, 3)
            df["Frecuencia_Callejeros"].value_counts().plot(
                kind="bar", ax=ax3, color=YELLOW, edgecolor=BG_DARK)
            ax3.set_title("Frecuencia de callejeros observados")
            ax3.set_xlabel(""); ax3.set_ylabel("")
            ax3.tick_params(axis="x", rotation=15)
            _annotate_bars(ax3)

            ax4 = fig.add_subplot(2, 2, 4)
            hr = df["Humano_Responsable"].value_counts()
            ax4.pie(hr.values, autopct="%1.0f%%",
                    colors=[GREEN, YELLOW, RED][:len(hr)],
                    textprops={"color": TEXT_ON_ACCENT, "fontweight": "bold", "fontsize": 10},
                    wedgeprops={"edgecolor": BG_PANEL, "linewidth": 2})
            ax4.set_title("¿Te considerás humano responsable?")
            ax4.set_ylabel("")
            ax4.legend(hr.index, loc="center left", bbox_to_anchor=(1.0, 0.5),
                       fontsize=8, frameon=False)
        self._redraw_fig("Resumen", build)

    # ── Castración ────────────────────────────────────────────────────────
    def _draw_castracion(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            ax1 = fig.add_subplot(1, 3, 1)
            mc = df["Mascota_Castrada"].value_counts()
            ax1.pie(mc.values, autopct="%1.1f%%", colors=[GREEN, RED][:len(mc)],
                    textprops={"color": TEXT_ON_ACCENT, "fontweight": "bold", "fontsize": 11},
                    wedgeprops={"edgecolor": BG_PANEL, "linewidth": 2})
            ax1.set_title("Mascotas castradas")
            ax1.set_xlabel(""); ax1.set_ylabel("")
            ax1.legend([f"{lbl} (castrada)" if lbl == "Si" else f"{lbl} (sin castrar)"
                        for lbl in mc.index],
                       loc="center left", bbox_to_anchor=(1.0, 0.5),
                       fontsize=8, frameon=False)

            ax2 = fig.add_subplot(1, 3, 2)
            cast_en = [c for c in df.columns if c.startswith("CastEn_")]
            if cast_en:
                sums = df[cast_en].sum().sort_values(ascending=True)
                # Etiquetas legibles con saltos de línea (no se cortan)
                sums.index = ["\n".join(textwrap.wrap(
                                  c.replace("CastEn_", "").replace("_", " "),
                                  width=22)) or c
                              for c in sums.index]
                sums.plot(kind="barh", ax=ax2, color=ACCENT, edgecolor=BG_DARK)
                ax2.set_title("¿Dónde castraron?")
                ax2.set_xlabel(""); ax2.set_ylabel("")
                ax2.tick_params(axis="y", labelsize=8)
                if sums.max() > 0:
                    ax2.set_xlim(0, sums.max() * 1.18)
                _annotate_bars(ax2, horizontal=True)

            ax3 = fig.add_subplot(1, 3, 3)
            sabe = df.groupby("Sabe_Castracion_Gratuita")["Mascota_Castrada"].apply(
                lambda s: (s == "Si").mean() * 100)
            sabe.plot(kind="bar", ax=ax3, color=[YELLOW, GREEN], edgecolor=BG_DARK)
            ax3.set_title("% de castradas según\nsi sabe que es gratuita")
            ax3.set_ylabel("% castradas")
            ax3.set_xlabel("¿Sabe que es gratis?")
            ax3.tick_params(axis="x", rotation=0)
            ax3.set_ylim(0, max(100, (sabe.max() if len(sabe) else 0) * 1.15))
            _annotate_bars(ax3, fmt="{:.1f}%", offset=1.5)
        self._redraw_fig("Castración", build)

    # ── Geografía ─────────────────────────────────────────────────────────
    def _draw_geografia(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            ax1 = fig.add_subplot(1, 2, 1)
            top = df["Barrio"].value_counts().head(15).sort_values()
            top.plot(kind="barh", ax=ax1, color=ACCENT, edgecolor=BG_DARK)
            ax1.set_title("Top 15 barrios por cantidad de encuestas")
            if len(top) > 0:
                ax1.set_xlim(0, top.max() * 1.18)
            _annotate_bars(ax1, horizontal=True)

            ax2 = fig.add_subplot(1, 2, 2)
            g = df.groupby("Barrio").agg(
                n=("Mascota_Castrada", "size"),
                cast=("Mascota_Castrada", lambda s: (s == "Si").mean() * 100))
            g = g[g["n"] >= 3].sort_values("cast", ascending=True).tail(15)
            ax2.barh(g.index, g["cast"], color=GREEN, edgecolor=BG_DARK)
            ax2.set_title("% de castradas por barrio (≥3 encuestas)")
            ax2.set_xlabel("%")
            ax2.set_xlim(0, 115)
            for i, val in enumerate(g["cast"]):
                ax2.text(val + 1.5, i, f"{val:.0f}%", va="center",
                         fontsize=9, fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Geografía", build)

    # ── Municipio ─────────────────────────────────────────────────────────
    def _draw_municipio(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            mun_cols = [c for c in df.columns if c.startswith("Mun_")]

            def _mun_lbl(c, width=24):
                base = c.replace("Mun_", "").replace("_", " ")
                return "\n".join(textwrap.wrap(base, width=width)) or base

            # 1) Demanda total al municipio (% de hogares que pide cada cosa)
            ax1 = fig.add_subplot(2, 2, 1)
            if mun_cols:
                pcts = (df[mun_cols].sum() / len(df) * 100).sort_values(ascending=True)
                pcts.index = [_mun_lbl(c, 26) for c in pcts.index]
                pcts.plot(kind="barh", ax=ax1, color=PURPLE, edgecolor=BG_PANEL)
                ax1.set_title("¿Qué le pide la gente al municipio? (% de hogares)")
                ax1.set_xlim(0, max(pcts.max() * 1.18, 10))
                ax1.tick_params(axis="y", labelsize=8)
                for i, v in enumerate(pcts.values):
                    ax1.text(v + 0.5, i, f"{v:.0f}%", va="center",
                             fontsize=8, fontweight="bold", color=FG_TEXT)

            # 2) Top 4 pedidos vs castración (¿quién pide es quien lo necesita?)
            ax2 = fig.add_subplot(2, 2, 2)
            top4 = sorted([c for c in mun_cols], key=lambda c: -df[c].sum())[:4]
            if top4 and "Mascota_Castrada" in df.columns:
                rows = []
                for c in top4:
                    sub = df[df[c] == 1]
                    if len(sub) > 0:
                        rows.append((_mun_lbl(c, 22),
                                     (sub["Mascota_Castrada"] == "Si").mean() * 100))
                if rows:
                    labels = [r[0] for r in rows]
                    vals = [r[1] for r in rows]
                    bars = ax2.barh(labels, vals, color=ACCENT, edgecolor=BG_PANEL)
                    ax2.set_title("% castración entre quienes\npiden cada mejora")
                    ax2.set_xlim(0, 110)
                    ax2.set_xlabel("% de castradas")
                    ax2.tick_params(axis="y", labelsize=8)
                    for i, v in enumerate(vals):
                        ax2.text(v + 1.5, i, f"{v:.0f}%", va="center",
                                 fontsize=9, fontweight="bold", color=FG_TEXT)

            # 3) Pedidos al municipio por ciudad (heatmap simple)
            ax3 = fig.add_subplot(2, 2, 3)
            if mun_cols and "Ciudad" in df.columns:
                top5 = sorted(mun_cols, key=lambda c: -df[c].sum())[:5]
                pivot = df.groupby("Ciudad")[top5].mean() * 100
                pivot.columns = [_mun_lbl(c, 14) for c in pivot.columns]
                im = ax3.imshow(pivot.values, aspect="auto", cmap="YlOrRd",
                                vmin=0, vmax=100)
                ax3.set_xticks(range(len(pivot.columns)))
                ax3.set_xticklabels(pivot.columns, rotation=0, ha="center", fontsize=7)
                ax3.set_yticks(range(len(pivot.index)))
                ax3.set_yticklabels(pivot.index, fontsize=8)
                ax3.set_title("% que lo pide, por ciudad")
                for i in range(pivot.shape[0]):
                    for j in range(pivot.shape[1]):
                        v = pivot.values[i, j]
                        col = "white" if v > 50 else FG_TEXT
                        ax3.text(j, i, f"{v:.0f}", ha="center", va="center",
                                 color=col, fontsize=8, fontweight="bold")

            # 4) Castr. Masivas vs estado castración
            ax4 = fig.add_subplot(2, 2, 4)
            col_cm = "Mun_Castraciones_Masivas"
            if col_cm in df.columns:
                ct = pd.crosstab(df[col_cm].map({0: "No pide", 1: "Sí pide"}),
                                 df["Mascota_Castrada"])
                ct.plot(kind="bar", stacked=False, ax=ax4,
                        color=[RED, GREEN], edgecolor=BG_PANEL)
                ax4.set_title("¿Pide castraciones masivas?\nvs ¿está castrada su mascota?")
                ax4.set_xlabel("")
                ax4.tick_params(axis="x", rotation=0)
                ax4.legend(title="¿Castrada?", fontsize=8)
                _annotate_bars(ax4)
        self._redraw_fig("Municipio", build)

    # ── Cuidado sanitario ─────────────────────────────────────────────────
    def _draw_cuidado(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            ax1 = fig.add_subplot(1, 2, 1)
            cuidado = ["Mascota_Castrada", "Vacunadas", "Desparasitadas",
                       "Sabe_Castracion_Gratuita", "Sabe_Vacunas_Anuales"]
            pcts = [(df[c] == "Si").mean() * 100 for c in cuidado]
            labels = ["Castradas", "Vacunadas", "Desparasit.", "Sabe Cast.\nGratis", "Sabe Vac.\nAnuales"]
            bars = ax1.bar(labels, pcts, color=[YELLOW, GREEN, GREEN, ACCENT, ACCENT],
                           edgecolor=BG_DARK)
            ax1.set_title("Indicadores de cuidado (%)")
            ax1.set_ylim(0, 110)
            for bar, val in zip(bars, pcts):
                ax1.text(bar.get_x() + bar.get_width() / 2, val + 2,
                         f"{val:.1f}%", ha="center", fontsize=9, fontweight="bold",
                         color=FG_TEXT)

            ax2 = fig.add_subplot(1, 2, 2)
            g = df.groupby("Tipo_Vivienda").apply(
                lambda x: pd.Series({
                    "Castradas": (x["Mascota_Castrada"] == "Si").mean() * 100,
                    "Vacunadas": (x["Vacunadas"] == "Si").mean() * 100,
                    "Desparasit.": (x["Desparasitadas"] == "Si").mean() * 100,
                }))
            g.plot(kind="bar", ax=ax2, color=[YELLOW, GREEN, ACCENT], edgecolor=BG_DARK)
            ax2.set_title("Indicadores de cuidado por tipo de vivienda (%)")
            ax2.set_ylabel("%")
            ax2.set_ylim(0, 110)
            ax2.tick_params(axis="x", rotation=15)
            ax2.legend(loc="lower right", fontsize=8)
        self._redraw_fig("Cuidado", build)

    # ── Barrios prioritarios (volumen absoluto sin castrar) ────────────────
    def _draw_barrios_prio(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            no_cast = df[df["Mascota_Castrada"] == "No"].copy()
            if len(no_cast) == 0:
                fig.text(0.5, 0.5, "No hay hogares sin castrar en el filtro actual",
                         ha="center", va="center", color=FG_TEXT, fontsize=13)
                return
            no_cast["_anim"] = pd.to_numeric(no_cast["Total_Mascotas"],
                                             errors="coerce").fillna(1)
            g = no_cast.groupby("Barrio").agg(
                hogares=("_anim", "size"),
                animales=("_anim", "sum")).reset_index()
            tot_hog = df.groupby("Barrio").size().rename("total_hog")
            g = g.merge(tot_hog, on="Barrio", how="left")
            g["pct_sin"] = g["hogares"] / g["total_hog"] * 100
            g = g[g["total_hog"] >= 3].sort_values("animales", ascending=True).tail(15)

            ax1 = fig.add_subplot(1, 2, 1)
            colors = plt.get_cmap("Reds")([0.4 + 0.5 * (v / max(g["animales"].max(), 1))
                                              for v in g["animales"]])
            ax1.barh(g["Barrio"], g["animales"], color=colors, edgecolor=BG_PANEL)
            ax1.set_title("Top barrios por cantidad absoluta\nde animales sin castrar (≥3 encuestas)")
            ax1.set_xlabel("Cantidad estimada de animales sin castrar")
            for i, v in enumerate(g["animales"]):
                ax1.text(v + 0.2, i, f"{int(v)}", va="center",
                         fontsize=9, fontweight="bold", color=FG_TEXT)
            if g["animales"].max() > 0:
                ax1.set_xlim(0, g["animales"].max() * 1.18)

            ax2 = fig.add_subplot(1, 2, 2)
            g2 = g.sort_values("pct_sin", ascending=True)
            ax2.barh(g2["Barrio"], g2["pct_sin"], color=YELLOW, edgecolor=BG_PANEL)
            ax2.set_title("% de hogares sin mascotas castradas\nen los mismos barrios del gráfico anterior")
            ax2.set_xlabel("% de hogares sin castrar")
            ax2.set_xlim(0, 110)
            for i, v in enumerate(g2["pct_sin"]):
                ax2.text(v + 1.5, i, f"{v:.0f}%", va="center",
                         fontsize=8, fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Barrios Prioritarios", build)

    # ── Callejeros & riesgo en vía pública ────────────────────────────────
    def _draw_callejeros(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            # 1) Frecuencia de callejeros por ciudad (% Todo el tiempo)
            ax1 = fig.add_subplot(2, 2, 1)
            if "Frecuencia_Callejeros" in df.columns and "Ciudad" in df.columns:
                ct = pd.crosstab(df["Ciudad"], df["Frecuencia_Callejeros"], normalize="index") * 100
                ct = ct.reindex(columns=[c for c in ["Todo El Tiempo", "A Veces", "Nunca"]
                                          if c in ct.columns])
                ct.plot(kind="bar", stacked=True, ax=ax1,
                        color=[RED, YELLOW, GREEN], edgecolor=BG_PANEL)
                ax1.set_title("Frecuencia de callejeros observados, por ciudad (%)")
                ax1.set_ylabel("%")
                ax1.set_xlabel("")
                ax1.set_ylim(0, 100)
                ax1.tick_params(axis="x", rotation=20)
                ax1.legend(fontsize=7, loc="lower right")

            # 2) % salen solos a la calle por tipo de vivienda
            ax2 = fig.add_subplot(2, 2, 2)
            col_solo = next((c for c in df.columns if c.startswith("Vive_Salen_solos")), None)
            if col_solo:
                gs = df.groupby("Tipo_Vivienda")[col_solo].apply(
                    lambda s: pd.to_numeric(s, errors="coerce").fillna(0).mean() * 100
                ).sort_values(ascending=True)
                ax2.barh(gs.index, gs.values, color=YELLOW, edgecolor=BG_PANEL)
                ax2.set_title("% de mascotas que salen solas a la calle,\nsegún tipo de vivienda")
                ax2.set_xlabel("%")
                if gs.max() > 0:
                    ax2.set_xlim(0, max(gs.max() * 1.25, 15))
                for i, v in enumerate(gs.values):
                    ax2.text(v + 0.4, i, f"{v:.0f}%", va="center",
                             fontsize=9, fontweight="bold", color=FG_TEXT)

            # 3) Identificación: % con vs sin
            ax3 = fig.add_subplot(2, 2, 3)
            col_id = next((c for c in df.columns if c.startswith("Vive_Tienen")), None)
            if col_id:
                con_id = pd.to_numeric(df[col_id], errors="coerce").fillna(0).mean() * 100
                vals = [con_id, 100 - con_id]
                ax3.pie(vals,
                        autopct="%1.0f%%", colors=[GREEN, RED],
                        textprops={"color": TEXT_ON_ACCENT, "fontweight": "bold", "fontsize": 10},
                        wedgeprops={"edgecolor": BG_PANEL, "linewidth": 2})
                ax3.set_title("Mascotas con identificación (chapita o microchip)")
                ax3.legend(["Con identificador", "Sin identificador"],
                           loc="center left", bbox_to_anchor=(1.0, 0.5),
                           fontsize=8, frameon=False)

            # 4) Triple riesgo: callejeros altos + salen solos + sin ID por ciudad
            ax4 = fig.add_subplot(2, 2, 4)
            if col_solo and col_id and "Ciudad" in df.columns:
                rows = []
                for ciudad, sub in df.groupby("Ciudad"):
                    if "Frecuencia_Callejeros" in sub.columns:
                        cal_alto = (sub["Frecuencia_Callejeros"] == "Todo El Tiempo").mean() * 100
                    else:
                        cal_alto = 0
                    sol = pd.to_numeric(sub[col_solo], errors="coerce").fillna(0).mean() * 100
                    sin_id = (1 - pd.to_numeric(sub[col_id], errors="coerce").fillna(0).mean()) * 100
                    rows.append((ciudad, cal_alto, sol, sin_id))
                if rows:
                    rd = pd.DataFrame(rows, columns=["Ciudad", "Callej. alto",
                                                     "Salen solos", "Sin ID"]).set_index("Ciudad")
                    rd.plot(kind="bar", ax=ax4, color=[RED, YELLOW, PURPLE], edgecolor=BG_PANEL)
                    ax4.set_title("Indicadores de riesgo en la vía pública, por ciudad")
                    ax4.set_ylabel("%")
                    ax4.set_xlabel("")
                    ax4.tick_params(axis="x", rotation=15)
                    ax4.legend(fontsize=7)
        self._redraw_fig("Callejeros", build)

    # ── Brecha de información (sabe gratuita vs castra) ───────────────────
    def _draw_brecha(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return

            # Layout: arriba 2 paneles + abajo 1 panel ancho
            # (eliminado el duplicado del % castración por conocimiento
            #  — ya está en la pestaña Castración)
            gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.45, wspace=0.35)

            # 1) % Sabe gratuita: castrados vs no castrados
            ax1 = fig.add_subplot(gs[0, 0])
            if "Sabe_Castracion_Gratuita" in df.columns:
                g = df.groupby("Mascota_Castrada")["Sabe_Castracion_Gratuita"].apply(
                    lambda s: (s == "Si").mean() * 100)
                bars = ax1.bar(g.index, g.values, color=[RED, GREEN], edgecolor=BG_PANEL)
                ax1.set_title("% que conoce castración gratuita\nsegún si castró su mascota")
                ax1.set_ylabel("%")
                ax1.set_ylim(0, 110)
                for bar, val in zip(bars, g.values):
                    ax1.text(bar.get_x() + bar.get_width() / 2, val + 2,
                             f"{val:.0f}%", ha="center", fontsize=10,
                             fontweight="bold", color=FG_TEXT)

            # 2) Calendario vacunas conocido vs desconocido
            ax3 = fig.add_subplot(gs[0, 1])
            if "Sabe_Vacunas_Anuales" in df.columns:
                sv = df["Sabe_Vacunas_Anuales"].value_counts()
                ax3.pie(sv.values, autopct="%1.0f%%",
                        colors=[GREEN, RED][:len(sv)],
                        textprops={"color": TEXT_ON_ACCENT, "fontweight": "bold", "fontsize": 10},
                        wedgeprops={"edgecolor": BG_PANEL, "linewidth": 2})
                ax3.set_title("¿Sabe sobre vacunas anuales?")
                ax3.legend([f"{lbl} sabe" if lbl == "Si" else f"{lbl} sabe"
                            for lbl in sv.index],
                           loc="center left", bbox_to_anchor=(1.0, 0.5),
                           fontsize=8, frameon=False)

            # 3) Autopercepción vs práctica real (panel ancho abajo)
            ax4 = fig.add_subplot(gs[1, :])
            metricas = []
            if "Humano_Responsable" in df.columns:
                resp = (df["Humano_Responsable"] == "Si").mean() * 100
                metricas.append(("Se considera\nresponsable", resp))
            metricas.append(("Castra realm.", (df["Mascota_Castrada"] == "Si").mean() * 100))
            if "Vacunadas" in df.columns:
                metricas.append(("Vacuna realm.", (df["Vacunadas"] == "Si").mean() * 100))
            if "Desparasitadas" in df.columns:
                metricas.append(("Desparas. realm.", (df["Desparasitadas"] == "Si").mean() * 100))
            labels = [m[0] for m in metricas]
            vals = [m[1] for m in metricas]
            colors = [PURPLE, YELLOW, GREEN, ACCENT][:len(metricas)]
            bars = ax4.bar(labels, vals, color=colors, edgecolor=BG_PANEL)
            ax4.set_title("Autopercepción vs práctica real")
            ax4.set_ylim(0, 110)
            ax4.set_ylabel("%")
            ax4.tick_params(axis="x", labelsize=9)
            for bar, val in zip(bars, vals):
                ax4.text(bar.get_x() + bar.get_width() / 2, val + 2,
                         f"{val:.0f}%", ha="center", fontsize=10,
                         fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Brecha Informativa", build)

    # ── Insights / Conclusiones cruzadas ───────────────────────────────────
    def _draw_insights(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return

            n = len(df)
            col_solo = next((c for c in df.columns if c.startswith("Vive_Salen_solos")), None)
            col_id   = next((c for c in df.columns if c.startswith("Vive_Tienen")), None)

            # === Cálculos clave ===
            sin_cast = df["Mascota_Castrada"] == "No"
            sale = (pd.to_numeric(df[col_solo], errors="coerce").fillna(0) == 1) if col_solo else pd.Series([False]*n, index=df.index)
            sin_id = (pd.to_numeric(df[col_id], errors="coerce").fillna(0) == 0) if col_id else pd.Series([False]*n, index=df.index)
            triple_riesgo = sin_cast & sale & sin_id
            n_triple = int(triple_riesgo.sum())
            pct_triple = n_triple / n * 100

            # Convertibles fáciles: sabe que es gratis pero NO castró
            sabe = df["Sabe_Castracion_Gratuita"] == "Si"
            convertibles = sabe & sin_cast
            n_conv = int(convertibles.sum())

            # No informados: NO sabe + NO castró → necesitan campaña informativa
            no_inf = (df["Sabe_Castracion_Gratuita"] == "No") & sin_cast
            n_noinf = int(no_inf.sum())

            # Ya OK: castrados
            ok = ~sin_cast
            n_ok = int(ok.sum())

            # Camadas potenciales: hembras no castradas (perras + gatas) × 2 camadas/año × 4 crías
            no_cast_df = df[sin_cast]
            def _safe_sum(col):
                if col not in no_cast_df.columns:
                    return 0.0
                return float(pd.to_numeric(no_cast_df[col], errors="coerce").fillna(0).sum())
            hembras_riesgo = _safe_sum("Perros_Hembra") + _safe_sum("Gatos_Hembra")
            camadas_anio = int(hembras_riesgo * 2 * 4)

            # Brecha vacuna/desparasitación
            no_vac_no_des = ((df.get("Vacunadas") == "No") & (df.get("Desparasitadas") == "No")).sum()
            pct_no_vac_no_des = no_vac_no_des / n * 100

            # === Layout: 2x2 con texto explicativo ===

            # Helper: fondo "tarjeta" para los paneles de texto/KPI
            def _card(ax, color=BG_CARD, border_color=BORDER, border_width=1.2):
                ax.set_facecolor(color)
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_edgecolor(border_color)
                    spine.set_linewidth(border_width)
                ax.set_xticks([]); ax.set_yticks([])

            # ── 1) Hogares Críticos (triple riesgo) ──
            ax1 = fig.add_subplot(2, 2, 1)
            _card(ax1, color="#fff5f5", border_color=RED, border_width=2.0)
            ax1.set_title("  ▲  Hogares de TRIPLE riesgo",
                          fontsize=12, fontweight="bold",
                          color=RED, loc="left", pad=10,
                          bbox=dict(facecolor="#fde8e8", edgecolor="none",
                                    boxstyle="round,pad=0.3"))
            ax1.text(0.05, 0.63, f"{n_triple}", fontsize=54, fontweight="bold",
                     color=RED, transform=ax1.transAxes, va="center")
            ax1.text(0.43, 0.74, f"de {n} hogares",
                     fontsize=11, color=FG_TEXT, transform=ax1.transAxes)
            ax1.text(0.43, 0.60, f"({pct_triple:.1f}%)",
                     fontsize=15, fontweight="bold", color=RED,
                     transform=ax1.transAxes)
            explic = ("Combinan los 3 riesgos a la vez:\n"
                      "  •  Mascota SIN castrar\n"
                      "  •  Sale sola a la calle\n"
                      "  •  Sin chapita/microchip\n\n"
                      "→  Población PRIORITARIA para campañas\n"
                      "    de castración + identificación.")
            ax1.text(0.05, 0.37, explic, fontsize=9, color=FG_TEXT,
                     transform=ax1.transAxes, va="top", linespacing=1.6)

            # ── 2) Segmentación accionable (donut) ──
            ax2 = fig.add_subplot(2, 2, 2)
            seg_vals = [n_ok, n_conv, n_noinf]
            seg_lbls = ["Ya OK (castrados)",
                        "Convertibles fáciles\n(sabe gratis, no castró)",
                        "Necesitan info\n(no sabe, no castró)"]
            seg_cols = [GREEN, YELLOW, RED]
            wedges, _texts, autotexts = ax2.pie(
                seg_vals, autopct="%1.0f%%", colors=seg_cols,
                pctdistance=0.78,
                textprops={"color": TEXT_ON_ACCENT, "fontweight": "bold", "fontsize": 10},
                wedgeprops={"edgecolor": BG_PANEL, "linewidth": 3, "width": 0.42})
            ax2.text(0, 0, f"{n}\nhogares", ha="center", va="center",
                     fontsize=11, fontweight="bold", color=FG_TEXT)
            ax2.set_title("Segmentación accionable de la población",
                          fontsize=12, fontweight="bold", pad=8)
            ax2.legend(wedges, seg_lbls, loc="center left",
                       bbox_to_anchor=(1.02, 0.5),
                       fontsize=8, frameon=False)

            # ── 3) Camadas potenciales ──
            ax3 = fig.add_subplot(2, 2, 3)
            _card(ax3, color="#f0faf9", border_color=ACCENT, border_width=2.0)
            ax3.set_title("  ⚠  Reproducción potencial sin intervención",
                          fontsize=12, fontweight="bold", color=ACCENT,
                          loc="left", pad=10,
                          bbox=dict(facecolor="#d8f3ee", edgecolor="none",
                                    boxstyle="round,pad=0.3"))
            ax3.text(0.05, 0.61, f"~{camadas_anio:,}".replace(",", "."),
                     fontsize=48, fontweight="bold", color=ACCENT,
                     transform=ax3.transAxes, va="center")
            ax3.text(0.05, 0.43, "nuevos cachorros / gatitos por año",
                     fontsize=10, color=FG_TEXT, transform=ax3.transAxes,
                     fontweight="bold")
            explic2 = (f"Estimado a partir de {int(hembras_riesgo)} hembras sin castrar\n"
                       "× 2 camadas/año × 4 crías promedio.\n\n"
                       "Cada año sin campaña masiva = más animales en\n"
                       "situación de calle, abandono y riesgo sanitario.")
            ax3.text(0.05, 0.33, explic2, fontsize=9, color=FG_TEXT,
                     transform=ax3.transAxes, va="top", linespacing=1.6)

            # ── 4) Top 10 barrios con más hogares críticos ──
            ax4 = fig.add_subplot(2, 2, 4)
            if n_triple > 0:
                top_b = df.loc[triple_riesgo, "Barrio"].value_counts().head(10).sort_values()
                # Degradado de claro a oscuro para jerarquía visual
                n_bars = len(top_b)
                intensities = [0.35 + 0.55 * (i / max(n_bars - 1, 1))
                               for i in range(n_bars)]
                colors4 = plt.get_cmap("Reds")(intensities)
                bars4 = ax4.barh(top_b.index, top_b.values,
                                 color=colors4, edgecolor=BG_PANEL,
                                 linewidth=0.8, height=0.62)
                ax4.set_title("Barrios con más hogares de triple riesgo",
                              fontsize=12, fontweight="bold")
                ax4.set_xlabel("Cantidad de hogares", fontsize=9)
                ax4.tick_params(axis="y", labelsize=9)
                for i, v in enumerate(top_b.values):
                    ax4.text(v + 0.08, i, f"{int(v)}", va="center",
                             fontsize=9, fontweight="bold", color=FG_TEXT)
                if top_b.max() > 0:
                    ax4.set_xlim(0, top_b.max() * 1.22)
            else:
                ax4.axis("off")
                ax4.text(0.5, 0.5, "Sin hogares de triple riesgo\nen el filtro actual",
                         ha="center", va="center", fontsize=12, color=FG_TEXT,
                         transform=ax4.transAxes)

            # Pie de página con dato extra
            fig.text(0.5, 0.01,
                     f"[!] Brecha sanitaria: {pct_no_vac_no_des:.0f}% de los hogares "
                     f"no vacuna NI desparasita a sus mascotas.",
                     ha="center", fontsize=9, color=FG_TEXT, style="italic")
            fig.subplots_adjust(left=0.06, right=0.82, top=0.94,
                                bottom=0.07, hspace=0.44, wspace=0.35)
        self._redraw_fig("Insights", build)

    # ── Salud Pública / Zoonosis ───────────────────────────────────────────
    def _draw_salud(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return
            n = len(df)

            # Layout: arriba matriz 2x2, abajo panel ancho de brecha sanitaria
            gs = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.45)

            # 1) Cruz vacunación × desparasitación (matriz 2×2)
            ax1 = fig.add_subplot(gs[0])
            if "Vacunadas" in df.columns and "Desparasitadas" in df.columns:
                ct = pd.crosstab(df["Vacunadas"], df["Desparasitadas"])
                ct = ct.reindex(index=["Si", "No"], columns=["Si", "No"], fill_value=0)
                from matplotlib.colors import ListedColormap
                cat = np.array([[0, 1],
                                [1, 2]])
                cmap = ListedColormap([GREEN, YELLOW, RED])
                ax1.imshow(cat, cmap=cmap, aspect="auto", vmin=0, vmax=2)
                ax1.set_xticks([0, 1]); ax1.set_xticklabels(["Despar.: Si", "Despar.: No"])
                ax1.set_yticks([0, 1]); ax1.set_yticklabels(["Vacuna: Si", "Vacuna: No"])
                ax1.set_title("Vacunación × Desparasitación\n(hogares en cada cuadrante)",
                              fontsize=11, fontweight="bold")
                for i in range(2):
                    for j in range(2):
                        v = int(ct.values[i, j])
                        pct = v / n * 100 if n else 0
                        ax1.text(j, i, f"{v}\n({pct:.0f}%)", ha="center", va="center",
                                 fontsize=12, fontweight="bold",
                                 color=TEXT_ON_ACCENT)

            # 2) % de hogares con riesgo zoonótico (sin vacuna o sin desparasitar)
            ax3 = fig.add_subplot(gs[1])
            riesgos = {}
            if "Vacunadas" in df.columns:
                riesgos["No vacuna"] = (df["Vacunadas"] == "No").mean() * 100
            if "Desparasitadas" in df.columns:
                riesgos["No desparasita"] = (df["Desparasitadas"] == "No").mean() * 100
            if "Vacunadas" in df.columns and "Desparasitadas" in df.columns:
                riesgos["Ninguna de las dos"] = (
                    (df["Vacunadas"] == "No") & (df["Desparasitadas"] == "No")
                ).mean() * 100
            if riesgos:
                names = list(riesgos.keys()); vals = list(riesgos.values())
                bars = ax3.bar(names, vals, color=[YELLOW, ACCENT, RED][:len(vals)],
                               edgecolor=BG_PANEL)
                ax3.set_title("Brecha sanitaria (% de hogares)",
                              fontsize=11, fontweight="bold")
                ax3.set_ylim(0, max(vals) * 1.20)
                ax3.set_ylabel("%")
                for b, v in zip(bars, vals):
                    ax3.text(b.get_x() + b.get_width() / 2, v + 1.5,
                             f"{v:.0f}%", ha="center", fontsize=10,
                             fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Salud Pública", build)

    # ── Demografía / segmentación de hogares ───────────────────────────────
    def _draw_demografia(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return

            # 1) Castración por tamaño de familia
            ax1 = fig.add_subplot(2, 2, 1)
            if "Integrantes_Familia" in df.columns:
                tmp = df.copy()
                tmp["_int"] = pd.to_numeric(tmp["Integrantes_Familia"], errors="coerce")
                tmp = tmp.dropna(subset=["_int"])
                tmp["bucket"] = pd.cut(tmp["_int"], bins=[0, 1, 2, 4, 6, 99],
                                       labels=["1", "2", "3-4", "5-6", "7+"])
                g = tmp.groupby("bucket", observed=True).apply(
                    lambda s: (s["Mascota_Castrada"] == "Si").mean() * 100)
                bars = ax1.bar([str(x) for x in g.index], g.values,
                               color=ACCENT, edgecolor=BG_PANEL)
                ax1.set_title("% castración según tamaño de familia",
                              fontsize=11, fontweight="bold")
                ax1.set_xlabel("Integrantes por hogar")
                ax1.set_ylabel("% castradas"); ax1.set_ylim(0, 110)
                for b, v in zip(bars, g.values):
                    ax1.text(b.get_x() + b.get_width() / 2, v + 1.5,
                             f"{v:.0f}%", ha="center", fontsize=9,
                             fontweight="bold", color=FG_TEXT)

            # 2) Densidad: mascotas por persona, según tipo de vivienda
            ax2 = fig.add_subplot(2, 2, 2)
            if "Integrantes_Familia" in df.columns and "Total_Mascotas" in df.columns:
                tmp = df.copy()
                tmp["_int"] = pd.to_numeric(tmp["Integrantes_Familia"], errors="coerce")
                tmp["_tot"] = pd.to_numeric(tmp["Total_Mascotas"], errors="coerce")
                tmp = tmp.dropna(subset=["_int", "_tot"])
                tmp = tmp[tmp["_int"] > 0]
                tmp["dens"] = tmp["_tot"] / tmp["_int"]
                g = tmp.groupby("Tipo_Vivienda")["dens"].mean().sort_values()
                bars = ax2.barh(g.index, g.values, color=PURPLE, edgecolor=BG_PANEL)
                ax2.set_title("Mascotas por persona, según vivienda",
                              fontsize=11, fontweight="bold")
                ax2.set_xlabel("Mascotas / integrante")
                for i, v in enumerate(g.values):
                    ax2.text(v + 0.02, i, f"{v:.2f}", va="center",
                             fontsize=9, fontweight="bold", color=FG_TEXT)

            # 3) Hogares con MUCHAS mascotas (≥4) por barrio
            ax3 = fig.add_subplot(2, 2, 3)
            if "Total_Mascotas" in df.columns:
                tmp = df.copy()
                tmp["_tot"] = pd.to_numeric(tmp["Total_Mascotas"], errors="coerce").fillna(0)
                muchos = tmp[tmp["_tot"] >= 4]
                if len(muchos) > 0:
                    top = muchos["Barrio"].value_counts().head(10).sort_values()
                    ax3.barh(top.index, top.values, color=YELLOW, edgecolor=BG_PANEL)
                    ax3.set_title("Hogares con ≥4 mascotas\n(posible acumulación)",
                                  fontsize=11, fontweight="bold")
                    ax3.set_xlabel("Cantidad de hogares")
                    for i, v in enumerate(top.values):
                        ax3.text(v + 0.1, i, f"{int(v)}", va="center",
                                 fontsize=9, fontweight="bold", color=FG_TEXT)
                else:
                    ax3.axis("off")
                    ax3.text(0.5, 0.5, "Sin hogares con ≥4 mascotas\nen el filtro actual",
                             ha="center", va="center", color=FG_TEXT, fontsize=11,
                             transform=ax3.transAxes)

            # 4) Hembras vs machos sin castrar (potencial reproductivo)
            ax4 = fig.add_subplot(2, 2, 4)
            no_cast = df[df["Mascota_Castrada"] == "No"]
            def _s(c): return float(pd.to_numeric(no_cast[c], errors="coerce").fillna(0).sum()) if c in no_cast.columns else 0.0
            ph, pm = _s("Perros_Hembra"), _s("Perros_Macho")
            gh, gm = _s("Gatos_Hembra"),  _s("Gatos_Macho")
            cats = ["Perros\n♀", "Perros\n♂", "Gatos\n♀", "Gatos\n♂"]
            vals = [ph, pm, gh, gm]
            cols_b = [RED, ACCENT, RED, ACCENT]
            bars = ax4.bar(cats, vals, color=cols_b, edgecolor=BG_PANEL)
            ax4.set_title("Animales SIN castrar por sexo\n(las ♀ generan camadas)",
                          fontsize=11, fontweight="bold")
            ax4.set_ylabel("Cantidad")
            for b, v in zip(bars, vals):
                ax4.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.01 + 0.5,
                         f"{int(v)}", ha="center", fontsize=10,
                         fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Demografía", build)

    # ── Acción Municipal: efectividad y demanda ────────────────────────────
    def _draw_accion_mun(self):
        df = self.df
        def build(fig):
            if len(df) == 0:
                fig.text(0.5, 0.5, "Sin datos con los filtros aplicados",
                         ha="center", va="center", color=FG_TEXT, fontsize=14)
                return

            # Layout: arriba 2 paneles + abajo 1 panel ancho
            # (eliminado el duplicado de "Demanda ciudadana al municipio"
            #  — ya está en la pestaña Municipio)
            gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.45, wspace=0.35)

            # 1) ¿La gente que castró por el municipio sabe que es gratis?
            ax1 = fig.add_subplot(gs[0, 0])
            if "CastEn_Municipio" in df.columns and "Sabe_Castracion_Gratuita" in df.columns:
                tmp = df.copy()
                tmp["_cm"] = pd.to_numeric(tmp["CastEn_Municipio"], errors="coerce").fillna(0)
                tmp["_cm_lbl"] = tmp["_cm"].map({1: "Castró por\nel municipio",
                                                  0: "Otros / no\ncastró"})
                g = tmp.groupby("_cm_lbl").apply(
                    lambda s: (s["Sabe_Castracion_Gratuita"] == "Si").mean() * 100)
                bars = ax1.bar(g.index, g.values, color=[GREEN, YELLOW][:len(g)],
                               edgecolor=BG_PANEL)
                ax1.set_title("% que sabe sobre castración gratuita",
                              fontsize=11, fontweight="bold")
                ax1.set_ylabel("% sabe que es gratis"); ax1.set_ylim(0, 110)
                for b, v in zip(bars, g.values):
                    ax1.text(b.get_x() + b.get_width() / 2, v + 1.5,
                             f"{v:.0f}%", ha="center", fontsize=10,
                             fontweight="bold", color=FG_TEXT)

            # 2) ¿Pedir castr. masivas se asocia a NO haber castrado?
            ax3 = fig.add_subplot(gs[0, 1])
            if "Mun_Castraciones_Masivas" in df.columns:
                tmp = df.copy()
                tmp["_pide"] = pd.to_numeric(tmp["Mun_Castraciones_Masivas"], errors="coerce").fillna(0)
                tmp["_pide_lbl"] = tmp["_pide"].map({1: "Pide castr.\nmasivas",
                                                      0: "No las pide"})
                g = tmp.groupby("_pide_lbl").apply(
                    lambda s: (s["Mascota_Castrada"] == "No").mean() * 100)
                bars = ax3.bar(g.index, g.values, color=[RED, ACCENT][:len(g)],
                               edgecolor=BG_PANEL)
                ax3.set_title("% SIN castrar, según si pide castr. masivas",
                              fontsize=11, fontweight="bold")
                ax3.set_ylabel("% sin castrar"); ax3.set_ylim(0, 110)
                for b, v in zip(bars, g.values):
                    ax3.text(b.get_x() + b.get_width() / 2, v + 1.5,
                             f"{v:.0f}%", ha="center", fontsize=10,
                             fontweight="bold", color=FG_TEXT)

            # 3) Barrios con mayor "abandono institucional" (panel ancho)
            ax2 = fig.add_subplot(gs[1, :])
            if "Municipio_Presente" in df.columns:
                tmp = df.copy()
                tmp["_no_mun"] = (~tmp["Municipio_Presente"].astype(str)
                                  .str.contains("Si", case=False, na=False)).astype(int)
                g = tmp.groupby("Barrio")["_no_mun"].agg(["mean", "size"])
                g = g[g["size"] >= 3].sort_values("mean", ascending=True).tail(10)
                if len(g) > 0:
                    pcts = np.asarray(g["mean"].values, dtype=float) * 100
                    ax2.barh(g.index, pcts,
                             color=RED, edgecolor=BG_PANEL)
                    ax2.set_title("Barrios donde MENOS se percibe la presencia del municipio",
                                  fontsize=11, fontweight="bold")
                    ax2.set_xlabel("% que dice 'No está presente'")
                    ax2.set_xlim(0, 110)
                    ax2.tick_params(axis="y", labelsize=9)
                    for i, v in enumerate(pcts):
                        ax2.text(v + 1.5, i, f"{v:.0f}%", va="center",
                                 fontsize=9, fontweight="bold", color=FG_TEXT)
        self._redraw_fig("Acción Municipal", build)

    # ── Tabla ─────────────────────────────────────────────────────────────
    def _draw_tabla(self):
        self._clear(self.tabs["Tabla"])
        df = self.df

        # Toolbar superior
        bar = ttk.Frame(self.tabs["Tabla"], style="Panel.TFrame", padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text=f"Mostrando {min(len(df), 1000)} de {len(df)} filas filtradas",
                  style="FilterLabel.TLabel").pack(side="left", padx=8)
        ttk.Button(bar, text="📥 Exportar a CSV (todas)", style="Accent.TButton",
                   command=self._exportar_csv).pack(side="right", padx=8)

        # TODAS las columnas del dataframe
        cols_show = list(df.columns)

        cont = ttk.Frame(self.tabs["Tabla"], style="Panel.TFrame")
        cont.pack(fill="both", expand=True)

        tree = ttk.Treeview(cont, columns=cols_show, show="headings",
                            style="Treeview")
        # Filas alternadas para mejor lectura
        tree.tag_configure("odd", background=BG_PANEL, foreground=FG_TEXT)
        tree.tag_configure("even", background=BG_CARD, foreground=FG_TEXT)

        for c in cols_show:
            tree.heading(c, text=friendly(c))
            # Anchos según tipo de columna
            if c.startswith(("Mascota_", "Vive_", "CastEn_", "Mun_")):
                w = 70
            elif c in ("Marca_Temporal", "Donde_Castracion", "Como_Viven_Mascotas",
                       "Municipio_Presente"):
                w = 180
            else:
                w = 110
            tree.column(c, width=w, anchor="w", stretch=False)

        vsb = ttk.Scrollbar(cont, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(cont, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        cont.rowconfigure(0, weight=1)
        cont.columnconfigure(0, weight=1)

        for i, (_, row) in enumerate(df[cols_show].head(1000).iterrows()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end",
                        values=["" if pd.isna(v) else v for v in row.tolist()],
                        tags=(tag,))

    def _exportar_csv(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="mascotas_filtrado.csv")
        if path:
            self.df.to_csv(path, index=False, encoding="utf-8")
            messagebox.showinfo("Exportar", f"Se guardaron {len(self.df)} filas en:\n{path}")


def main():
    if not os.path.exists(CSV_LIMPIO):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error",
            f"No se encontró:\n{CSV_LIMPIO}\n\n"
            "Ejecutá primero la limpieza (PipelineMascotas → paso 1).")
        return
    df = pd.read_csv(CSV_LIMPIO, encoding="utf-8")
    # Asegura columnas derivadas (por si el CSV viene de una limpieza vieja)
    for c in ("Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"):
        if c not in df.columns:
            df[c] = 0
    if "Total_Perros" not in df.columns:
        df["Total_Perros"] = (pd.to_numeric(df["Perros_Macho"], errors="coerce").fillna(0)
                              + pd.to_numeric(df["Perros_Hembra"], errors="coerce").fillna(0))
    if "Total_Gatos" not in df.columns:
        df["Total_Gatos"] = (pd.to_numeric(df["Gatos_Macho"], errors="coerce").fillna(0)
                             + pd.to_numeric(df["Gatos_Hembra"], errors="coerce").fillna(0))
    if "Total_Mascotas" not in df.columns:
        df["Total_Mascotas"] = df["Total_Perros"] + df["Total_Gatos"]
    app = Dashboard(df)
    app.mainloop()


if __name__ == "__main__":
    main()
