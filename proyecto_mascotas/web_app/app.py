"""
Dashboard Web — Cuidado de Mascotas
====================================
Versión Streamlit completa con todas las pestañas del dashboard de escritorio.
Pensada para deploy en Streamlit Community Cloud.

Ejecutar localmente:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
import textwrap
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # backend no-GUI: indispensable en servidor
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages

# ── Configuración base ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DEFAULT = os.path.join(BASE_DIR, "mascotas_limpio.csv")

# Paleta clínica/teal
ACCENT = "#2a9d8f"
GREEN = "#52b788"
RED = "#e63946"
YELLOW = "#f4a261"
BLUE = "#4895ef"
PURPLE = "#9d4edd"
NAVY = "#1f3a5f"
BG_PANEL = "#ffffff"
BG_CARD = "#f4faf9"
PALETTE = [ACCENT, BLUE, YELLOW, GREEN, RED, PURPLE, "#ff8fab"]

st.set_page_config(
    page_title="Dashboard — Cuidado de Mascotas",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

plt.rcParams.update({
    "axes.facecolor": BG_PANEL,
    "figure.facecolor": BG_PANEL,
    "axes.edgecolor": "#cfd8dc",
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.titlecolor": NAVY,
    "axes.titleweight": "bold",
    "axes.titlesize": 11,
    "font.size": 9,
    "axes.grid": True,
    "grid.color": "#dde6ea",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.constrained_layout.use": True,
})

# ── CSS para mejorar el look general ────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Layout */
        .block-container {
            padding-top: 1.5rem; padding-bottom: 2rem;
            max-width: 1400px;
        }
        /* Tipografía general (NO toca al banner, que usa .hero-*) */
        .main h1:not(.hero-title),
        .main h2, .main h3 { color: #1f3a5f; }

        /* Banner principal */
        .hero {
            background: linear-gradient(135deg, #2a9d8f 0%, #4895ef 100%);
            padding: 26px 32px;
            border-radius: 14px;
            margin: 4px 0 22px 0;
            box-shadow: 0 6px 20px rgba(42,157,143,0.25);
            color: #ffffff !important;
        }
        .hero-title {
            color: #ffffff !important;
            margin: 0 !important;
            font-size: 30px !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
            letter-spacing: -0.5px;
        }
        .hero-sub {
            color: #eaf6f4 !important;
            margin: 8px 0 0 0 !important;
            font-size: 14px !important;
            font-weight: 400 !important;
        }
        .hero-sub b { color: #ffffff !important; font-weight: 700 !important; }

        /* Métricas tipo card */
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #f4faf9 100%);
            padding: 14px 16px;
            border-radius: 12px;
            border-left: 4px solid #2a9d8f;
            box-shadow: 0 2px 6px rgba(31,58,95,0.06);
        }
        [data-testid="stMetricValue"] {
            color: #2a9d8f !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: #1f3a5f !important;
            font-weight: 600 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eaf2f5 0%, #ffffff 100%);
            border-right: 1px solid #d8e3e8;
        }
        section[data-testid="stSidebar"] .stMultiSelect label,
        section[data-testid="stSidebar"] .stFileUploader label {
            font-weight: 600; color: #1f3a5f;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            flex-wrap: wrap;
            border-bottom: 2px solid #e0e8ec;
        }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border-radius: 10px 10px 0 0;
            padding: 10px 16px;
            font-weight: 600;
            color: #1f3a5f;
            border: 1px solid transparent;
            transition: all 0.15s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: #f0f7f6;
            color: #2a9d8f;
        }
        .stTabs [aria-selected="true"] {
            background: #2a9d8f !important;
            color: white !important;
            box-shadow: 0 -2px 8px rgba(42,157,143,0.25);
        }
        .stTabs [aria-selected="true"] p { color: white !important; }

        /* Botones */
        .stDownloadButton button, .stButton button {
            background: #2a9d8f; color: white !important;
            border: none; border-radius: 8px;
            font-weight: 600; padding: 8px 18px;
            transition: all 0.15s ease;
        }
        .stDownloadButton button:hover, .stButton button:hover {
            background: #21867a; color: white !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(42,157,143,0.3);
        }

        /* Otros */
        hr { border-color: #d8e3e8; }
        .stDataFrame { border-radius: 10px; overflow: hidden; }
        .stAlert { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_csv(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    if "Marca_Temporal" in df.columns:
        df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"], errors="coerce")
    for c in ("Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra",
              "Integrantes_Familia"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["Total_Perros"] = df.get("Perros_Macho", 0) + df.get("Perros_Hembra", 0)
    df["Total_Gatos"] = df.get("Gatos_Macho", 0) + df.get("Gatos_Hembra", 0)
    df["Total_Mascotas"] = df["Total_Perros"] + df["Total_Gatos"]
    return df


def _pct_si(serie: pd.Series) -> float:
    if serie.empty:
        return 0.0
    return (serie.astype(str).str.lower().eq("si")).mean() * 100


def _empty_msg(fig, msg="Sin datos con los filtros aplicados"):
    fig.text(0.5, 0.5, msg, ha="center", va="center", color=NAVY, fontsize=13)


def _wrap(s, width=22):
    return "\n".join(textwrap.wrap(str(s), width=width)) or str(s)


def _safe_max(values, default: float = 1.0) -> float:
    """Devuelve el máximo de una secuencia ignorando NaN/Inf.

    Si está vacía o el máximo no es finito, devuelve `default`.
    """
    try:
        arr = np.asarray(list(values), dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return float(default)
        m = float(arr.max())
        return m if m > 0 else float(default)
    except Exception:
        return float(default)


def _donut(ax, values, labels, colors, title, min_pct_inside=4.0):
    """Pie/donut con % dentro (solo si la porción es grande) y leyenda abajo.

    Evita el solapamiento de etiquetas externas en porciones chicas y el
    recorte de leyendas laterales cuando hay varios subplots juntos.
    """
    values = list(values)
    labels = [str(l) for l in labels]
    total = sum(values) or 1
    pcts = [v / total * 100 for v in values]

    def _autopct(p):
        return f"{p:.0f}%" if p >= min_pct_inside else ""

    wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=_autopct,
        colors=colors,
        startangle=90,
        pctdistance=0.78,
        wedgeprops={"edgecolor": "white", "linewidth": 2, "width": 0.45},
        textprops={"fontsize": 11, "fontweight": "bold"},
    )
    for at in autotexts:
        at.set_color("white")

    # Leyenda DEBAJO del donut (evita clipping con subplots vecinos)
    legend_labels = [f"{lab} · {p:.0f}%" for lab, p in zip(labels, pcts)]
    ax.legend(
        wedges, legend_labels,
        loc="upper center", bbox_to_anchor=(0.5, -0.02),
        frameon=False, fontsize=9,
        ncol=min(len(labels), 2),
    )
    ax.set_title(title, pad=10)
    ax.axis("equal")
    ax.grid(False)


def _empty_panel(ax, msg="Sin datos suficientes"):
    """Limpia un eje y escribe un mensaje centrado de empty-state."""
    ax.clear()
    ax.axis("off")
    ax.text(0.5, 0.5, msg, ha="center", va="center",
            color="#7a8b99", fontsize=11, style="italic",
            transform=ax.transAxes)


def _section_header(title: str, subtitle: str = ""):
    """Encabezado consistente arriba de cada tab."""
    sub_html = (
        f"<div style='color:#7a8b99; font-size:13px; margin-top:-4px;'>{subtitle}</div>"
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div style='margin: 2px 0 14px 0;'>
            <div style='color:#1f3a5f; font-size:18px; font-weight:700;'>{title}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_fig(fig, key: str):
    """Muestra una figura matplotlib con botón de descarga PNG."""
    st.pyplot(fig, clear_figure=False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    st.download_button(
        "⬇️ Descargar como PNG",
        data=buf.getvalue(),
        file_name=f"{key}.png",
        mime="image/png",
        key=f"dl_{key}",
        use_container_width=False,
    )
    plt.close(fig)


def _generar_insights(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Devuelve lista de (icono, titulo, valor/comentario) auto-generados."""
    out: list[tuple[str, str, str]] = []
    if "Mascota_Castrada" in df.columns:
        cast = _pct_si(df["Mascota_Castrada"])
        if cast >= 70:
            out.append(("✅", "Castración alta",
                        f"{cast:.0f}% de los hogares castra. Buen indicador."))
        elif cast >= 40:
            out.append(("⚠️", "Castración intermedia",
                        f"Solo {cast:.0f}% castra: queda margen de mejora."))
        else:
            out.append(("🚨", "Castración baja",
                        f"Apenas {cast:.0f}% castra. Brecha sanitaria importante."))

    if "Vacunadas" in df.columns and "Desparasitadas" in df.columns:
        ambas = (
            (df["Vacunadas"].astype(str).str.lower() == "no") &
            (df["Desparasitadas"].astype(str).str.lower() == "no")
        ).mean() * 100
        if ambas > 0:
            out.append(("🩺", "Riesgo sanitario",
                        f"{ambas:.0f}% de hogares no vacuna NI desparasita."))

    if {"Sabe_Castracion_Gratuita", "Mascota_Castrada"} <= set(df.columns):
        sabe_si = df[df["Sabe_Castracion_Gratuita"].astype(str).str.lower() == "si"]
        sabe_no = df[df["Sabe_Castracion_Gratuita"].astype(str).str.lower() == "no"]
        if len(sabe_si) > 5 and len(sabe_no) > 5:
            p_si = _pct_si(sabe_si.get("Mascota_Castrada", pd.Series(dtype=str)))
            p_no = _pct_si(sabe_no.get("Mascota_Castrada", pd.Series(dtype=str)))
            delta = p_si - p_no
            if abs(delta) >= 10:
                out.append(("📚", "Información influye",
                            f"Quien sabe que la castración es gratuita la realiza "
                            f"{delta:+.0f} pp más."))

    if "Barrio" in df.columns and "Mascota_Castrada" in df.columns and len(df) >= 30:
        g = (df.assign(_si=df["Mascota_Castrada"].astype(str).str.lower().eq("si"))
               .groupby("Barrio")["_si"].agg(["mean", "size"])
               .query("size >= 5")
               .sort_values("mean"))
        if not g.empty:
            peor = g.index[0]
            out.append(("📍", "Barrio prioritario",
                        f"«{peor}»: solo {g.iloc[0]['mean']*100:.0f}% castra "
                        f"(n={int(g.iloc[0]['size'])})."))

    if "Mun_Castraciones_Masivas" in df.columns:
        pide = pd.to_numeric(df["Mun_Castraciones_Masivas"], errors="coerce").fillna(0).mean() * 100
        if pide >= 30:
            out.append(("🏛️", "Demanda al municipio",
                        f"{pide:.0f}% de hogares pide castraciones masivas."))

    return out[:4]


# ── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f"<h2 style='color:{ACCENT}; margin:0;'>🐾 Dashboard Mascotas</h2>"
    f"<p style='color:{NAVY}; font-size:12px; margin-top:2px;'>"
    "Relevamiento de cuidado responsable</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

uploaded = st.sidebar.file_uploader(
    "📂 Subí tu CSV limpio (opcional)", type=["csv"],
    help="Si no subís nada, se usa el dataset incluido."
)

try:
    df_full = cargar_csv(uploaded if uploaded is not None else CSV_DEFAULT)
except FileNotFoundError:
    st.error("No se encontró `mascotas_limpio.csv`. Subí un CSV desde el panel lateral.")
    st.stop()

st.sidebar.markdown("### 🔍 Filtros")

if st.sidebar.button("🔄 Limpiar filtros", use_container_width=True):
    for k in ("flt_ciudades", "flt_barrios", "flt_viviendas", "flt_tipos"):
        st.session_state.pop(k, None)
    st.rerun()


def _opciones(col: str) -> list[str]:
    if col not in df_full.columns:
        return []
    return sorted(df_full[col].dropna().astype(str).unique().tolist())


ciudades = st.sidebar.multiselect(
    "Ciudad", _opciones("Ciudad"),
    placeholder="Todas las ciudades",
    key="flt_ciudades",
)
barrios = st.sidebar.multiselect(
    "Barrio", _opciones("Barrio"),
    placeholder="Todos los barrios",
    key="flt_barrios",
)
viviendas = st.sidebar.multiselect(
    "Tipo de vivienda", _opciones("Tipo_Vivienda"),
    placeholder="Todas las viviendas",
    key="flt_viviendas",
)
tipos_mascota = st.sidebar.multiselect(
    "Tipo de mascotas", _opciones("Tipo_Mascotas"),
    placeholder="Todos los tipos",
    key="flt_tipos",
)

df = df_full.copy()
if ciudades:
    df = df[df["Ciudad"].astype(str).isin(ciudades)]
if barrios:
    df = df[df["Barrio"].astype(str).isin(barrios)]
if viviendas:
    df = df[df["Tipo_Vivienda"].astype(str).isin(viviendas)]
if tipos_mascota:
    df = df[df["Tipo_Mascotas"].astype(str).isin(tipos_mascota)]

st.sidebar.markdown(
    f"<div style='background:#ffffff; padding:10px 12px; border-radius:8px; "
    f"margin-top:10px; border-left:3px solid {ACCENT};'>"
    f"<div style='font-size:11px; color:#7a8b99;'>Registros</div>"
    f"<div style='font-size:22px; font-weight:800; color:{ACCENT};'>"
    f"{len(df):,}</div>".replace(",", ".")
    + f"<div style='font-size:11px; color:#7a8b99;'>de {len(df_full):,} totales</div></div>".replace(",", "."),
    unsafe_allow_html=True,
)

# Chips con filtros activos
filtros_activos: list[str] = []
if ciudades:
    filtros_activos.append(f"🏙️ {len(ciudades)} ciudad(es)")
if barrios:
    filtros_activos.append(f"🏘️ {len(barrios)} barrio(s)")
if viviendas:
    filtros_activos.append(f"🏠 {len(viviendas)} vivienda(s)")
if tipos_mascota:
    filtros_activos.append(f"🐾 {len(tipos_mascota)} tipo(s)")

if filtros_activos:
    chips_html = "".join(
        f"<span style='display:inline-block; background:{ACCENT}; color:white; "
        f"padding:3px 9px; border-radius:12px; font-size:11px; "
        f"margin:2px 3px 2px 0; font-weight:600;'>{c}</span>"
        for c in filtros_activos
    )
    st.sidebar.markdown(
        f"<div style='margin-top:10px;'>"
        f"<div style='font-size:11px; color:{NAVY}; font-weight:600; margin-bottom:4px;'>"
        f"Filtros activos:</div>{chips_html}</div>",
        unsafe_allow_html=True,
    )

