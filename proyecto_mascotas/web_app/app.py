"""
Dashboard Web — Cuidado de Mascotas
====================================
Versión Streamlit del dashboard original (Tkinter).
Pensada para deploy en Streamlit Community Cloud.

Ejecutar localmente:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # backend no-GUI: indispensable en servidor
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages

# ── Configuración base ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DEFAULT = os.path.join(BASE_DIR, "mascotas_limpio.csv")

# Paleta clínica/teal (idéntica al dashboard de escritorio)
ACCENT = "#2a9d8f"
GREEN = "#52b788"
RED = "#e63946"
YELLOW = "#f4a261"
BLUE = "#4895ef"
NAVY = "#1f3a5f"
PALETTE = [ACCENT, BLUE, YELLOW, GREEN, RED, "#9d4edd", "#ff8fab"]

st.set_page_config(
    page_title="Dashboard — Cuidado de Mascotas",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

plt.rcParams.update({
    "axes.facecolor": "#ffffff",
    "figure.facecolor": "#ffffff",
    "axes.edgecolor": "#cfd8dc",
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "axes.titlecolor": NAVY,
    "axes.titleweight": "bold",
    "font.size": 9,
    "axes.grid": True,
    "grid.color": "#dde6ea",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ── Carga de datos ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_csv(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    if "Marca_Temporal" in df.columns:
        df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"], errors="coerce")
    # variables derivadas
    for c in ("Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"):
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


def _annotate_bars(ax, horizontal=False, fmt="{:.0f}"):
    for p in ax.patches:
        if horizontal:
            w = p.get_width()
            if w == 0:
                continue
            ax.text(w + 0.5, p.get_y() + p.get_height() / 2,
                    fmt.format(w), va="center", ha="left",
                    color=NAVY, fontsize=8, fontweight="bold")
        else:
            h = p.get_height()
            if h == 0:
                continue
            ax.text(p.get_x() + p.get_width() / 2, h + 0.5,
                    fmt.format(h), ha="center", va="bottom",
                    color=NAVY, fontsize=8, fontweight="bold")


# ── Sidebar: fuente de datos + filtros ──────────────────────────────────────
st.sidebar.title("🐾 Dashboard Mascotas")
st.sidebar.caption("Relevamiento de cuidado responsable")

uploaded = st.sidebar.file_uploader(
    "Subí tu CSV limpio (opcional)", type=["csv"],
    help="Si no subís nada, se usa el dataset incluido en la app."
)

try:
    df_full = cargar_csv(uploaded if uploaded is not None else CSV_DEFAULT)
except FileNotFoundError:
    st.error(
        "No se encontró `mascotas_limpio.csv`. Subí un CSV desde el panel lateral "
        "o asegurate de que el archivo esté junto a `app.py`."
    )
    st.stop()

st.sidebar.markdown("### Filtros")


def _opciones(col: str) -> list[str]:
    if col not in df_full.columns:
        return []
    return sorted(df_full[col].dropna().astype(str).unique().tolist())


ciudades = st.sidebar.multiselect("Ciudad", _opciones("Ciudad"))
barrios = st.sidebar.multiselect("Barrio", _opciones("Barrio"))
viviendas = st.sidebar.multiselect("Tipo de vivienda", _opciones("Tipo_Vivienda"))
tipos_mascota = st.sidebar.multiselect("Tipo de mascotas", _opciones("Tipo_Mascotas"))

df = df_full.copy()
if ciudades:
    df = df[df["Ciudad"].astype(str).isin(ciudades)]
if barrios:
    df = df[df["Barrio"].astype(str).isin(barrios)]
if viviendas:
    df = df[df["Tipo_Vivienda"].astype(str).isin(viviendas)]
if tipos_mascota:
    df = df[df["Tipo_Mascotas"].astype(str).isin(tipos_mascota)]

st.sidebar.markdown(f"**Registros filtrados:** {len(df):,}".replace(",", "."))
if st.sidebar.button("🔄 Limpiar filtros"):
    st.rerun()

# ── Cabecera ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background: linear-gradient(90deg, {ACCENT} 0%, {BLUE} 100%);
                padding: 18px 24px; border-radius: 10px; margin-bottom: 18px;">
        <h1 style="color:white; margin:0;">Clínica Veterinaria — Dashboard de Cuidado de Mascotas</h1>
        <p style="color:#eaf2f5; margin:4px 0 0 0;">
            Análisis interactivo del relevamiento · {len(df):,} encuestas filtradas
        </p>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No hay registros con los filtros actuales. Probá ajustar el panel lateral.")
    st.stop()

# ── KPIs ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total encuestas", f"{len(df):,}".replace(",", "."))
col2.metric("Total mascotas", f"{int(df['Total_Mascotas'].sum()):,}".replace(",", "."))
col3.metric("% Castradas", f"{_pct_si(df.get('Mascota_Castrada', pd.Series(dtype=str))):.1f}%")
col4.metric("% Vacunadas", f"{_pct_si(df.get('Vacunadas', pd.Series(dtype=str))):.1f}%")
col5.metric("% Desparasitadas", f"{_pct_si(df.get('Desparasitadas', pd.Series(dtype=str))):.1f}%")

st.divider()

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_resumen, tab_cast, tab_geo, tab_mun, tab_cuidado, tab_calle, tab_tabla = st.tabs([
    "📊 Resumen", "✂️ Castración", "🗺️ Geografía", "🏛️ Municipio",
    "💊 Cuidado", "🐕 Callejeros", "📋 Tabla"
])

# ── Resumen ─────────────────────────────────────────────────────────────────
with tab_resumen:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tipo de mascotas")
        if "Tipo_Mascotas" in df.columns:
            counts = df["Tipo_Mascotas"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(counts.index.astype(str), counts.values, color=PALETTE[: len(counts)])
            ax.set_ylabel("Encuestas")
            plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
            _annotate_bars(ax)
            st.pyplot(fig, clear_figure=True)
    with c2:
        st.subheader("Tipo de vivienda")
        if "Tipo_Vivienda" in df.columns:
            counts = df["Tipo_Vivienda"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.barh(counts.index.astype(str)[::-1], counts.values[::-1], color=ACCENT)
            ax.set_xlabel("Encuestas")
            _annotate_bars(ax, horizontal=True)
            st.pyplot(fig, clear_figure=True)

    st.subheader("Composición de la población de mascotas")
    totales = {
        "Perros macho": df.get("Perros_Macho", pd.Series([0])).sum(),
        "Perros hembra": df.get("Perros_Hembra", pd.Series([0])).sum(),
        "Gatos macho": df.get("Gatos_Macho", pd.Series([0])).sum(),
        "Gatos hembra": df.get("Gatos_Hembra", pd.Series([0])).sum(),
    }
    fig, ax = plt.subplots(figsize=(9, 3.5))
    nombres = list(totales.keys())
    valores = [float(v) for v in totales.values()]
    ax.bar(nombres, valores, color=[BLUE, "#a8c7ec", ACCENT, "#a8d8d2"])
    ax.set_ylabel("Cantidad de animales")
    _annotate_bars(ax)
    st.pyplot(fig, clear_figure=True)


# ── Castración ──────────────────────────────────────────────────────────────
with tab_cast:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("¿Mascotas castradas?")
        if "Mascota_Castrada" in df.columns:
            counts = df["Mascota_Castrada"].value_counts()
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = [GREEN if str(x).lower() == "si" else RED for x in counts.index]
            ax.pie(counts.values, labels=counts.index.astype(str), colors=colors,
                   autopct="%1.1f%%", startangle=90,
                   wedgeprops={"edgecolor": "white", "linewidth": 2})
            ax.axis("equal")
            st.pyplot(fig, clear_figure=True)

    with c2:
        st.subheader("¿Sabe que la castración es gratuita?")
        if "Sabe_Castracion_Gratuita" in df.columns:
            counts = df["Sabe_Castracion_Gratuita"].value_counts()
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = [GREEN if str(x).lower() == "si" else YELLOW for x in counts.index]
            ax.pie(counts.values, labels=counts.index.astype(str), colors=colors,
                   autopct="%1.1f%%", startangle=90,
                   wedgeprops={"edgecolor": "white", "linewidth": 2})
            ax.axis("equal")
            st.pyplot(fig, clear_figure=True)

    st.subheader("¿Dónde castraron?")
    cols_cast = [c for c in df.columns if c.startswith("CastEn_")]
    if cols_cast:
        sums = df[cols_cast].sum().sort_values(ascending=True)
        labels = [c.replace("CastEn_", "").replace("_", " ") for c in sums.index]
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.barh(labels, sums.values, color=ACCENT)
        ax.set_xlabel("Encuestas")
        _annotate_bars(ax, horizontal=True)
        st.pyplot(fig, clear_figure=True)


# ── Geografía ───────────────────────────────────────────────────────────────
with tab_geo:
    st.subheader("Encuestas por barrio")
    if "Barrio" in df.columns:
        top = df["Barrio"].value_counts().head(20).iloc[::-1]
        fig, ax = plt.subplots(figsize=(9, max(4, 0.3 * len(top))))
        ax.barh(top.index.astype(str), top.values, color=BLUE)
        ax.set_xlabel("Encuestas")
        _annotate_bars(ax, horizontal=True)
        st.pyplot(fig, clear_figure=True)

    st.subheader("Castración por barrio (top 15)")
    if {"Barrio", "Mascota_Castrada"} <= set(df.columns):
        g = (df.assign(_si=df["Mascota_Castrada"].astype(str).str.lower().eq("si"))
               .groupby("Barrio")["_si"].agg(["mean", "count"])
               .query("count >= 3")
               .sort_values("mean", ascending=True)
               .tail(15))
        if not g.empty:
            fig, ax = plt.subplots(figsize=(9, max(4, 0.35 * len(g))))
            ax.barh(g.index.astype(str), g["mean"].values * 100, color=GREEN)
            ax.set_xlabel("% castradas")
            ax.set_xlim(0, 100)
            for i, (m, n) in enumerate(zip(g["mean"].values, g["count"].values)):
                ax.text(m * 100 + 1, i, f"{m*100:.0f}% (n={int(n)})",
                        va="center", fontsize=8, color=NAVY)
            st.pyplot(fig, clear_figure=True)


# ── Municipio ───────────────────────────────────────────────────────────────
with tab_mun:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("¿Presencia del municipio?")
        if "Municipio_Presente" in df.columns:
            counts = df["Municipio_Presente"].value_counts()
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = [GREEN if str(x).lower() == "si" else RED for x in counts.index]
            ax.pie(counts.values, labels=counts.index.astype(str), colors=colors,
                   autopct="%1.1f%%", startangle=90,
                   wedgeprops={"edgecolor": "white", "linewidth": 2})
            ax.axis("equal")
            st.pyplot(fig, clear_figure=True)
    with c2:
        st.subheader("Pedidos al municipio")
        cols_mun = [c for c in df.columns if c.startswith("Mun_")]
        if cols_mun:
            sums = df[cols_mun].sum().sort_values(ascending=True)
            labels = [c.replace("Mun_", "").replace("_", " ") for c in sums.index]
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.barh(labels, sums.values, color=BLUE)
            ax.set_xlabel("Encuestas")
            _annotate_bars(ax, horizontal=True)
            st.pyplot(fig, clear_figure=True)


# ── Cuidado ─────────────────────────────────────────────────────────────────
with tab_cuidado:
    st.subheader("Indicadores de cuidado responsable (% Sí)")
    indicadores = {
        "Castración": "Mascota_Castrada",
        "Vacunación": "Vacunadas",
        "Desparasitación": "Desparasitadas",
        "Sabe vacunas anuales": "Sabe_Vacunas_Anuales",
        "Sabe castración gratis": "Sabe_Castracion_Gratuita",
        "Humano responsable": "Humano_Responsable",
    }
    pares = [(k, _pct_si(df[c])) for k, c in indicadores.items() if c in df.columns]
    if pares:
        nombres = [p[0] for p in pares]
        valores = [p[1] for p in pares]
        fig, ax = plt.subplots(figsize=(9, 4))
        bars = ax.barh(nombres[::-1], valores[::-1], color=ACCENT)
        ax.set_xlim(0, 100)
        ax.set_xlabel("% Sí")
        for bar, v in zip(bars, valores[::-1]):
            ax.text(v + 1, bar.get_y() + bar.get_height() / 2,
                    f"{v:.1f}%", va="center", fontsize=9, color=NAVY, fontweight="bold")
        st.pyplot(fig, clear_figure=True)

    st.subheader("¿Cómo viven las mascotas?")
    cols_vive = [c for c in df.columns if c.startswith("Vive_")]
    if cols_vive:
        sums = df[cols_vive].sum().sort_values(ascending=True)
        labels = [c.replace("Vive_", "").replace("_", " ") for c in sums.index]
        fig, ax = plt.subplots(figsize=(9, 3.5))
        ax.barh(labels, sums.values, color=GREEN)
        ax.set_xlabel("Encuestas")
        _annotate_bars(ax, horizontal=True)
        st.pyplot(fig, clear_figure=True)


# ── Callejeros ──────────────────────────────────────────────────────────────
with tab_calle:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Frecuencia de callejeros observados")
        if "Frecuencia_Callejeros" in df.columns:
            counts = df["Frecuencia_Callejeros"].value_counts()
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(counts.index.astype(str), counts.values, color=YELLOW)
            ax.set_ylabel("Encuestas")
            plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
            _annotate_bars(ax)
            st.pyplot(fig, clear_figure=True)
    with c2:
        st.subheader("Animales perdidos frecuentes")
        if "Animal_Perdido_Frecuente" in df.columns:
            counts = df["Animal_Perdido_Frecuente"].value_counts().head(8)
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.barh(counts.index.astype(str)[::-1], counts.values[::-1], color=RED)
            ax.set_xlabel("Encuestas")
            _annotate_bars(ax, horizontal=True)
            st.pyplot(fig, clear_figure=True)


# ── Tabla ───────────────────────────────────────────────────────────────────
with tab_tabla:
    st.subheader("Datos filtrados")
    st.caption(f"{len(df):,} filas — podés ordenar y buscar.".replace(",", "."))
    st.dataframe(df, use_container_width=True, height=520)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=csv_bytes,
        file_name="mascotas_filtrado.csv",
        mime="text/csv",
    )


# ── Generación de PDF resumen ───────────────────────────────────────────────
st.divider()
st.subheader("📄 Reporte PDF resumen")
st.caption("Genera un PDF con los gráficos clave del dashboard (filtros aplicados).")


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
        ax.text(0.5, 0.45, f"{len(df):,} encuestas · generado {datetime.now():%Y-%m-%d %H:%M}".replace(",", "."),
                ha="center", va="center", fontsize=11, color=NAVY)
        pdf.savefig(fig); plt.close(fig)

        # KPIs
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.axis("off")
        ax.set_title("Indicadores clave (% Sí)", fontsize=16, fontweight="bold", color=NAVY, pad=20)
        kpis = [
            ("Castración", _pct_si(df.get("Mascota_Castrada", pd.Series(dtype=str)))),
            ("Vacunación", _pct_si(df.get("Vacunadas", pd.Series(dtype=str)))),
            ("Desparasitación", _pct_si(df.get("Desparasitadas", pd.Series(dtype=str)))),
            ("Sabe vacunas anuales", _pct_si(df.get("Sabe_Vacunas_Anuales", pd.Series(dtype=str)))),
            ("Sabe castración gratis", _pct_si(df.get("Sabe_Castracion_Gratuita", pd.Series(dtype=str)))),
            ("Humano responsable", _pct_si(df.get("Humano_Responsable", pd.Series(dtype=str)))),
        ]
        nombres = [k[0] for k in kpis]
        valores = [k[1] for k in kpis]
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.7])
        bars = ax2.barh(nombres[::-1], valores[::-1], color=ACCENT)
        ax2.set_xlim(0, 100); ax2.set_xlabel("% Sí")
        for bar, v in zip(bars, valores[::-1]):
            ax2.text(v + 1, bar.get_y() + bar.get_height() / 2,
                     f"{v:.1f}%", va="center", fontsize=10, color=NAVY, fontweight="bold")
        pdf.savefig(fig); plt.close(fig)

        # Top barrios
        if "Barrio" in df.columns and not df["Barrio"].isna().all():
            top = df["Barrio"].value_counts().head(15).iloc[::-1]
            fig, ax = plt.subplots(figsize=(11, 6))
            ax.barh(top.index.astype(str), top.values, color=BLUE)
            ax.set_title("Top 15 barrios por encuestas", fontweight="bold", color=NAVY)
            _annotate_bars(ax, horizontal=True)
            pdf.savefig(fig); plt.close(fig)

        # Municipio
        cols_mun = [c for c in df.columns if c.startswith("Mun_")]
        if cols_mun:
            sums = df[cols_mun].sum().sort_values(ascending=True)
            labels = [c.replace("Mun_", "").replace("_", " ") for c in sums.index]
            fig, ax = plt.subplots(figsize=(11, 5))
            ax.barh(labels, sums.values, color=ACCENT)
            ax.set_title("Pedidos al municipio", fontweight="bold", color=NAVY)
            _annotate_bars(ax, horizontal=True)
            pdf.savefig(fig); plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


col_pdf, _ = st.columns([1, 3])
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
    f"<div style='text-align:center; color:#7a8b99; font-size:12px; margin-top:30px;'>"
    f"Dashboard Web · Cuidado de Mascotas · {datetime.now():%Y}"
    f"</div>",
    unsafe_allow_html=True,
)
