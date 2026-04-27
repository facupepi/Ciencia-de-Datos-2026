"""
Reporte Visual General — PDF
Genera un PDF con gráficos y tablas para TODAS las columnas,
incluyendo las columnas one-hot de multi-respuesta.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import os
import textwrap

# ── Configuración ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE_DIR, "mascotas_limpio.csv")
PDF_PATH = os.path.join(BASE_DIR, "reporte_general.pdf")
INFORME_MD = os.path.join(BASE_DIR, "informe_limpieza.md")

sns.set_theme(style="whitegrid", palette="Set2", font_scale=1.0)
plt.rcParams["figure.dpi"] = 150

df = pd.read_csv(CSV)
df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"])
N = len(df)

# ── Helpers ─────────────────────────────────────────────────────────────────

def portada(pdf, titulo, subtitulo=""):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.6, titulo, transform=ax.transAxes,
            fontsize=28, fontweight="bold", ha="center", va="center",
            color="#2c3e50")
    ax.text(0.5, 0.45, subtitulo, transform=ax.transAxes,
            fontsize=14, ha="center", va="center", color="#7f8c8d")
    ax.text(0.5, 0.30, f"Dataset: mascotas_limpio.csv — {N} registros, {len(df.columns)} columnas",
            transform=ax.transAxes, fontsize=11, ha="center", va="center", color="#95a5a6")
    pdf.savefig(fig)
    plt.close()


def pagina_titulo(pdf, titulo):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.5, titulo, transform=ax.transAxes,
            fontsize=22, fontweight="bold", ha="center", va="center",
            color="#2c3e50")
    pdf.savefig(fig)
    plt.close()


def _md_inline_clean(s: str) -> str:
    """Quita marcas inline (**, *, `) y emojis problemáticos."""
    s = s.replace("**", "").replace("`", "")
    # reemplazar emojis comunes por texto
    for emo, rep in (("✅", "[OK]"), ("⚠️", "[!]"), ("⚠", "[!]"),
                     ("🎉", ""), ("ℹ", "i"), ("✔", "[OK]"), ("📂", ""),
                     ("📋", ""), ("📄", ""), ("📊", ""), ("📝", ""),
                     ("📁", ""), ("▶", ">"), ("❌", "[X]")):
        s = s.replace(emo, rep)
    return s


def _parse_md_blocks(lineas):
    """Agrupa el markdown en bloques tipados: heading, table, bullet, text, hr, blank."""
    bloques = []
    i = 0
    n = len(lineas)
    while i < n:
        s = lineas[i].rstrip()
        # tabla: línea empieza con '|' y la siguiente es separador ---
        if s.startswith("|") and i + 1 < n and set(lineas[i + 1].strip()) <= set("|-: "):
            header = [c.strip() for c in s.strip("|").split("|")]
            i += 2  # saltar separador
            filas = []
            while i < n and lineas[i].lstrip().startswith("|"):
                row = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                filas.append(row)
                i += 1
            bloques.append(("table", header, filas))
            continue
        if s.startswith("# "):
            bloques.append(("h1", _md_inline_clean(s[2:])))
        elif s.startswith("## "):
            bloques.append(("h2", _md_inline_clean(s[3:])))
        elif s.startswith("### "):
            bloques.append(("h3", _md_inline_clean(s[4:])))
        elif s.startswith("---"):
            bloques.append(("hr",))
        elif s.startswith(("- ", "* ")):
            bloques.append(("bullet", _md_inline_clean(s[2:])))
        elif s.startswith("> "):
            bloques.append(("quote", _md_inline_clean(s[2:])))
        elif s.strip() == "":
            bloques.append(("blank",))
        else:
            bloques.append(("text", _md_inline_clean(s)))
        i += 1
    return bloques


# Alturas estimadas (en unidades de ejes) por tipo de bloque
_ALTURAS = {
    "h1": 0.055, "h2": 0.042, "h3": 0.034,
    "text": 0.022, "bullet": 0.022, "quote": 0.024,
    "hr": 0.020, "blank": 0.015,
}


def _altura_tabla(filas: int) -> float:
    # encabezado + filas + margen
    return 0.045 + filas * 0.028


def _render_bloque(ax, bloque, y: float) -> float:
    """Dibuja un bloque a partir de y (coords de ejes) y devuelve la nueva y."""
    tipo = bloque[0]
    if tipo == "h1":
        ax.text(0.06, y, bloque[1], transform=ax.transAxes,
                fontsize=16, fontweight="bold", color="#1a5276", va="top")
        return y - _ALTURAS["h1"]
    if tipo == "h2":
        ax.text(0.06, y, bloque[1], transform=ax.transAxes,
                fontsize=13, fontweight="bold", color="#2471a3", va="top")
        # línea bajo el h2
        ax.plot([0.06, 0.94], [y - 0.028, y - 0.028],
                transform=ax.transAxes, color="#d5dbdb", linewidth=0.8)
        return y - _ALTURAS["h2"]
    if tipo == "h3":
        ax.text(0.06, y, bloque[1], transform=ax.transAxes,
                fontsize=11, fontweight="bold", color="#2e86c1", va="top")
        return y - _ALTURAS["h3"]
    if tipo == "text":
        for sub in textwrap.wrap(bloque[1], width=115) or [""]:
            ax.text(0.06, y, sub, transform=ax.transAxes,
                    fontsize=9.5, color="#2c3e50", va="top")
            y -= _ALTURAS["text"]
        return y
    if tipo == "bullet":
        for k, sub in enumerate(textwrap.wrap(bloque[1], width=110) or [""]):
            prefix = "•  " if k == 0 else "   "
            ax.text(0.08, y, prefix + sub, transform=ax.transAxes,
                    fontsize=9.5, color="#2c3e50", va="top")
            y -= _ALTURAS["bullet"]
        return y
    if tipo == "quote":
        for sub in textwrap.wrap(bloque[1], width=110) or [""]:
            ax.text(0.09, y, sub, transform=ax.transAxes,
                    fontsize=9, color="#566573", style="italic", va="top")
            y -= _ALTURAS["quote"]
        return y
    if tipo == "hr":
        ax.plot([0.06, 0.94], [y - 0.008, y - 0.008],
                transform=ax.transAxes, color="#bdc3c7", linewidth=0.6)
        return y - _ALTURAS["hr"]
    if tipo == "blank":
        return y - _ALTURAS["blank"]
    return y


def _draw_table_on_ax(ax, header, filas, y: float) -> float:
    """Dibuja una tabla sobre ax usando ax.table(bbox=...) en coordenadas de ejes.
    Mismo sistema de coordenadas que ax.text(transform=ax.transAxes).
    Devuelve la nueva y tras la tabla."""
    if not filas or not header:
        return y

    ROW_H = 0.032           # altura de cada fila en coords de ejes
    n_total = len(filas) + 1  # filas de datos + encabezado
    total_h = n_total * ROW_H
    bottom = y - total_h

    # bbox=[left, bottom, width, height] en coordenadas del eje (transAxes)
    tab = ax.table(
        cellText=[[str(v) for v in row] for row in filas],
        colLabels=[str(h) for h in header],
        bbox=[0.06, bottom, 0.88, total_h],
        cellLoc="center",
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.5)

    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#d5dbdb")
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f4f6f7")
        else:
            cell.set_facecolor("white")

    return bottom - 0.012  # pequeño espacio tras la tabla


def renderizar_informe_md(pdf, md_path: str):
    """Renderiza el informe de limpieza .md como páginas formateadas en el PDF.

    Soporta headings, tablas, bullets, separadores y texto.
    """
    if not os.path.exists(md_path):
        return
    with open(md_path, "r", encoding="utf-8") as f:
        lineas = f.read().splitlines()

    pagina_titulo(pdf, "Informe de Limpieza del Dataset")

    bloques = _parse_md_blocks(lineas)

    Y_TOP = 0.96
    Y_BOT = 0.06

    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    y = Y_TOP

    def _nueva_pagina():
        nonlocal fig, ax, y
        pdf.savefig(fig)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        y = Y_TOP

    for b in bloques:
        tipo = b[0]
        if tipo == "table":
            _, header, filas = b
            ROW_H = 0.032
            restante = list(filas)
            while restante:
                # cuántas filas de datos caben (descontar encabezado + gap)
                espacio = y - Y_BOT - ROW_H - 0.012
                max_filas = max(1, int(espacio / ROW_H))
                chunk = restante[:max_filas]
                restante = restante[max_filas:]
                y = _draw_table_on_ax(ax, header, chunk, y)
                if restante:
                    _nueva_pagina()
        else:
            # estimar altura aprox para decidir salto
            alto = _ALTURAS.get(tipo, 0.022)
            if y - alto < Y_BOT:
                _nueva_pagina()
            y = _render_bloque(ax, b, y)

    # última página
    pdf.savefig(fig)
    plt.close(fig)


MAX_FILAS_POR_PAGINA = 22


def _render_tabla(pdf, data, col_labels, titulo, col_widths=None, fontsize=9):
    n_rows = len(data)
    fig_height = min(max(3.5, 1.8 + n_rows * 0.32), 10.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.axis("off")
    ax.set_title(titulo, fontsize=13, fontweight="bold", pad=15, loc="left")
    table = ax.table(cellText=data, colLabels=col_labels, loc="center",
                     cellLoc="center", colWidths=col_widths)
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.35)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#ecf0f1")
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def tabla_pagina(pdf, data, col_labels, titulo, col_widths=None, fontsize=9):
    """Renderiza tabla en una o varias páginas según cantidad de filas."""
    if len(data) <= MAX_FILAS_POR_PAGINA:
        _render_tabla(pdf, data, col_labels, titulo, col_widths, fontsize)
        return
    total_pag = (len(data) + MAX_FILAS_POR_PAGINA - 1) // MAX_FILAS_POR_PAGINA
    for i in range(0, len(data), MAX_FILAS_POR_PAGINA):
        chunk = data[i:i + MAX_FILAS_POR_PAGINA]
        sub = f" (pág. {i // MAX_FILAS_POR_PAGINA + 1}/{total_pag})"
        _render_tabla(pdf, chunk, col_labels, titulo + sub, col_widths, fontsize)


def pie_limpio(ax, serie, titulo="", palette="Set2"):
    """Pie chart con leyenda lateral y % solo en slices ≥ 3%. Sin superposición."""
    valores = serie.values
    etiquetas = [str(i) for i in serie.index]
    total = valores.sum()
    colors = sns.color_palette(palette, len(valores))

    def fmt(pct):
        return f"{pct:.1f}%" if pct >= 3 else ""

    wedges, _, autotexts = ax.pie(
        valores,
        labels=None,
        autopct=fmt,
        startangle=90,
        colors=colors,
        pctdistance=0.72,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(9)
        t.set_fontweight("bold")
    leyenda = [f"{l} ({v}, {v/total*100:.1f}%)" for l, v in zip(etiquetas, valores)]
    ax.legend(wedges, leyenda, loc="center left",
              bbox_to_anchor=(1.02, 0.5), fontsize=8, frameon=False)
    if titulo:
        ax.set_title(titulo)
    ax.set_ylabel("")


# ═══════════════════════════════════════════════════════════════════════════
# Pre-detectar archivo bloqueado (VS Code preview, etc.)
_pdf_path_out = PDF_PATH
if os.path.exists(PDF_PATH):
    try:
        with open(PDF_PATH, "ab"):
            pass
    except PermissionError:
        _pdf_path_out = PDF_PATH.replace(".pdf", "_nuevo.pdf")
        print(f"⚠ {os.path.basename(PDF_PATH)} bloqueado, guardando como {os.path.basename(_pdf_path_out)}")

with PdfPages(_pdf_path_out) as pdf:

    # ── FOOTER GLOBAL: integrantes del grupo en cada hoja ───────────────
    _FOOTER_TEXT = ("Pepino, Facundo  |  Truchet, Mauricio  |"
                    "  Gamarra, Jael  |  Silvestro, María Azul")
    _orig_savefig = pdf.savefig
    def _savefig_footer(figure=None, *a, **kw):
        f = figure if figure is not None else plt.gcf()
        f.text(0.98, 0.02, _FOOTER_TEXT, ha="right", va="bottom",
               fontsize=7.5, color="#555555", style="italic")
        return _orig_savefig(f, *a, **kw)
    pdf.savefig = _savefig_footer  # type: ignore[assignment]

    # ── PORTADA ─────────────────────────────────────────────────────────
    portada(pdf,
            "Reporte Visual General",
            "Relevamiento Cuidado de Mascotas")

    # ── INFORME DE LIMPIEZA (markdown) ─────────────────────────────────
    renderizar_informe_md(pdf, INFORME_MD)

    # ── 1. CIUDAD ───────────────────────────────────────────────────────
    conteo_ciudad = df["Ciudad"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("1. Ciudad", fontsize=14, fontweight="bold")
    conteo_ciudad.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad")
    axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_ciudad)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    data = [[c, cnt, f"{cnt/N*100:.1f}%"] for c, cnt in conteo_ciudad.items()]
    tabla_pagina(pdf, data, ["Ciudad", "Cantidad", "%"], "Tabla — Ciudad")

    # ── 2. BARRIO TOP 20 ───────────────────────────────────────────────
    conteo_barrio = df["Barrio"].value_counts()
    top20 = conteo_barrio.head(20)

    fig, ax = plt.subplots(figsize=(11, 7))
    top20.plot(kind="barh", ax=ax, color=sns.color_palette("Set2", 20), edgecolor="white")
    ax.set_xlabel("Cantidad de respuestas")
    ax.set_title("2. Top 20 Barrios", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    data = [[b, cnt] for b, cnt in top20.items()]
    tabla_pagina(pdf, data, ["Barrio", "Cantidad"], "Tabla — Top 20 Barrios")

    # ── 3. TIPO DE VIVIENDA ─────────────────────────────────────────────
    conteo_viv = df["Tipo_Vivienda"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("3. Tipo de Vivienda", fontsize=14, fontweight="bold")
    conteo_viv.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=20, labelsize=8)
    pie_limpio(axes[1], conteo_viv)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 4. INTEGRANTES DE LA FAMILIA ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5))
    df["Integrantes_Familia"].dropna().value_counts().sort_index().plot(
        kind="bar", ax=ax, color=sns.color_palette("Set2")[1], edgecolor="white")
    ax.set_title("4. Integrantes por Familia", fontsize=14, fontweight="bold")
    ax.set_xlabel("Cantidad de integrantes"); ax.set_ylabel("Frecuencia")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 5. TIPO DE MASCOTAS (original + one-hot) ───────────────────────
    conteo_tipo = df["Tipo_Mascotas"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("5. Tipo de Mascotas (combinaciones originales)", fontsize=14, fontweight="bold")
    conteo_tipo.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_tipo)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ONE-HOT: Mascota_Gatos, Mascota_Perros
    COLS_OH_MASCOTA = [c for c in df.columns if c.startswith("Mascota_") and c not in ["Mascota_Castrada"]]
    labels_m = [c.replace("Mascota_", "") for c in COLS_OH_MASCOTA]
    vals_m = [df[c].sum() for c in COLS_OH_MASCOTA]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels_m, vals_m, color=sns.color_palette("Set2", len(labels_m)), edgecolor="white")
    ax.set_title("7b. Tipo de Mascota — Columnas individuales (one-hot)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Hogares que poseen")
    for i, v in enumerate(vals_m):
        ax.text(i, v + 3, str(v), ha="center", fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 6. CANTIDAD MASCOTAS POR SEXO ───────────────────────────────────
    COLS_ANI = ["Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    colores = sns.color_palette("Set2", 4)
    for i, col in enumerate(COLS_ANI):
        ax = axes[i // 2][i % 2]
        df[col].dropna().value_counts().sort_index().plot(
            kind="bar", ax=ax, color=colores[i], edgecolor="white")
        ax.set_title(col.replace("_", " ")); ax.set_xlabel("Cantidad"); ax.set_ylabel("Frecuencia")
    plt.suptitle("6. Cantidad de Mascotas por Tipo y Sexo", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    pdf.savefig(fig); plt.close()

    data = []
    for col in COLS_ANI:
        s = df[col]
        data.append([col, s.notna().sum(), s.isna().sum(),
                      f"{s.mean():.2f}", f"{int(s.max()) if pd.notna(s.max()) else '-'}"])
    tabla_pagina(pdf, data, ["Columna", "Respondieron", "Nulos", "Media", "Máx"],
                 "Tabla — Cantidad de Mascotas")

    # ── 7. MASCOTA CASTRADA ─────────────────────────────────────────────
    conteo_cast = df["Mascota_Castrada"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("7. ¿Mascota Castrada?", fontsize=14, fontweight="bold")
    conteo_cast.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_cast)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 8. DÓNDE CASTRACIÓN (original + one-hot) ───────────────────────
    conteo_donde = df["Donde_Castracion"].value_counts()

    fig, ax = plt.subplots(figsize=(11, 5))
    conteo_donde.plot(kind="barh", ax=ax, color=sns.color_palette("Set2", len(conteo_donde)),
                      edgecolor="white")
    ax.set_xlabel("Cantidad")
    ax.set_title("8. Lugar de Castración (combinaciones)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    COLS_OH_CAST = [c for c in df.columns if c.startswith("CastEn_")]
    labels_ce = [c.replace("CastEn_", "").replace("_", " ") for c in COLS_OH_CAST]
    vals_ce = [df[c].sum() for c in COLS_OH_CAST]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.barh(labels_ce, vals_ce, color=sns.color_palette("Set2", len(labels_ce)), edgecolor="white")
    ax.set_title("10b. Lugar de Castración — Columnas individuales (one-hot)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Hogares")
    for bar, v in zip(bars, vals_ce):
        ax.text(v + 2, bar.get_y() + bar.get_height()/2, str(v), va="center", fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 9. SABE CASTRACIÓN GRATUITA ──────────────────────────────────────
    conteo_sabe = df["Sabe_Castracion_Gratuita"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("9. ¿Sabe sobre Castración Gratuita?", fontsize=14, fontweight="bold")
    conteo_sabe.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_sabe)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 10. VACUNADAS ───────────────────────────────────────────────────
    conteo_vac = df["Vacunadas"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("10. ¿Mascotas Vacunadas?", fontsize=14, fontweight="bold")
    conteo_vac.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_vac)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 11. DESPARASITADAS ──────────────────────────────────────────────
    conteo_desp = df["Desparasitadas"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("11. ¿Mascotas Desparasitadas?", fontsize=14, fontweight="bold")
    conteo_desp.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_desp)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 12. SABE VACUNAS ANUALES ────────────────────────────────────────
    conteo_sv = df["Sabe_Vacunas_Anuales"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("12. ¿Sabe sobre Vacunas Anuales?", fontsize=14, fontweight="bold")
    conteo_sv.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_sv)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 13. CÓMO VIVEN (original + one-hot) ─────────────────────────────
    conteo_viven = df["Como_Viven_Mascotas"].value_counts()

    fig, ax = plt.subplots(figsize=(11, 5))
    conteo_viven.plot(kind="barh", ax=ax, color=sns.color_palette("Set2", len(conteo_viven)),
                      edgecolor="white")
    ax.set_xlabel("Cantidad")
    ax.set_title("13. Cómo viven las mascotas (combinaciones)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    COLS_OH_VIVE = [c for c in df.columns if c.startswith("Vive_")]
    labels_v = [c.replace("Vive_", "").replace("_", " ") for c in COLS_OH_VIVE]
    vals_v = [df[c].sum() for c in COLS_OH_VIVE]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.barh(labels_v, vals_v, color=sns.color_palette("Set2", len(labels_v)), edgecolor="white")
    ax.set_title("15b. Cómo viven — Columnas individuales (one-hot)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Hogares")
    for bar, v in zip(bars, vals_v):
        ax.text(v + 2, bar.get_y() + bar.get_height()/2, str(v), va="center", fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 14. FRECUENCIA CALLEJEROS ───────────────────────────────────────
    conteo_frec = df["Frecuencia_Callejeros"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("14. Frecuencia de Animales Callejeros", fontsize=14, fontweight="bold")
    conteo_frec.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_frec)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 15. ANIMAL PERDIDO ──────────────────────────────────────────────
    conteo_perd = df["Animal_Perdido_Frecuente"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("15. Animal Perdido con más Frecuencia", fontsize=14, fontweight="bold")
    conteo_perd.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_perd)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 16. MUNICIPIO PRESENTE (original + one-hot) ─────────────────────
    conteo_mun = df["Municipio_Presente"].value_counts()

    fig, ax = plt.subplots(figsize=(11, 6))
    y_labels = [textwrap.fill(str(v), 40) for v in conteo_mun.index]
    ax.barh(y_labels, np.asarray(conteo_mun.values),
            color=sns.color_palette("Set2", len(conteo_mun)), edgecolor="white")
    ax.set_xlabel("Cantidad")
    ax.set_title("16. Participación del Municipio (combinaciones)",
                 fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    COLS_OH_MUN = [c for c in df.columns if c.startswith("Mun_")]
    labels_mu = [c.replace("Mun_", "").replace("_", " ") for c in COLS_OH_MUN]
    vals_mu = [df[c].sum() for c in COLS_OH_MUN]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.barh([textwrap.fill(l, 35) for l in labels_mu], vals_mu,
                   color=sns.color_palette("Set2", len(labels_mu)), edgecolor="white")
    ax.set_title("18b. Participación del Municipio — Columnas individuales (one-hot)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Hogares que seleccionaron la opción")
    for bar, v in zip(bars, vals_mu):
        ax.text(v + 2, bar.get_y() + bar.get_height()/2, str(v), va="center", fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 17. HUMANO RESPONSABLE ──────────────────────────────────────────
    conteo_hr = df["Humano_Responsable"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("17. ¿Se considera Humano Responsable?", fontsize=14, fontweight="bold")
    conteo_hr.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2"), edgecolor="white")
    axes[0].set_ylabel("Cantidad"); axes[0].tick_params(axis="x", rotation=0)
    pie_limpio(axes[1], conteo_hr)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    pdf.savefig(fig); plt.close()

    # ── 18. PANEL RESUMEN Sí/No ─────────────────────────────────────────
    COLS_SINO = ["Mascota_Castrada", "Sabe_Castracion_Gratuita", "Vacunadas",
                 "Desparasitadas", "Sabe_Vacunas_Anuales"]
    labels_sino = ["Castrada", "Sabe Cast.\nGratuita", "Vacunadas", "Desparasit.", "Sabe Vac.\nAnuales"]

    fig, ax = plt.subplots(figsize=(11, 6))
    si_vals = [(df[c] == "Si").sum() for c in COLS_SINO]
    no_vals = [(df[c] == "No").sum() for c in COLS_SINO]
    x = range(len(COLS_SINO))
    bars1 = ax.bar(x, si_vals, label="Sí", color=sns.color_palette("Set2")[0], edgecolor="white")
    bars2 = ax.bar(x, no_vals, bottom=si_vals, label="No", color=sns.color_palette("Set2")[1], edgecolor="white")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels_sino, fontsize=9)
    ax.set_ylabel("Cantidad")
    ax.set_title("18. Panel Resumen — Preguntas Sí/No", fontsize=14, fontweight="bold")
    ax.legend()
    for bar, val in zip(bars1, si_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, str(val),
                ha="center", va="center", fontweight="bold", fontsize=10)
    for bar, base, val in zip(bars2, si_vals, no_vals):
        ax.text(bar.get_x() + bar.get_width()/2, base + val/2, str(val),
                ha="center", va="center", fontweight="bold", fontsize=10)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    data = []
    for c, lbl in zip(COLS_SINO, ["Castrada", "Sabe Cast. Gratuita", "Vacunadas", "Desparasitadas", "Sabe Vac. Anuales"]):
        si = (df[c] == "Si").sum()
        no = (df[c] == "No").sum()
        data.append([lbl, si, no, f"{si/N*100:.1f}%"])
    tabla_pagina(pdf, data, ["Pregunta", "Sí", "No", "% Sí"], "Tabla — Resumen Sí/No")

    # ── 19. RESUMEN ONE-HOT: TODAS LAS MULTI-RESPUESTA ──────────────────
    pagina_titulo(pdf, "Resumen — Columnas One-Hot\n(Multi-Respuesta Desagregada)")

    all_oh = {}
    for prefix, label in [("Mascota_", "Tipo Mascota"), ("Vive_", "Cómo Viven"),
                           ("CastEn_", "Dónde Castración"), ("Mun_", "Municipio Presente")]:
        cols = [c for c in df.columns if c.startswith(prefix) and c not in ["Mascota_Castrada"]]
        if cols:
            all_oh[label] = cols

    data = []
    for grupo, cols in all_oh.items():
        for c in cols:
            nombre_limpio = c.split("_", 1)[1].replace("_", " ") if "_" in c else c
            data.append([grupo, nombre_limpio, df[c].sum(), f"{df[c].mean()*100:.1f}%"])
    tabla_pagina(pdf, data, ["Grupo", "Categoría", "Cantidad (=1)", "% del total"],
                 "Tabla — Todas las columnas one-hot",
                 col_widths=[0.20, 0.45, 0.15, 0.15])

print(f"\n✅ PDF generado: {_pdf_path_out}")