# ── Cabecera ────────────────────────────────────────────────────────────────
n_filtrados = len(df)
n_total = len(df_full)
pct_filtro = (n_filtrados / n_total * 100) if n_total else 100
n_barrios = df["Barrio"].nunique() if "Barrio" in df.columns else 0
n_ciudades = df["Ciudad"].nunique() if "Ciudad" in df.columns else 0

chips = (
    f"<span style='background:rgba(255,255,255,0.18); padding:4px 12px; "
    f"border-radius:20px; font-size:12px; font-weight:600; margin-right:8px;'>"
    f"📋 {n_filtrados:,} / {n_total:,} encuestas ({pct_filtro:.0f}%)</span>"
    f"<span style='background:rgba(255,255,255,0.18); padding:4px 12px; "
    f"border-radius:20px; font-size:12px; font-weight:600; margin-right:8px;'>"
    f"🏘️ {n_barrios} barrios</span>"
    f"<span style='background:rgba(255,255,255,0.18); padding:4px 12px; "
    f"border-radius:20px; font-size:12px; font-weight:600;'>"
    f"🏙️ {n_ciudades} ciudades</span>"
).replace(",", ".")

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">🏥 Clínica Veterinaria — Cuidado de Mascotas</div>
        <div class="hero-sub">
            Dashboard interactivo del relevamiento de cuidado responsable
        </div>
        <div style="margin-top:14px;">{chips}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No hay registros con los filtros actuales. Probá ajustar el panel lateral.")
    st.stop()

if len(df) < 10:
    st.info(
        f"⚠️ Solo hay **{len(df)} encuestas** con los filtros actuales. "
        "Algunos gráficos pueden quedar vacíos o poco representativos. "
        "Probá ampliar los filtros para obtener una muestra más significativa."
    )

# ── KPIs ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📋 Encuestas", f"{len(df):,}".replace(",", "."))
k2.metric("🐾 Mascotas", f"{int(df['Total_Mascotas'].sum()):,}".replace(",", "."))
k3.metric("✂️ Castradas", f"{_pct_si(df.get('Mascota_Castrada', pd.Series(dtype=str))):.1f}%")
k4.metric("💉 Vacunadas", f"{_pct_si(df.get('Vacunadas', pd.Series(dtype=str))):.1f}%")
k5.metric("🪱 Desparasitadas", f"{_pct_si(df.get('Desparasitadas', pd.Series(dtype=str))):.1f}%")
k6.metric("🏘️ Barrios", f"{df['Barrio'].nunique() if 'Barrio' in df.columns else 0}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_names = [
    "📊 Resumen", "✂️ Castración", "🗺️ Geografía", "⚠️ Barrios prioritarios",
    "🏛️ Municipio", "💊 Cuidado", "🐕 Callejeros", "📚 Brecha informativa",
    "🩺 Salud pública", "👨‍👩‍👧 Demografía", "🎯 Acción municipal", "📋 Tabla",
]
tabs = st.tabs(tab_names)


def _label_bars_v(ax, vals, fmt="{:.0f}%", offset_pct=0.02):
    """Etiqueta barras verticales."""
    ymax = ax.get_ylim()[1]
    off = ymax * offset_pct
    for i, v in enumerate(vals):
        if v == 0 or pd.isna(v):
            continue
        ax.text(i, v + off, fmt.format(v), ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=NAVY)


def _label_bars_h(ax, vals, fmt="{:.0f}", offset_pct=0.015):
    """Etiqueta barras horizontales."""
    xmax = ax.get_xlim()[1]
    off = max(xmax * offset_pct, 0.2)
    for i, v in enumerate(vals):
        if v == 0 or pd.isna(v):
            continue
        ax.text(v + off, i, fmt.format(v), va="center", ha="left",
                fontsize=8, fontweight="bold", color=NAVY)


# ── 1. Resumen ──────────────────────────────────────────────────────────────
with tabs[0]:
    _section_header(
        "Vista general",
        "Composición del relevamiento: tipo de mascotas, viviendas y autopercepción.",
    )

    insights = _generar_insights(df)
    if insights:
        cards = "".join(
            f"<div style='flex:1; min-width:220px; background:#ffffff; "
            f"border-left:4px solid {ACCENT}; border-radius:10px; padding:12px 14px; "
            f"box-shadow:0 2px 6px rgba(31,58,95,0.06);'>"
            f"<div style='font-size:14px; margin-bottom:4px;'>"
            f"<span style='font-size:18px;'>{ic}</span> "
            f"<b style='color:{NAVY};'>{tt}</b></div>"
            f"<div style='font-size:13px; color:#3a4d5e; line-height:1.4;'>{vv}</div></div>"
            for ic, tt, vv in insights
        )
        st.markdown(
            f"<div style='display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px;'>"
            f"{cards}</div>",
            unsafe_allow_html=True,
        )

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax1, ax2, ax3, ax4 = axes.flat

    if "Tipo_Mascotas" in df.columns and not df["Tipo_Mascotas"].dropna().empty:
        c = df["Tipo_Mascotas"].value_counts().sort_values()
        ax1.barh(c.index.astype(str), c.values, color=ACCENT, edgecolor="white")
        ax1.set_title("Tipo de mascotas en el hogar")
        ax1.set_xlim(0, _safe_max(c.values) * 1.2)
        _label_bars_h(ax1, c.values)
    else:
        _empty_panel(ax1, "Sin datos de tipo de mascotas")

    if "Tipo_Vivienda" in df.columns and not df["Tipo_Vivienda"].dropna().empty:
        c = df["Tipo_Vivienda"].value_counts()
        ax2.bar(range(len(c)), c.values, color=BLUE, edgecolor="white")
        ax2.set_xticks(range(len(c)))
        ax2.set_xticklabels([_wrap(x, 12) for x in c.index], fontsize=8)
        ax2.set_title("Tipo de vivienda")
        ax2.set_ylim(0, _safe_max(c.values) * 1.2)
        _label_bars_v(ax2, c.values, fmt="{:.0f}")
    else:
        _empty_panel(ax2, "Sin datos de vivienda")

    if "Frecuencia_Callejeros" in df.columns and not df["Frecuencia_Callejeros"].dropna().empty:
        c = df["Frecuencia_Callejeros"].value_counts()
        ax3.bar(range(len(c)), c.values, color=YELLOW, edgecolor="white")
        ax3.set_xticks(range(len(c)))
        ax3.set_xticklabels([_wrap(x, 12) for x in c.index], fontsize=8)
        ax3.set_title("Frecuencia de callejeros observados")
        ax3.set_ylim(0, _safe_max(c.values) * 1.2)
        _label_bars_v(ax3, c.values, fmt="{:.0f}")
    else:
        _empty_panel(ax3, "Sin datos de callejeros")

    if "Humano_Responsable" in df.columns and not df["Humano_Responsable"].dropna().empty:
        hr = df["Humano_Responsable"].value_counts()
        colors = []
        for x in hr.index:
            xl = str(x).lower()
            if xl == "si":
                colors.append(GREEN)
            elif xl == "no":
                colors.append(RED)
            else:
                colors.append(YELLOW)
        _donut(ax4, hr.values, hr.index.astype(str), colors,
               "¿Te considerás humano responsable?")
    else:
        _empty_panel(ax4, "Sin respuestas de autopercepción")
    _render_fig(fig, "resumen")


# ── 2. Castración ───────────────────────────────────────────────────────────
with tabs[1]:
    _section_header(
        "Castración",
        "Dónde castran y cómo influye conocer que es gratuita.",
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    ax1, ax2, ax3 = axes

    if "Mascota_Castrada" in df.columns:
        mc = df["Mascota_Castrada"].value_counts()
        colors = [GREEN if str(x).lower() == "si" else RED for x in mc.index]
        _donut(ax1, mc.values, mc.index.astype(str), colors,
               "¿Mascotas castradas?")

    cast_en = [c for c in df.columns if c.startswith("CastEn_")]
    if cast_en:
        sums = df[cast_en].sum().sort_values(ascending=True)
        labels = [_wrap(c.replace("CastEn_", "").replace("_", " "), 22) for c in sums.index]
        ax2.barh(labels, sums.values, color=ACCENT, edgecolor="white")
        ax2.set_title("¿Dónde castraron?")
        if _safe_max(sums.values, 0) > 0:
            ax2.set_xlim(0, _safe_max(sums.values, 1.0) * 1.2)
            _label_bars_h(ax2, sums.values)

    if {"Sabe_Castracion_Gratuita", "Mascota_Castrada"} <= set(df.columns):
        sabe = df.groupby("Sabe_Castracion_Gratuita")["Mascota_Castrada"].apply(
            lambda s: (s.astype(str).str.lower() == "si").mean() * 100)
        colors_b = [YELLOW if str(x).lower() == "no" else GREEN for x in sabe.index]
        ax3.bar(sabe.index.astype(str), sabe.values, color=colors_b, edgecolor="white")
        ax3.set_title("% castradas según si\nsabe que es gratuita")
        ax3.set_ylim(0, 110)
        ax3.set_ylabel("% castradas")
        _label_bars_v(ax3, sabe.values, fmt="{:.1f}%")
    _render_fig(fig, "castracion")


# ── 3. Geografía ────────────────────────────────────────────────────────────
with tabs[2]:
    _section_header(
        "Geografía",
        "Cobertura por barrio y nivel de castración donde hay datos suficientes.",
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax1, ax2 = axes

    if "Barrio" in df.columns:
        top = df["Barrio"].value_counts().head(15).iloc[::-1]
        ax1.barh(top.index.astype(str), top.values, color=ACCENT, edgecolor="white")
        ax1.set_title("Top 15 barrios por encuestas")
        if len(top):
            ax1.set_xlim(0, _safe_max(top.values, 1.0) * 1.18)
            _label_bars_h(ax1, top.values)

    if {"Barrio", "Mascota_Castrada"} <= set(df.columns):
        g = (df.assign(_si=df["Mascota_Castrada"].astype(str).str.lower().eq("si"))
               .groupby("Barrio")["_si"].agg(["mean", "size"])
               .query("size >= 3")
               .sort_values("mean", ascending=True)
               .tail(15))
        if not g.empty:
            mean_arr = g["mean"].to_numpy(dtype=float)
            size_arr = g["size"].to_numpy(dtype=float)
            ax2.barh(g.index.astype(str), mean_arr * 100,
                     color=GREEN, edgecolor="white")
            ax2.set_title("% castradas por barrio (≥3 encuestas)")
            ax2.set_xlabel("%")
            ax2.set_xlim(0, 115)
            for i, (m, n) in enumerate(zip(mean_arr, size_arr)):
                ax2.text(m * 100 + 1.5, i, f"{m*100:.0f}% (n={int(n)})",
                         va="center", fontsize=8, color=NAVY, fontweight="bold")
    _render_fig(fig, "geografia")


# ── 4. Barrios prioritarios ─────────────────────────────────────────────────
with tabs[3]:
    _section_header(
        "Barrios prioritarios",
        "Zonas donde concentrar campañas de castración.",
    )
    no_cast = df[df.get("Mascota_Castrada", pd.Series(dtype=str))
                 .astype(str).str.lower() == "no"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax1, ax2 = axes
    if no_cast.empty:
        _empty_msg(fig, "No hay hogares sin castrar en el filtro actual")
        for a in axes:
            a.axis("off")
    else:
        no_cast["_anim"] = pd.to_numeric(no_cast["Total_Mascotas"], errors="coerce").fillna(1)
        g = no_cast.groupby("Barrio").agg(hogares=("_anim", "size"),
                                          animales=("_anim", "sum")).reset_index()
        tot_hog = df.groupby("Barrio").size().rename("total_hog")
        g = g.merge(tot_hog, on="Barrio", how="left")
        g["pct_sin"] = g["hogares"] / g["total_hog"] * 100
        g = g[g["total_hog"] >= 3].sort_values("animales", ascending=True).tail(15)

        if g.empty:
            _empty_msg(fig, "Sin barrios con ≥3 encuestas")
            for a in axes:
                a.axis("off")
        else:
            cmap = plt.get_cmap("Reds")
            max_a = max(g["animales"].max(), 1)
            colors = cmap([0.4 + 0.5 * (v / max_a) for v in g["animales"]])
            ax1.barh(g["Barrio"], g["animales"], color=colors, edgecolor="white")
            ax1.set_title("Top barrios: animales sin castrar (abs.)")
            ax1.set_xlabel("Cantidad estimada de animales sin castrar")
            ax1.set_xlim(0, _safe_max(g["animales"].values, 1.0) * 1.18)
            _label_bars_h(ax1, g["animales"].values)

            g2 = g.sort_values("pct_sin", ascending=True)
            ax2.barh(g2["Barrio"], g2["pct_sin"], color=YELLOW, edgecolor="white")
            ax2.set_title("% hogares sin mascotas castradas\n(mismos barrios)")
            ax2.set_xlabel("% hogares sin castrar")
            ax2.set_xlim(0, 110)
            for i, v in enumerate(g2["pct_sin"]):
                ax2.text(v + 1.5, i, f"{v:.0f}%", va="center",
                         fontsize=8, fontweight="bold", color=NAVY)
    _render_fig(fig, "barrios_prio")


# ── 5. Municipio ────────────────────────────────────────────────────────────
with tabs[4]:
    _section_header(
        "Demanda al municipio",
        "Pedidos de la comunidad y distribución por ciudad.",
    )
    mun_cols = [c for c in df.columns if c.startswith("Mun_")]

    def _mun_lbl(c, width=24):
        return _wrap(c.replace("Mun_", "").replace("_", " "), width)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    # 1) Demanda total al municipio
    if mun_cols:
        pcts = (df[mun_cols].sum() / len(df) * 100).sort_values(ascending=True)
        labels = [_mun_lbl(c, 26) for c in pcts.index]
        ax1.barh(labels, pcts.values, color=BLUE, edgecolor="white")
        ax1.set_title("¿Qué le pide la gente al municipio? (% de hogares)")
        ax1.set_xlim(0, max(_safe_max(pcts.values, 0.0) * 1.18, 10))
        for i, v in enumerate(pcts.values):
            ax1.text(v + 0.5, i, f"{v:.0f}%", va="center",
                     fontsize=8, fontweight="bold", color=NAVY)

    # 2) Top 4 pedidos vs castración
    top4 = sorted(mun_cols, key=lambda c: -df[c].sum())[:4] if mun_cols else []
    if top4 and "Mascota_Castrada" in df.columns:
        rows = []
        for c in top4:
            sub = df[df[c] == 1]
            if len(sub) > 0:
                rows.append((_mun_lbl(c, 22),
                             (sub["Mascota_Castrada"].astype(str).str.lower() == "si").mean() * 100))
        if rows:
            labels = [r[0] for r in rows]
            vals = [r[1] for r in rows]
            ax2.barh(labels, vals, color=ACCENT, edgecolor="white")
            ax2.set_title("% castración entre quienes\npiden cada mejora")
            ax2.set_xlim(0, 110)
            ax2.set_xlabel("% castradas")
            for i, v in enumerate(vals):
                ax2.text(v + 1.5, i, f"{v:.0f}%", va="center",
                         fontsize=9, fontweight="bold", color=NAVY)

    # 3) Heatmap pedidos por ciudad
    if mun_cols and "Ciudad" in df.columns:
        top5 = sorted(mun_cols, key=lambda c: -df[c].sum())[:5]
        pivot = df.groupby("Ciudad")[top5].mean() * 100
        pivot.columns = [_mun_lbl(c, 14) for c in pivot.columns]
        if not pivot.empty:
            ax3.imshow(pivot.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=100)
            ax3.set_xticks(range(len(pivot.columns)))
            ax3.set_xticklabels(pivot.columns, fontsize=7)
            ax3.set_yticks(range(len(pivot.index)))
            ax3.set_yticklabels(pivot.index, fontsize=8)
            ax3.set_title("% que lo pide, por ciudad")
            ax3.grid(False)
            for i in range(pivot.shape[0]):
                for j in range(pivot.shape[1]):
                    v = pivot.values[i, j]
                    col = "white" if v > 50 else NAVY
                    ax3.text(j, i, f"{v:.0f}", ha="center", va="center",
                             color=col, fontsize=8, fontweight="bold")

    # 4) Castr. masivas vs estado castración
    col_cm = "Mun_Castraciones_Masivas"
    if col_cm in df.columns and "Mascota_Castrada" in df.columns:
        ct = pd.crosstab(df[col_cm].map({0: "No pide", 1: "Sí pide"}),
                         df["Mascota_Castrada"])
        x = np.arange(len(ct.index))
        w = 0.38
        for i, (col, color) in enumerate(zip(ct.columns, [RED, GREEN])):
            ax4.bar(x + (i - 0.5) * w, ct[col].values, w,
                    label=str(col), color=color, edgecolor="white")
            for xi, v in zip(x + (i - 0.5) * w, ct[col].values):
                if v > 0:
                    ax4.text(xi, v + 0.3, f"{int(v)}", ha="center",
                             fontsize=8, fontweight="bold", color=NAVY)
        ax4.set_xticks(x)
        ax4.set_xticklabels(ct.index)
        ax4.set_title("¿Pide castr. masivas? vs ¿castrada?")
        ax4.legend(title="¿Castrada?", fontsize=8)
    _render_fig(fig, "municipio")


# ── 6. Cuidado ──────────────────────────────────────────────────────────────
with tabs[5]:
    _section_header(
        "Cuidado responsable",
        "Indicadores combinados y diferencias por tipo de vivienda.",
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    ax1, ax2 = axes
    cuidado_cols = ["Mascota_Castrada", "Vacunadas", "Desparasitadas",
                    "Sabe_Castracion_Gratuita", "Sabe_Vacunas_Anuales"]
    nombres = ["Castradas", "Vacunadas", "Desparasit.", "Sabe Cast.\nGratis", "Sabe Vac.\nAnuales"]
    pares = [(n, _pct_si(df[c])) for n, c in zip(nombres, cuidado_cols) if c in df.columns]
    if pares:
        labels = [p[0] for p in pares]
        vals = [p[1] for p in pares]
        colors = [YELLOW, GREEN, GREEN, ACCENT, ACCENT][:len(pares)]
        ax1.bar(labels, vals, color=colors, edgecolor="white")
        ax1.set_title("Indicadores de cuidado (%)")
        ax1.set_ylim(0, 110)
        _label_bars_v(ax1, vals, fmt="{:.1f}%")

    if "Tipo_Vivienda" in df.columns:
        sub = df.copy()
        cols_b = []
        for c in ["Mascota_Castrada", "Vacunadas", "Desparasitadas"]:
            if c in sub.columns:
                sub[c + "_b"] = (sub[c].astype(str).str.lower() == "si").astype(int)
                cols_b.append(c + "_b")
        if cols_b:
            g = sub.groupby("Tipo_Vivienda")[cols_b].mean() * 100
            g.columns = ["Castradas", "Vacunadas", "Desparasit."][:len(cols_b)]
            x = np.arange(len(g.index))
            w = 0.27
            colors_b = [YELLOW, GREEN, ACCENT]
            for i, col in enumerate(g.columns):
                ax2.bar(x + (i - 1) * w, g[col].values, w,
                        label=col, color=colors_b[i], edgecolor="white")
            ax2.set_xticks(x)
            ax2.set_xticklabels([_wrap(v, 12) for v in g.index], fontsize=8)
            ax2.set_title("Cuidado por tipo de vivienda (%)")
            ax2.set_ylim(0, 110)
            ax2.set_ylabel("%")
            ax2.legend(loc="upper right", fontsize=8)
    _render_fig(fig, "cuidado")


# ── 7. Callejeros ───────────────────────────────────────────────────────────
with tabs[6]:
    _section_header(
        "Animales en la calle",
        "Frecuencia observada, salidas sin supervisión e identificación.",
    )
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    if {"Frecuencia_Callejeros", "Ciudad"} <= set(df.columns):
        ct = pd.crosstab(df["Ciudad"], df["Frecuencia_Callejeros"], normalize="index") * 100
        order = [c for c in ["Todo El Tiempo", "A Veces", "Nunca"] if c in ct.columns]
        if order:
            ct = ct[order]
            bottom = np.zeros(len(ct))
            colors_s = {"Todo El Tiempo": RED, "A Veces": YELLOW, "Nunca": GREEN}
            for col in ct.columns:
                vals_arr = ct[col].to_numpy(dtype=float)
                ax1.bar(ct.index.astype(str), vals_arr, bottom=bottom,
                        label=col, color=colors_s.get(col, ACCENT), edgecolor="white")
                bottom = bottom + vals_arr
            ax1.set_title("Frecuencia callejeros por ciudad (%)")
            ax1.set_ylim(0, 100)
            ax1.set_ylabel("%")
            ax1.tick_params(axis="x", labelsize=8)
            ax1.legend(fontsize=7, loc="lower right")

    col_solo = next((c for c in df.columns if c.startswith("Vive_Salen_solos")), None)
    if col_solo and "Tipo_Vivienda" in df.columns:
        gs = (df.groupby("Tipo_Vivienda")[col_solo]
                .apply(lambda s: pd.to_numeric(s, errors="coerce").fillna(0).mean() * 100)
                .sort_values(ascending=True))
        ax2.barh(gs.index.astype(str), gs.values, color=YELLOW, edgecolor="white")
        ax2.set_title("% que salen solos a la calle\nsegún tipo de vivienda")
        ax2.set_xlabel("%")
        gs_max = _safe_max(gs.values, default=10)
        ax2.set_xlim(0, max(gs_max * 1.25, 15))
        for i, v in enumerate(gs.values):
            if v > 0:
                ax2.text(v + 0.4, i, f"{v:.0f}%", va="center",
                         fontsize=9, fontweight="bold", color=NAVY)

    col_id = next((c for c in df.columns if c.startswith("Vive_Tienen")), None)
    if col_id:
        con_id = pd.to_numeric(df[col_id], errors="coerce").fillna(0).mean() * 100
        vals = [con_id, 100 - con_id]
        _donut(ax3, vals, ["Con identificador", "Sin identificador"],
               [GREEN, RED], "Mascotas con identificación")

    if col_solo and col_id and "Ciudad" in df.columns:
        rows = []
        for ciudad, sub in df.groupby("Ciudad"):
            cal_alto = (sub.get("Frecuencia_Callejeros", pd.Series(dtype=str))
                          .astype(str).eq("Todo El Tiempo")).mean() * 100
            sol = pd.to_numeric(sub[col_solo], errors="coerce").fillna(0).mean() * 100
            sin_id = (1 - pd.to_numeric(sub[col_id], errors="coerce").fillna(0).mean()) * 100
            rows.append((str(ciudad), cal_alto, sol, sin_id))
        if rows:
            rd = pd.DataFrame(rows, columns=["Ciudad", "Callej. alto",
                                             "Salen solos", "Sin ID"]).set_index("Ciudad")
            x = np.arange(len(rd.index))
            w = 0.27
            for i, (col, color) in enumerate(zip(rd.columns, [RED, YELLOW, PURPLE])):
                ax4.bar(x + (i - 1) * w, rd[col].values, w,
                        label=col, color=color, edgecolor="white")
            ax4.set_xticks(x)
            ax4.set_xticklabels([_wrap(s, 10) for s in rd.index], fontsize=8)
            ax4.set_title("Indicadores de riesgo por ciudad")
            ax4.set_ylabel("%")
            ax4.legend(fontsize=7)
    _render_fig(fig, "callejeros")


# ── 8. Brecha informativa ───────────────────────────────────────────────────
with tabs[7]:
    _section_header(
        "Brecha informativa",
        "Distancia entre lo que la gente sabe y lo que efectivamente hace.",
    )
    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.40, wspace=0.25)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    if {"Sabe_Castracion_Gratuita", "Mascota_Castrada"} <= set(df.columns):
        # % castración real, separado por si CONOCE o NO la castración gratuita
        sabe_si_df = df[df["Sabe_Castracion_Gratuita"].astype(str).str.lower() == "si"]
        sabe_no_df = df[df["Sabe_Castracion_Gratuita"].astype(str).str.lower() == "no"]
        p_si = _pct_si(sabe_si_df.get("Mascota_Castrada", pd.Series(dtype=str)))
        p_no = _pct_si(sabe_no_df.get("Mascota_Castrada", pd.Series(dtype=str)))
        n_si, n_no = len(sabe_si_df), len(sabe_no_df)
        if n_si + n_no > 0:
            labels = [
                f"Sabe que es gratuita\n(n={n_si})",
                f"No lo sabe\n(n={n_no})",
            ]
            vals = [p_si, p_no]
            colors_b = [GREEN, RED]
            bars = ax1.bar(labels, vals, color=colors_b, edgecolor="white",
                           width=0.55)
            ax1.set_title("¿Conocer la castración gratuita\ncambia la decisión?",
                          fontweight="bold")
            ax1.set_ylabel("% que castró su mascota")
            top = max(vals + [10]) * 1.30
            ax1.set_ylim(0, max(top, 110))
            for bar, v in zip(bars, vals):
                ax1.text(bar.get_x() + bar.get_width() / 2,
                         v + top * 0.015, f"{v:.0f}%",
                         ha="center", va="bottom", fontsize=12,
                         fontweight="bold", color=NAVY)
            # Anotación del delta entre las dos barras
            delta = p_si - p_no
            y_arrow = max(vals) + top * 0.10
            ax1.annotate("", xy=(0, y_arrow), xytext=(1, y_arrow),
                         arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1.6))
            ax1.text(0.5, y_arrow + top * 0.03,
                     f"Brecha: {delta:+.0f} pp",
                     ha="center", va="bottom", fontsize=11,
                     fontweight="bold", color=NAVY,
                     bbox=dict(boxstyle="round,pad=0.35",
                               facecolor="#fff3b0",
                               edgecolor=NAVY, linewidth=1))
            ax1.spines["top"].set_visible(False)
            ax1.spines["right"].set_visible(False)
            ax1.tick_params(axis="x", labelsize=10)
        else:
            _empty_panel(ax1, "Sin datos de castración\ny conocimiento")

    if "Sabe_Vacunas_Anuales" in df.columns:
        sv = df["Sabe_Vacunas_Anuales"].value_counts()
        colors = [GREEN if str(x).lower() == "si" else RED for x in sv.index]
        _donut(ax2, sv.values, sv.index.astype(str), colors,
               "¿Sabe sobre vacunas anuales?")

    metricas = []
    if "Humano_Responsable" in df.columns:
        metricas.append(("Se considera\nresponsable", _pct_si(df["Humano_Responsable"])))
    if "Mascota_Castrada" in df.columns:
        metricas.append(("Castra realm.", _pct_si(df["Mascota_Castrada"])))
    if "Vacunadas" in df.columns:
        metricas.append(("Vacuna realm.", _pct_si(df["Vacunadas"])))
    if "Desparasitadas" in df.columns:
        metricas.append(("Desparas. realm.", _pct_si(df["Desparasitadas"])))
    if metricas:
        labels = [m[0] for m in metricas]
        vals = [m[1] for m in metricas]
        colors = [PURPLE, YELLOW, GREEN, ACCENT][:len(metricas)]
        ax3.bar(labels, vals, color=colors, edgecolor="white")
        ax3.set_title("Autopercepción vs práctica real")
        ax3.set_ylim(0, 110)
        ax3.set_ylabel("%")
        _label_bars_v(ax3, vals, fmt="{:.0f}%")
    _render_fig(fig, "brecha")


# ── 9. Salud pública ────────────────────────────────────────────────────────
with tabs[8]:
    _section_header(
        "Salud pública",
        "Cruces de vacunación y desparasitación: zonas de riesgo zoonótico.",
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    ax1, ax2 = axes
    n = len(df)

    if {"Vacunadas", "Desparasitadas"} <= set(df.columns):
        ct = pd.crosstab(df["Vacunadas"], df["Desparasitadas"])
        ct = ct.reindex(index=["Si", "No"], columns=["Si", "No"], fill_value=0)
        # Etiqueta semántica por celda (i=vacuna, j=despar)
        cat = np.array([[0, 1], [1, 2]])  # 0 ok / 1 parcial / 2 riesgo
        cmap = ListedColormap([GREEN, YELLOW, RED])
        ax1.imshow(cat, cmap=cmap, aspect="auto", vmin=0, vmax=2)
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(["Desparasita ✓", "No desparasita ✗"], fontsize=10)
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(["Vacuna ✓", "No vacuna ✗"], fontsize=10)
        ax1.set_title("Matriz de riesgo sanitario\n(% sobre total de hogares)",
                      fontweight="bold")
        ax1.grid(False)
        # Texto descriptivo por celda
        celdas_txt = [
            ["Cobertura\ncompleta", "Solo\nvacunan"],
            ["Solo\ndesparasitan", "Doble\nriesgo"],
        ]
        for i in range(2):
            for j in range(2):
                v = int(ct.values[i, j])
                pct = v / n * 100 if n else 0
                ax1.text(j, i - 0.18, celdas_txt[i][j], ha="center", va="center",
                         fontsize=10, fontweight="bold", color="white",
                         alpha=0.9)
                ax1.text(j, i + 0.18, f"{pct:.0f}%  (n={v})",
                         ha="center", va="center",
                         fontsize=13, fontweight="bold", color="white")
        # Borde sutil entre celdas
        for spine in ax1.spines.values():
            spine.set_visible(False)
        ax1.set_xticks([-0.5, 0.5, 1.5], minor=True)
        ax1.set_yticks([-0.5, 0.5, 1.5], minor=True)
        ax1.grid(which="minor", color="white", linewidth=3)
    else:
        _empty_panel(ax1, "Sin datos de vacunación/desparasitación")

    riesgos = {}
    if "Vacunadas" in df.columns:
        riesgos["No vacuna"] = (df["Vacunadas"].astype(str).str.lower() == "no").mean() * 100
    if "Desparasitadas" in df.columns:
        riesgos["No desparasita"] = (df["Desparasitadas"].astype(str).str.lower() == "no").mean() * 100
    if {"Vacunadas", "Desparasitadas"} <= set(df.columns):
        riesgos["Ninguna de\nlas dos"] = (
            (df["Vacunadas"].astype(str).str.lower() == "no") &
            (df["Desparasitadas"].astype(str).str.lower() == "no")
        ).mean() * 100
    if riesgos:
        names = list(riesgos.keys())
        vals = list(riesgos.values())
        colors = [YELLOW, ACCENT, RED][:len(vals)]
        ax2.bar(names, vals, color=colors, edgecolor="white")
        ax2.set_title("Brecha sanitaria (% de hogares)")
        ax2.set_ylim(0, max(vals + [10]) * 1.30)
        ax2.set_ylabel("%")
        _label_bars_v(ax2, vals, fmt="{:.0f}%")
    _render_fig(fig, "salud")


# ── 10. Demografía ──────────────────────────────────────────────────────────
with tabs[9]:
    _section_header(
        "Demografía y composición",
        "Castración por tamaño familiar y densidad de mascotas.",
    )
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    if "Integrantes_Familia" in df.columns and "Mascota_Castrada" in df.columns:
        tmp = df.copy()
        tmp["_int"] = pd.to_numeric(tmp["Integrantes_Familia"], errors="coerce")
        tmp = tmp.dropna(subset=["_int"])
        if not tmp.empty:
            tmp["bucket"] = pd.cut(tmp["_int"], bins=[0, 1, 2, 4, 6, 99],
                                   labels=["1", "2", "3-4", "5-6", "7+"])
            g = tmp.groupby("bucket", observed=True).apply(
                lambda s: (s["Mascota_Castrada"].astype(str).str.lower() == "si").mean() * 100)
            ax1.bar([str(x) for x in g.index], g.values, color=ACCENT, edgecolor="white")
            ax1.set_title("% castración según tamaño de familia")
            ax1.set_xlabel("Integrantes")
            ax1.set_ylabel("% castradas")
            ax1.set_ylim(0, 115)
            _label_bars_v(ax1, g.values, fmt="{:.0f}%")

    if "Integrantes_Familia" in df.columns and "Total_Mascotas" in df.columns:
        tmp = df.copy()
        tmp["_int"] = pd.to_numeric(tmp["Integrantes_Familia"], errors="coerce")
        tmp["_tot"] = pd.to_numeric(tmp["Total_Mascotas"], errors="coerce")
        tmp = tmp.dropna(subset=["_int", "_tot"])
        tmp = tmp[tmp["_int"] > 0]
        if not tmp.empty and "Tipo_Vivienda" in tmp.columns:
            tmp["dens"] = tmp["_tot"] / tmp["_int"]
            g = tmp.groupby("Tipo_Vivienda")["dens"].mean().sort_values()
            ax2.barh(g.index.astype(str), g.values, color=PURPLE, edgecolor="white")
            ax2.set_title("Mascotas por persona, según vivienda")
            ax2.set_xlabel("Mascotas / integrante")
            if g.max() > 0:
                ax2.set_xlim(0, _safe_max(g.values, 1.0) * 1.25)
            for i, v in enumerate(g.values):
                ax2.text(v + g.max() * 0.02, i, f"{v:.2f}",
                         va="center", fontsize=9, fontweight="bold", color=NAVY)

    if "Total_Mascotas" in df.columns and "Barrio" in df.columns:
        tmp = df.copy()
        tmp["_tot"] = pd.to_numeric(tmp["Total_Mascotas"], errors="coerce").fillna(0)
        muchos = tmp[tmp["_tot"] >= 4]
        if len(muchos) > 0 and not muchos["Barrio"].dropna().empty:
            top = muchos["Barrio"].value_counts().head(8).iloc[::-1]
            top_max = _safe_max(top.values)
            ax3.barh(top.index.astype(str), top.values, color=YELLOW, edgecolor="white")
            ax3.set_title("Hogares con ≥4 mascotas (acumulación)")
            ax3.set_xlabel("Cantidad de hogares")
            ax3.set_xlim(0, top_max * 1.25)
            for i, v in enumerate(top.values):
                ax3.text(v + top_max * 0.02, i, f"{int(v)}",
                         va="center", fontsize=9, fontweight="bold", color=NAVY)
        else:
            ax3.axis("off")
            ax3.text(0.5, 0.5, "Sin hogares con ≥4 mascotas",
                     ha="center", va="center", color=NAVY, fontsize=11,
                     transform=ax3.transAxes)

    if "Mascota_Castrada" in df.columns:
        no_cast = df[df["Mascota_Castrada"].astype(str).str.lower() == "no"]

        def _s(c):
            return float(pd.to_numeric(no_cast[c], errors="coerce").fillna(0).sum()) \
                if c in no_cast.columns else 0.0

        cats = ["Perros\n(hembra)", "Perros\n(macho)", "Gatos\n(hembra)", "Gatos\n(macho)"]
        vals = [_s("Perros_Hembra"), _s("Perros_Macho"),
                _s("Gatos_Hembra"), _s("Gatos_Macho")]
        cols_b = [RED, ACCENT, RED, ACCENT]
        ax4.bar(cats, vals, color=cols_b, edgecolor="white")
        ax4.set_title("Animales SIN castrar por sexo")
        ax4.set_ylabel("Cantidad")
        max_v = max(vals + [1])
        ax4.set_ylim(0, max_v * 1.18)
        for i, v in enumerate(vals):
            if v > 0:
                ax4.text(i, v + max_v * 0.02, f"{int(v)}",
                         ha="center", fontsize=10, fontweight="bold", color=NAVY)
    _render_fig(fig, "demografia")


# ── 11. Acción municipal ────────────────────────────────────────────────────
with tabs[10]:
    _section_header(
        "Acción municipal",
        "Efecto del municipio en la castración y barrios con baja demanda institucional.",
    )
    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.40, wspace=0.30)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    if "CastEn_Municipio" in df.columns and "Sabe_Castracion_Gratuita" in df.columns:
        tmp = df.copy()
        tmp["_cm"] = pd.to_numeric(tmp["CastEn_Municipio"], errors="coerce").fillna(0)
        tmp["_cm_lbl"] = tmp["_cm"].map({1: "Castró por\nel municipio",
                                          0: "Otros / no\ncastró"})
        g = tmp.groupby("_cm_lbl").apply(
            lambda s: (s["Sabe_Castracion_Gratuita"].astype(str).str.lower() == "si").mean() * 100)
        g_vals = g.to_numpy(dtype=float)
        ax1.bar(g.index.astype(str), g_vals, color=[GREEN, YELLOW][:len(g)],
                edgecolor="white")
        ax1.set_title("% que sabe sobre castración gratuita")
        ax1.set_ylabel("%")
        ax1.set_ylim(0, 110)
        _label_bars_v(ax1, g_vals, fmt="{:.0f}%")

    if "Mun_Castraciones_Masivas" in df.columns and "Mascota_Castrada" in df.columns:
        tmp = df.copy()
        tmp["_pide"] = pd.to_numeric(tmp["Mun_Castraciones_Masivas"], errors="coerce").fillna(0)
        tmp["_pide_lbl"] = tmp["_pide"].map({1: "Pide castr.\nmasivas", 0: "No las pide"})
        g = tmp.groupby("_pide_lbl").apply(
            lambda s: (s["Mascota_Castrada"].astype(str).str.lower() == "no").mean() * 100)
        g_vals = g.to_numpy(dtype=float)
        ax2.bar(g.index.astype(str), g_vals, color=[RED, ACCENT][:len(g)],
                edgecolor="white")
        ax2.set_title("% SIN castrar, según si pide castr. masivas")
        ax2.set_ylabel("% sin castrar")
        ax2.set_ylim(0, 110)
        _label_bars_v(ax2, g_vals, fmt="{:.0f}%")

    col_no_part = "Mun_No_es_necesaria_la_participación_del_municipio"
    if col_no_part in df.columns and "Barrio" in df.columns:
        tmp = df.copy()
        tmp["_no_mun"] = pd.to_numeric(tmp[col_no_part], errors="coerce").fillna(0)
        g = tmp.groupby("Barrio").agg(no_demanda=("_no_mun", "mean"),
                                      n=("_no_mun", "size"))
        g = g[g["n"] >= 3].sort_values("no_demanda", ascending=True).tail(8)
        if not g.empty:
            pcts = g["no_demanda"].to_numpy(dtype=float) * 100
            ax3.barh(g.index.astype(str), pcts, color=RED, edgecolor="white")
            ax3.set_title("Barrios donde más hogares dicen «no es necesaria la participación del municipio»")
            ax3.set_xlabel("% del barrio")
            ax3.set_xlim(0, 110)
            for i, v in enumerate(pcts):
                ax3.text(v + 1.5, i, f"{v:.0f}%", va="center",
                         fontsize=9, fontweight="bold", color=NAVY)
    _render_fig(fig, "accion_mun")


# ── 12. Tabla ───────────────────────────────────────────────────────────────
with tabs[11]:
    _section_header(
        "Datos filtrados",
        "Tabla detallada con búsqueda y descarga.",
    )
    st.caption(f"{len(df):,} filas — podés ordenar y buscar.".replace(",", "."))
    st.dataframe(df, use_container_width=True, height=520)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=csv_bytes,
        file_name="mascotas_filtrado.csv",
        mime="text/csv",
    )


# ── PDF Resumen ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📄 Reporte PDF resumen")
st.caption("Genera un PDF con los gráficos clave (filtros aplicados).")


def construir_pdf(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        # Portada
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        ax.text(0.5, 0.65, "Reporte — Cuidado de Mascotas",
                ha="center", va="center", fontsize=26, fontweight="bold", color=NAVY)
        ax.text(0.5, 0.55, "Dashboard Web · Streamlit",
                ha="center", va="center", fontsize=14, color=ACCENT)
        ax.text(0.5, 0.45, f"{len(df):,} encuestas · {datetime.now():%Y-%m-%d %H:%M}".replace(",", "."),
                ha="center", va="center", fontsize=11, color=NAVY)
        pdf.savefig(fig); plt.close(fig)

        # KPIs
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.set_title("Indicadores clave (% Sí)", fontsize=15, color=NAVY, fontweight="bold")
        kpis = [
            ("Castración", _pct_si(df.get("Mascota_Castrada", pd.Series(dtype=str)))),
            ("Vacunación", _pct_si(df.get("Vacunadas", pd.Series(dtype=str)))),
            ("Desparasitación", _pct_si(df.get("Desparasitadas", pd.Series(dtype=str)))),
            ("Sabe vacunas anuales", _pct_si(df.get("Sabe_Vacunas_Anuales", pd.Series(dtype=str)))),
            ("Sabe castración gratis", _pct_si(df.get("Sabe_Castracion_Gratuita", pd.Series(dtype=str)))),
            ("Humano responsable", _pct_si(df.get("Humano_Responsable", pd.Series(dtype=str)))),
        ]
        names = [k[0] for k in kpis][::-1]
        vals = [k[1] for k in kpis][::-1]
        ax.barh(names, vals, color=ACCENT, edgecolor="white")
        ax.set_xlim(0, 115)
        ax.set_xlabel("% Sí")
        for i, v in enumerate(vals):
            ax.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=10,
                    color=NAVY, fontweight="bold")
        pdf.savefig(fig); plt.close(fig)

        # Top barrios
        if "Barrio" in df.columns and not df["Barrio"].isna().all():
            top = df["Barrio"].value_counts().head(15).iloc[::-1]
            top_vals = top.to_numpy(dtype=float)
            fig, ax = plt.subplots(figsize=(11, 6))
            ax.barh(top.index.astype(str), top_vals, color=BLUE, edgecolor="white")
            ax.set_title("Top 15 barrios por encuestas", fontweight="bold", color=NAVY)
            for i, v in enumerate(top_vals):
                ax.text(v + _safe_max(top_vals, 1.0) * 0.01, i, f"{int(v)}",
                        va="center", fontsize=9, fontweight="bold", color=NAVY)
            pdf.savefig(fig); plt.close(fig)

        # Pedidos al municipio
        cols_mun = [c for c in df.columns if c.startswith("Mun_")]
        if cols_mun:
            sums = df[cols_mun].sum().sort_values(ascending=True)
            sums_vals = sums.to_numpy(dtype=float)
            labels = [c.replace("Mun_", "").replace("_", " ") for c in sums.index]
            fig, ax = plt.subplots(figsize=(11, 5))
            ax.barh(labels, sums_vals, color=ACCENT, edgecolor="white")
            ax.set_title("Pedidos al municipio", fontweight="bold", color=NAVY)
            for i, v in enumerate(sums_vals):
                ax.text(v + _safe_max(sums_vals, 1.0) * 0.01, i, f"{int(v)}",
                        va="center", fontsize=9, fontweight="bold", color=NAVY)
            pdf.savefig(fig); plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


col_pdf, _ = st.columns([1, 4])
with col_pdf:
    if st.button("Generar PDF", type="primary"):
        with st.spinner("Generando reporte..."):
            pdf_bytes = construir_pdf(df)
        st.download_button(
            "⬇️ Descargar reporte.pdf",
            data=pdf_bytes,
            file_name=f"reporte_mascotas_{datetime.now():%Y%m%d_%H%M}.pdf",
            mime="application/pdf",
        )

st.markdown(
    f"<div style='text-align:center; color:#7a8b99; font-size:12px; margin-top:30px; "
    f"padding:14px; border-top:1px solid #e6eaf0;'>"
    f"<strong style='color:#1f3a5f;'>Dashboard · Cuidado de Mascotas</strong>"
    f" &nbsp;·&nbsp; {len(df):,} registros filtrados sobre {len(df_full):,} totales"
    f" &nbsp;·&nbsp; Última actualización: {datetime.now():%Y-%m-%d %H:%M}"
    f"</div>".replace(",", "."),
    unsafe_allow_html=True,
)
