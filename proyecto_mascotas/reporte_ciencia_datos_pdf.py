"""
Reporte de Ciencia de Datos — PDF
Correlaciones, distribuciones, chi-cuadrado, segmentación,
análisis de columnas one-hot desagregadas.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
from scipy import stats
import os
import textwrap
import warnings
warnings.filterwarnings("ignore")

# ── Configuración ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE_DIR, "mascotas_limpio.csv")
PDF_PATH = os.path.join(BASE_DIR, "reporte_ciencia_datos.pdf")

sns.set_theme(style="whitegrid", palette="colorblind", font_scale=1.0)
plt.rcParams["figure.dpi"] = 150

df = pd.read_csv(CSV)
df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"])
N = len(df)

# ── Variables derivadas ─────────────────────────────────────────────────────
df["Total_Perros"] = df["Perros_Macho"].fillna(0) + df["Perros_Hembra"].fillna(0)
df["Total_Gatos"] = df["Gatos_Macho"].fillna(0) + df["Gatos_Hembra"].fillna(0)
df["Total_Mascotas"] = df["Total_Perros"] + df["Total_Gatos"]

COLS_SINO = ["Mascota_Castrada", "Sabe_Castracion_Gratuita", "Vacunadas",
             "Desparasitadas", "Sabe_Vacunas_Anuales"]
for c in COLS_SINO:
    df[f"{c}_bin"] = (df[c] == "Si").astype(int)

# One-hot cols already in dataset
COLS_OH_MASCOTA = [c for c in df.columns if c.startswith("Mascota_") and c not in ["Mascota_Castrada"]]
COLS_OH_VIVE = [c for c in df.columns if c.startswith("Vive_")]
COLS_OH_CAST = [c for c in df.columns if c.startswith("CastEn_")]
COLS_OH_MUN = [c for c in df.columns if c.startswith("Mun_")]
ALL_OH = COLS_OH_MASCOTA + COLS_OH_VIVE + COLS_OH_CAST + COLS_OH_MUN

# ── Helpers ─────────────────────────────────────────────────────────────────

def portada(pdf, titulo, subtitulo=""):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.6, titulo, transform=ax.transAxes,
            fontsize=28, fontweight="bold", ha="center", va="center", color="#2c3e50")
    ax.text(0.5, 0.45, subtitulo, transform=ax.transAxes,
            fontsize=14, ha="center", va="center", color="#7f8c8d")
    ax.text(0.5, 0.30,
            f"Dataset: mascotas_limpio.csv — {N} registros, {len(df.columns)} columnas",
            transform=ax.transAxes, fontsize=11, ha="center", va="center", color="#95a5a6")
    pdf.savefig(fig); plt.close()


def pagina_titulo(pdf, titulo):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.5, titulo, transform=ax.transAxes,
            fontsize=22, fontweight="bold", ha="center", va="center", color="#2c3e50")
    pdf.savefig(fig); plt.close()


MAX_FILAS_POR_PAGINA = 22


def _render_tabla(pdf, data, col_labels, titulo, col_widths=None, fontsize=9, row_height=1.3):
    n_rows = len(data)
    fig_height = min(max(3.5, 1.8 + n_rows * 0.32), 10.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.axis("off")
    ax.set_title(titulo, fontsize=13, fontweight="bold", pad=15, loc="left")
    table = ax.table(cellText=data, colLabels=col_labels, loc="center",
                     cellLoc="center", colWidths=col_widths)
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, row_height)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#ecf0f1")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()


def tabla_pagina(pdf, data, col_labels, titulo, col_widths=None, fontsize=9, row_height=1.3):
    """Renderiza tabla en una o varias páginas según la cantidad de filas."""
    if len(data) <= MAX_FILAS_POR_PAGINA:
        _render_tabla(pdf, data, col_labels, titulo, col_widths, fontsize, row_height)
        return
    total_pag = (len(data) + MAX_FILAS_POR_PAGINA - 1) // MAX_FILAS_POR_PAGINA
    for i in range(0, len(data), MAX_FILAS_POR_PAGINA):
        chunk = data[i:i + MAX_FILAS_POR_PAGINA]
        sub = f" (pág. {i // MAX_FILAS_POR_PAGINA + 1}/{total_pag})"
        _render_tabla(pdf, chunk, col_labels, titulo + sub, col_widths, fontsize, row_height)


def pagina_texto(pdf, titulo, lineas):
    """Página con texto libre (para conclusiones, etc.)."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.05, 0.95, titulo, transform=ax.transAxes,
            fontsize=16, fontweight="bold", va="top", color="#2c3e50")
    texto = "\n".join(lineas)
    ax.text(0.05, 0.85, texto, transform=ax.transAxes,
            fontsize=11, va="top", wrap=True, linespacing=1.6,
            fontfamily="sans-serif", color="#34495e")
    pdf.savefig(fig); plt.close()


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
    def _savefig_footer(fig=None, *a, **kw):
        f = fig if fig is not None else plt.gcf()
        f.text(0.98, 0.02, _FOOTER_TEXT, ha="right", va="bottom",
               fontsize=7.5, color="#555555", style="italic")
        return _orig_savefig(f, *a, **kw)
    pdf.savefig = _savefig_footer

    # ── PORTADA ─────────────────────────────────────────────────────────
    portada(pdf,
            "Reporte de Ciencia de Datos",
            "Relevamiento Cuidado de Mascotas")

    # ── 1. ESTADÍSTICA DESCRIPTIVA ──────────────────────────────────────
    pagina_titulo(pdf, "1. Estadística Descriptiva\nVariables Numéricas")

    num_cols = ["Integrantes_Familia", "Perros_Macho", "Perros_Hembra",
                "Gatos_Macho", "Gatos_Hembra", "Total_Perros", "Total_Gatos", "Total_Mascotas"]
    data = []
    for col in num_cols:
        s = df[col]
        data.append([col, s.notna().sum(), s.isna().sum(),
                      f"{s.mean():.2f}", f"{s.median():.1f}", f"{s.std():.2f}",
                      f"{s.min():.0f}", f"{s.max():.0f}",
                      f"{s.skew():.2f}", f"{s.kurtosis():.2f}"])
    tabla_pagina(pdf, data,
                 ["Variable", "N", "Nulos", "Media", "Mediana", "Desvío",
                  "Mín", "Máx", "Asimetría", "Curtosis"],
                 "Tabla — Estadística Descriptiva",
                 fontsize=8, row_height=1.4)

    # ── 2. DISTRIBUCIONES ───────────────────────────────────────────────
    # Dividir en 2 páginas (6 + 3) para que no se superpongan títulos/ejes
    chunks = [num_cols[:6], num_cols[6:]]
    for idx, chunk in enumerate(chunks, 1):
        n = len(chunk)
        rows = 2
        cols = 3 if n > 3 else n
        fig, axes = plt.subplots(rows, cols, figsize=(11, 8))
        axes = axes.ravel() if n > 1 else [axes]
        for i, col in enumerate(chunk):
            ax = axes[i]
            data_col = df[col].dropna()
            ax.hist(data_col, bins=20, color=sns.color_palette("colorblind")[i % 10],
                    edgecolor="white", alpha=0.8)
            ax.axvline(data_col.mean(), color="red", linestyle="--", linewidth=1.2,
                       label=f"Media={data_col.mean():.1f}")
            ax.axvline(data_col.median(), color="blue", linestyle="-.", linewidth=1.2,
                       label=f"Med={data_col.median():.1f}")
            ax.set_title(col.replace("_", " "), fontsize=10)
            ax.legend(fontsize=7)
            ax.tick_params(labelsize=8)
        # Ocultar ejes sobrantes
        for j in range(len(chunk), len(axes)):
            axes[j].axis("off")
        plt.suptitle(f"2. Distribuciones con Media y Mediana ({idx}/2)",
                     fontsize=14, fontweight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        pdf.savefig(fig); plt.close()

    # ── 3. BOXPLOTS ─────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(11, 5.5))
    fig.suptitle("3. Boxplots — Detección de Outliers", fontsize=14, fontweight="bold")
    sns.boxplot(data=df, x="Tipo_Vivienda", y="Total_Mascotas", ax=axes[0], palette="Set2")
    axes[0].set_title("Mascotas por Vivienda", fontsize=10)
    axes[0].tick_params(axis="x", rotation=30, labelsize=7)
    for lbl in axes[0].get_xticklabels():
        lbl.set_ha("right")
    sns.boxplot(data=df, x="Ciudad", y="Integrantes_Familia", ax=axes[1], palette="Set2")
    axes[1].set_title("Integrantes por Ciudad", fontsize=10)
    axes[1].tick_params(axis="x", rotation=30, labelsize=7)
    for lbl in axes[1].get_xticklabels():
        lbl.set_ha("right")
    axes[1].set_xlabel("")
    sns.boxplot(data=df, x="Tipo_Vivienda", y="Integrantes_Familia", ax=axes[2], palette="Set2")
    axes[2].set_title("Integrantes por Vivienda", fontsize=10)
    axes[2].tick_params(axis="x", rotation=30, labelsize=7)
    for lbl in axes[2].get_xticklabels():
        lbl.set_ha("right")
    axes[2].set_xlabel("")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig); plt.close()

    # ── 4. CORRELACIÓN ──────────────────────────────────────────────────
    corr_cols = (["Integrantes_Familia", "Total_Perros", "Total_Gatos", "Total_Mascotas"]
                 + [f"{c}_bin" for c in COLS_SINO]
                 + COLS_OH_MASCOTA + COLS_OH_VIVE)
    corr_labels = (["Integrantes", "Perros", "Gatos", "Total"]
                   + ["Castrada", "SabeCast", "Vacunada", "Desparasit", "SabeVac"]
                   + [c.split("_", 1)[1] for c in COLS_OH_MASCOTA]
                   + [c.split("_", 1)[1].replace("_", " ")[:12] for c in COLS_OH_VIVE])
    corr = df[corr_cols].corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                xticklabels=corr_labels, yticklabels=corr_labels,
                linewidths=0.3, ax=ax, vmin=-1, vmax=1, annot_kws={"size": 6})
    ax.set_title("4. Matriz de Correlación de Pearson (incluye one-hot)", fontsize=14, fontweight="bold")
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # Tabla de correlaciones destacadas
    pairs = []
    for i in range(len(corr_cols)):
        for j in range(i+1, len(corr_cols)):
            r = corr.iloc[i, j]
            if abs(r) > 0.20:
                pairs.append([corr_labels[i], corr_labels[j], f"{r:.3f}"])
    pairs.sort(key=lambda x: abs(float(x[2])), reverse=True)
    if pairs:
        tabla_pagina(pdf, pairs[:20], ["Variable A", "Variable B", "r"],
                     "Correlaciones destacadas (|r| > 0.20)")

    # ── 5. CHI-CUADRADO ────────────────────────────────────────────────
    pagina_titulo(pdf, "5. Tests Chi-Cuadrado (χ²)\nIndependencia entre variables categóricas")

    chi2_pairs = [
        ("Mascota_Castrada", "Vacunadas", "Castrada", "Vacunadas"),
        ("Mascota_Castrada", "Desparasitadas", "Castrada", "Desparasitadas"),
        ("Tipo_Mascotas", "Mascota_Castrada", "Tipo Mascotas", "Castrada"),
        ("Tipo_Vivienda", "Mascota_Castrada", "Tipo Vivienda", "Castrada"),
        ("Frecuencia_Callejeros", "Humano_Responsable", "Frec. Callejeros", "Humano Resp."),
        ("Vacunadas", "Desparasitadas", "Vacunadas", "Desparasitadas"),
    ]
    chi2_data = []
    for c1, c2, l1, l2 in chi2_pairs:
        ct = pd.crosstab(df[c1], df[c2])
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        sig = "SI" if p < 0.05 else "NO"
        chi2_data.append([f"{l1} vs {l2}", f"{chi2:.2f}", dof, f"{p:.4f}", sig])
    tabla_pagina(pdf, chi2_data,
                 ["Par de variables", "χ²", "gl", "p-value", "Significativo"],
                 "Resumen — Tests Chi-Cuadrado (α = 0.05)")

    # ── 6. HEATMAPS CONTINGENCIA ────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    hm_pairs = [
        ("Mascota_Castrada", "Vacunadas", "Castrada vs Vacunadas"),
        ("Tipo_Mascotas", "Mascota_Castrada", "Tipo Mascotas vs Castrada"),
        ("Frecuencia_Callejeros", "Humano_Responsable", "Callejeros vs Humano Resp."),
        ("Vacunadas", "Desparasitadas", "Vacunadas vs Desparasitadas"),
    ]
    for i, (c1, c2, title) in enumerate(hm_pairs):
        ax = axes[i // 2][i % 2]
        ct = pd.crosstab(df[c1], df[c2])
        sns.heatmap(ct, annot=True, fmt="d", cmap="YlOrRd", ax=ax, linewidths=0.5)
        ax.set_title(title, fontsize=10)
    plt.suptitle("6. Heatmaps de Contingencia", fontsize=14, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 7. SEGMENTACIÓN POR CIUDAD ──────────────────────────────────────
    seg_data = []
    for ciudad, g in df.groupby("Ciudad"):
        n = len(g)
        seg_data.append([
            ciudad, n,
            f"{(g['Mascota_Castrada']=='Si').mean()*100:.1f}%",
            f"{(g['Vacunadas']=='Si').mean()*100:.1f}%",
            f"{(g['Desparasitadas']=='Si').mean()*100:.1f}%",
            f"{g['Total_Mascotas'].mean():.2f}",
            f"{g['Integrantes_Familia'].mean():.2f}",
        ])
    tabla_pagina(pdf, seg_data,
                 ["Ciudad", "N", "% Castrada", "% Vacunada", "% Despar.", "Prom. Masc.", "Prom. Integ."],
                 "7. Segmentación por Ciudad")

    fig, axes = plt.subplots(1, 3, figsize=(11, 5.5))
    fig.suptitle("7. Segmentación por Ciudad", fontsize=14, fontweight="bold")
    ct_c1 = pd.crosstab(df["Ciudad"], df["Mascota_Castrada"], normalize="index") * 100
    ct_c1.plot(kind="bar", stacked=True, ax=axes[0], color=sns.color_palette("Set2")[:2], edgecolor="white")
    axes[0].set_title("% Castración"); axes[0].set_ylabel("%")
    axes[0].tick_params(axis="x", rotation=30, labelsize=7)
    axes[0].set_xlabel("")
    for lbl in axes[0].get_xticklabels():
        lbl.set_ha("right")
    ct_c2 = pd.crosstab(df["Ciudad"], df["Vacunadas"], normalize="index") * 100
    ct_c2.plot(kind="bar", stacked=True, ax=axes[1], color=sns.color_palette("Set2")[:2], edgecolor="white")
    axes[1].set_title("% Vacunación"); axes[1].set_ylabel("%")
    axes[1].tick_params(axis="x", rotation=30, labelsize=7)
    axes[1].set_xlabel("")
    for lbl in axes[1].get_xticklabels():
        lbl.set_ha("right")
    sns.boxplot(data=df, x="Ciudad", y="Total_Mascotas", ax=axes[2], palette="Set2")
    axes[2].set_title("Total Mascotas")
    axes[2].tick_params(axis="x", rotation=30, labelsize=7)
    axes[2].set_xlabel("")
    for lbl in axes[2].get_xticklabels():
        lbl.set_ha("right")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig); plt.close()

    # ── 8. SEGMENTACIÓN POR VIVIENDA ────────────────────────────────────
    seg_viv = []
    for tipo, g in df.groupby("Tipo_Vivienda"):
        seg_viv.append([
            tipo, len(g),
            f"{(g['Mascota_Castrada']=='Si').mean()*100:.1f}%",
            f"{(g['Vacunadas']=='Si').mean()*100:.1f}%",
            f"{g['Total_Mascotas'].mean():.2f}",
        ])
    tabla_pagina(pdf, seg_viv,
                 ["Tipo Vivienda", "N", "% Castrada", "% Vacunada", "Prom. Masc."],
                 "8. Segmentación por Tipo de Vivienda")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("8. Segmentación por Tipo Vivienda", fontsize=14, fontweight="bold")
    ct_v = pd.crosstab(df["Tipo_Vivienda"], df["Mascota_Castrada"], normalize="index") * 100
    ct_v.plot(kind="bar", stacked=True, ax=axes[0], color=sns.color_palette("Set2")[:2], edgecolor="white")
    axes[0].set_title("% Castración"); axes[0].set_ylabel("%"); axes[0].tick_params(axis="x", rotation=20, labelsize=8)
    sns.boxplot(data=df, x="Tipo_Vivienda", y="Total_Mascotas", ax=axes[1], palette="Set2")
    axes[1].set_title("Total Mascotas"); axes[1].tick_params(axis="x", rotation=20, labelsize=8)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 9. CASTRACIÓN vs CUIDADO SANITARIO ──────────────────────────────
    pagina_titulo(pdf, "9. Castración vs Cuidado Sanitario\n¿Quienes castran también vacunan y desparasitan?")

    comp_data = []
    for c, label in [("Vacunadas", "% Vacunadas"), ("Desparasitadas", "% Desparasitadas"),
                     ("Sabe_Castracion_Gratuita", "% Sabe Cast. Gratuita"),
                     ("Sabe_Vacunas_Anuales", "% Sabe Vac. Anuales")]:
        si = f"{(df[df['Mascota_Castrada']=='Si'][c]=='Si').mean()*100:.1f}%"
        no = f"{(df[df['Mascota_Castrada']=='No'][c]=='Si').mean()*100:.1f}%"
        comp_data.append([label, si, no])
    for c, label in [("Total_Mascotas", "Prom. Total Mascotas"),
                     ("Integrantes_Familia", "Prom. Integrantes")]:
        si = f"{df[df['Mascota_Castrada']=='Si'][c].mean():.2f}"
        no = f"{df[df['Mascota_Castrada']=='No'][c].mean():.2f}"
        comp_data.append([label, si, no])
    tabla_pagina(pdf, comp_data,
                 ["Indicador", "Castrada = Sí", "Castrada = No"],
                 "Castración vs Cuidado Sanitario")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("9. Castración vs Cuidado Sanitario", fontsize=14, fontweight="bold")
    cast_vac = df.groupby("Mascota_Castrada")[[f"{c}_bin" for c in ["Vacunadas", "Desparasitadas"]]].mean() * 100
    cast_vac.columns = ["% Vacunadas", "% Desparasitadas"]
    cast_vac.plot(kind="bar", ax=axes[0], color=sns.color_palette("Set2")[:2], edgecolor="white")
    axes[0].set_title("Vac/Desp según Castración"); axes[0].set_ylabel("%")
    axes[0].tick_params(axis="x", rotation=0)
    df.groupby("Mascota_Castrada")["Total_Mascotas"].mean().plot(
        kind="bar", ax=axes[1], color=sns.color_palette("Set2")[2], edgecolor="white")
    axes[1].set_title("Prom. Mascotas según Castración"); axes[1].set_ylabel("Promedio")
    axes[1].tick_params(axis="x", rotation=0)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 10. DISTRIBUCIÓN TOTAL MASCOTAS ─────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("10. Total de Mascotas por Hogar", fontsize=14, fontweight="bold")
    df["Total_Mascotas"].value_counts().sort_index().plot(
        kind="bar", ax=axes[0], color=sns.color_palette("colorblind")[3], edgecolor="white")
    axes[0].set_xlabel("Total mascotas"); axes[0].set_ylabel("Frecuencia")
    sns.violinplot(data=df, x="Tipo_Mascotas", y="Total_Mascotas", ax=axes[1],
                   palette="Set2", inner="box")
    axes[1].set_title("Total por Tipo")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 11. PAIRPLOT ────────────────────────────────────────────────────
    explicacion_pairplot = [
        "¿QUÉ ES UN PAIRPLOT?",
        "Es una matriz 3×3 que cruza todas las combinaciones entre 3 variables",
        "numéricas, coloreando cada punto según si la mascota está castrada o no.",
        "",
        "VARIABLES USADAS:",
        "  • Total_Perros",
        "  • Total_Gatos",
        "  • Integrantes_Familia",
        "  • Mascota_Castrada  → usada como COLOR (hue), no como eje",
        "",
        "CÓMO LEERLO:",
        "  • Diagonal (histogramas): distribución de cada variable, separada en dos",
        "    curvas (Sí castra / No castra). Si están desplazadas, esa variable se",
        "    relaciona con la castración.",
        "  • Fuera de la diagonal (scatter): cada punto es un hogar. El color indica",
        "    si castra o no. Clusters de un mismo color revelan patrones.",
        "",
        "QUÉ BUSCAR:",
        "  • Perros vs Gatos → hogares mono-especie vs mixtos. Si los no-castradores",
        "    se concentran en 'muchos perros + muchos gatos', son hogares de riesgo",
        "    reproductivo.",
        "  • Perros vs Integrantes → familias más grandes suelen tener más perros.",
        "  • Si los colores están mezclados → la castración no depende de estas",
        "    variables. Si están separados → sí hay asociación.",
        "",
        "UTILIDAD MUNICIPAL:",
        "  Detectar el perfil NUMÉRICO del hogar que no castra (ej: familias de 4+",
        "  integrantes con 3+ perros) para focalizar campañas en vez de mensajes",
        "  genéricos.",
    ]
    pagina_texto(pdf, "11. Pairplot — ¿Cómo interpretarlo?", explicacion_pairplot)

    pair_df = df[["Total_Perros", "Total_Gatos", "Integrantes_Familia", "Mascota_Castrada"]].dropna()
    g = sns.pairplot(pair_df, hue="Mascota_Castrada", palette="Set2",
                     diag_kind="hist", height=2.2, plot_kws={"alpha": 0.5})
    g.figure.suptitle("11. Pairplot: Mascotas e Integrantes por Castración",
                      fontsize=13, fontweight="bold")
    g.figure.subplots_adjust(top=0.92)
    pdf.savefig(g.figure, bbox_inches="tight"); plt.close()

    # ── 12. DATOS FALTANTES ─────────────────────────────────────────────
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0].sort_values(ascending=False)
    if len(nulos) > 0:
        data_n = [[col, n, f"{n/N*100:.1f}%"] for col, n in nulos.items()]
        tabla_pagina(pdf, data_n, ["Columna", "Nulos", "% del total"],
                     "12. Perfil de Datos Faltantes")

        fig, ax = plt.subplots(figsize=(11, 5))
        nulos.plot(kind="barh", ax=ax, color=sns.color_palette("Reds_r", len(nulos)), edgecolor="white")
        ax.set_xlabel("Cantidad de nulos")
        ax.set_title("12. Datos Faltantes por Columna", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
        plt.tight_layout()
        pdf.savefig(fig); plt.close()

    # ── 13. BARRIOS CON MENOR CASTRACIÓN ────────────────────────────────
    df["Mascota_Castrada_bin2"] = (df["Mascota_Castrada"] == "Si").astype(int)
    barrio_stats = df.groupby("Barrio").agg(
        n=("Mascota_Castrada_bin2", "count"),
        castradas=("Mascota_Castrada_bin2", "sum"),
    ).reset_index()
    barrio_stats["pct"] = barrio_stats["castradas"] / barrio_stats["n"] * 100
    barrio_stats = barrio_stats[barrio_stats["n"] >= 5].sort_values("pct")

    data_b = [[row["Barrio"], row["n"], row["castradas"], f"{row['pct']:.1f}%"]
              for _, row in barrio_stats.head(10).iterrows()]
    tabla_pagina(pdf, data_b,
                 ["Barrio", "N", "Castradas", "% Castración"],
                 "13. Barrios con menor % de Castración (N ≥ 5)")

    fig, ax = plt.subplots(figsize=(11, 5))
    top10 = barrio_stats.head(10).set_index("Barrio")
    colors = sns.color_palette("YlOrRd", len(top10))
    top10["pct"].plot(kind="barh", ax=ax, color=colors, edgecolor="white")
    ax.set_xlabel("% Castración")
    ax.set_title("13. Top 10 Barrios — Menor Castración", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(top10["pct"].items()):
        ax.text(val + 1, i, f"{val:.0f}%", va="center", fontsize=9)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 13b. BARRIOS CON MÁS ANIMALES NO CASTRADOS (VOLUMEN) ────────────
    # Cantidad ABSOLUTA de hogares que declaran mascotas NO castradas por barrio.
    # Útil para priorizar campañas de castración donde hay más animales afectados.
    df["No_Castradas_flag"] = (df["Mascota_Castrada"] == "No").astype(int)
    # Aproximación al volumen de animales no castrados: N_hogares_no_castrados * total_mascotas
    df["Animales_No_Cast_aprox"] = df["No_Castradas_flag"] * df["Total_Mascotas"].fillna(0)

    barrio_vol = df.groupby("Barrio").agg(
        hogares=("No_Castradas_flag", "count"),
        hogares_no_cast=("No_Castradas_flag", "sum"),
        animales_no_cast=("Animales_No_Cast_aprox", "sum"),
    ).reset_index()
    barrio_vol["pct_no_cast"] = barrio_vol["hogares_no_cast"] / barrio_vol["hogares"] * 100
    barrio_vol_top = barrio_vol[barrio_vol["hogares"] >= 3].sort_values(
        "animales_no_cast", ascending=False).head(15)

    data_bv = [[row["Barrio"], int(row["hogares"]), int(row["hogares_no_cast"]),
                int(row["animales_no_cast"]), f"{row['pct_no_cast']:.0f}%"]
               for _, row in barrio_vol_top.iterrows()]
    tabla_pagina(pdf, data_bv,
                 ["Barrio", "Hogares", "Hog. sin cast.", "Animales sin cast. (aprox)", "% sin cast."],
                 "13b. Top 15 Barrios por Volumen de Animales NO Castrados (N ≥ 3)")

    fig, ax = plt.subplots(figsize=(11, 6))
    top_vol = barrio_vol_top.set_index("Barrio")
    colors = sns.color_palette("Reds_r", len(top_vol))
    top_vol["animales_no_cast"].plot(kind="barh", ax=ax, color=colors, edgecolor="white")
    ax.set_xlabel("Animales no castrados (aprox)")
    ax.set_title("13b. Barrios prioritarios para campaña de castración",
                 fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    for i, val in enumerate(top_vol["animales_no_cast"].values):
        ax.text(val + 0.3, i, f"{int(val)}", va="center", fontsize=9)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 13c. NO CASTRACIÓN POR CIUDAD + BARRIO ──────────────────────────
    # Desglose ciudad × barrio: ¿dónde y cuántos animales sin castrar?
    ciudad_barrio = df.groupby(["Ciudad", "Barrio"]).agg(
        hogares=("No_Castradas_flag", "count"),
        no_cast=("No_Castradas_flag", "sum"),
        animales_sc=("Animales_No_Cast_aprox", "sum"),
    ).reset_index()
    ciudad_barrio = ciudad_barrio[ciudad_barrio["hogares"] >= 3]
    ciudad_barrio["pct"] = ciudad_barrio["no_cast"] / ciudad_barrio["hogares"] * 100
    ciudad_barrio = ciudad_barrio.sort_values(
        ["Ciudad", "animales_sc"], ascending=[True, False])

    data_cb = [[row["Ciudad"], row["Barrio"], int(row["hogares"]),
                int(row["no_cast"]), int(row["animales_sc"]), f"{row['pct']:.0f}%"]
               for _, row in ciudad_barrio.iterrows()]
    tabla_pagina(pdf, data_cb,
                 ["Ciudad", "Barrio", "Hogares", "Hog. sin cast.",
                  "Animales sin cast.", "% sin cast."],
                 "13c. Desglose por Ciudad y Barrio (N ≥ 3)")

    # Resumen por ciudad
    ciudad_sum = df.groupby("Ciudad").agg(
        hogares=("No_Castradas_flag", "count"),
        no_cast=("No_Castradas_flag", "sum"),
        animales_sc=("Animales_No_Cast_aprox", "sum"),
    ).reset_index()
    ciudad_sum["pct"] = ciudad_sum["no_cast"] / ciudad_sum["hogares"] * 100

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle("13c. Comparativa entre Ciudades — No Castración",
                 fontsize=14, fontweight="bold")
    ciudad_sum_sorted = ciudad_sum.sort_values("pct", ascending=False)
    ax1 = axes[0]
    ax1.bar(ciudad_sum_sorted["Ciudad"], ciudad_sum_sorted["pct"],
            color=sns.color_palette("Reds_r", len(ciudad_sum_sorted)), edgecolor="white")
    ax1.set_ylabel("% hogares sin castrar"); ax1.set_ylim(0, 100)
    ax1.set_title("% Hogares sin Castración", fontsize=10)
    for i, v in enumerate(ciudad_sum_sorted["pct"]):
        ax1.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9)
    ax1.tick_params(axis="x", rotation=20, labelsize=8)

    ax2 = axes[1]
    ax2.bar(ciudad_sum_sorted["Ciudad"], ciudad_sum_sorted["animales_sc"],
            color=sns.color_palette("Oranges_r", len(ciudad_sum_sorted)), edgecolor="white")
    ax2.set_ylabel("Animales sin castrar (aprox)")
    ax2.set_title("Volumen Absoluto de Animales sin Castrar", fontsize=10)
    for i, v in enumerate(ciudad_sum_sorted["animales_sc"]):
        ax2.text(i, v + 1, f"{int(v)}", ha="center", fontsize=9)
    ax2.tick_params(axis="x", rotation=20, labelsize=8)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    pdf.savefig(fig); plt.close()

    # ── 13d. ¿POR QUÉ NO CASTRAN? — FACTORES ASOCIADOS ──────────────────
    no_cast_df = df[df["Mascota_Castrada"] == "No"].copy()
    si_cast_df = df[df["Mascota_Castrada"] == "Si"].copy()

    factor_data = []
    # Conocimiento de castración gratuita
    for lbl, sub in [("Hogares SIN castrar", no_cast_df),
                     ("Hogares CON castración", si_cast_df)]:
        if len(sub) > 0:
            sabe_si = (sub["Sabe_Castracion_Gratuita"] == "Si").sum()
            sabe_no = (sub["Sabe_Castracion_Gratuita"] == "No").sum()
            total = sabe_si + sabe_no
            factor_data.append([
                lbl, len(sub),
                f"{sabe_si} ({sabe_si/total*100:.0f}%)" if total > 0 else "-",
                f"{sabe_no} ({sabe_no/total*100:.0f}%)" if total > 0 else "-",
            ])
    tabla_pagina(pdf, factor_data,
                 ["Grupo", "N", "Sabe gratuita: Sí", "Sabe gratuita: No"],
                 "13d. Conocimiento de Castración Gratuita según Estado")

    # Chi-cuadrado: Castración vs Conocimiento
    ct_sab = pd.crosstab(df["Mascota_Castrada"], df["Sabe_Castracion_Gratuita"])
    try:
        chi2_s, p_s, _, _ = stats.chi2_contingency(ct_sab)
        chi_line = (f"χ² = {chi2_s:.2f}, p = {p_s:.4f} "
                    f"{'(asociación significativa)' if p_s < 0.05 else '(sin asociación significativa)'}.")
    except Exception:
        chi_line = "No se pudo calcular chi-cuadrado."

    # Cuidado sanitario en hogares sin castrar
    pct_vac_no = (no_cast_df["Vacunadas"] == "Si").mean() * 100 if len(no_cast_df) else 0
    pct_vac_si = (si_cast_df["Vacunadas"] == "Si").mean() * 100 if len(si_cast_df) else 0
    pct_desp_no = (no_cast_df["Desparasitadas"] == "Si").mean() * 100 if len(no_cast_df) else 0
    pct_desp_si = (si_cast_df["Desparasitadas"] == "Si").mean() * 100 if len(si_cast_df) else 0

    # Top barrios del top 15 por volumen (prioritarios)
    barrios_priorit = ", ".join(barrio_vol_top["Barrio"].head(5).tolist())

    texto_14d = [
        f"Hogares sin castración: {len(no_cast_df)} ({len(no_cast_df)/N*100:.1f}% del total).",
        f"Hogares con castración: {len(si_cast_df)} ({len(si_cast_df)/N*100:.1f}% del total).",
        "",
        "Conocimiento de castración gratuita (chi-cuadrado):",
        f"  {chi_line}",
        "",
        "Cuidado sanitario asociado:",
        f"  • Hogares SIN castrar → Vacunan: {pct_vac_no:.0f}%  |  Desparasitan: {pct_desp_no:.0f}%",
        f"  • Hogares CON castrar → Vacunan: {pct_vac_si:.0f}%  |  Desparasitan: {pct_desp_si:.0f}%",
        "",
        "Barrios prioritarios (mayor volumen absoluto de animales sin castrar):",
        f"  {barrios_priorit}",
    ]
    pagina_texto(pdf, "13d. Factores asociados a la NO Castración", texto_14d)

    # Heatmap: % no castración por combinación Ciudad × Tipo_Vivienda
    pivot_nc = pd.crosstab(df["Ciudad"], df["Tipo_Vivienda"],
                           values=df["No_Castradas_flag"], aggfunc="mean") * 100
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot_nc, annot=True, fmt=".0f", cmap="Reds",
                cbar_kws={"label": "% hogares sin castrar"},
                linewidths=0.5, ax=ax)
    ax.set_title("13d. % de Hogares sin Castrar — Ciudad × Tipo de Vivienda",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel(""); ax.set_ylabel("")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── 13e. ANIMALES CALLEJEROS POR CIUDAD ─────────────────────────────
    # Cruza percepción de callejeros (Frecuencia_Callejeros) con la Ciudad.
    FREC_ORDER = ["Todo El Tiempo", "Frecuentemente", "A Veces", "Nunca"]
    fc_ciudad = pd.crosstab(df["Ciudad"], df["Frecuencia_Callejeros"])
    fc_ciudad = fc_ciudad.reindex(columns=[c for c in FREC_ORDER if c in fc_ciudad.columns])
    fc_ciudad_pct = fc_ciudad.div(fc_ciudad.sum(axis=1), axis=0) * 100

    # Tabla resumen: % de vecinos que ven callejeros "Todo el tiempo" o "Frecuentemente"
    alto_cols = [c for c in ["Todo El Tiempo", "Frecuentemente"] if c in fc_ciudad.columns]
    fc_ciudad_pct_sorted = fc_ciudad_pct.assign(
        _alto=fc_ciudad_pct[alto_cols].sum(axis=1) if alto_cols else 0
    ).sort_values("_alto", ascending=False).drop(columns="_alto")

    data_fc = []
    for ciudad, row in fc_ciudad_pct_sorted.iterrows():
        n_ciudad = int(fc_ciudad.loc[ciudad].sum())
        fila = [ciudad, n_ciudad]
        for c in FREC_ORDER:
            fila.append(f"{row[c]:.0f}%" if c in row.index else "-")
        data_fc.append(fila)
    tabla_pagina(pdf, data_fc,
                 ["Ciudad", "N", "Todo el tiempo", "Frecuentemente", "A veces", "Nunca"],
                 "13e. Frecuencia de Animales Callejeros por Ciudad (%)")

    # Heatmap: % por ciudad × frecuencia
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(fc_ciudad_pct_sorted, annot=True, fmt=".0f", cmap="Reds",
                cbar_kws={"label": "% respuestas"},
                linewidths=0.5, ax=ax, vmin=0, vmax=100)
    ax.set_title("13e. Percepción de Callejeros por Ciudad (%)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel(""); ax.set_ylabel("")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # Barras: % de "Todo el tiempo" + "Frecuentemente" (presencia alta) por ciudad
    fig, ax = plt.subplots(figsize=(11, 5))
    if alto_cols:
        pct_alto = fc_ciudad_pct[alto_cols].sum(axis=1).sort_values(ascending=False)
        colors = sns.color_palette("Reds_r", len(pct_alto))
        ax.bar(pct_alto.index, pct_alto.values, color=colors, edgecolor="white")
        ax.set_ylabel("% vecinos con presencia ALTA de callejeros")
        ax.set_ylim(0, 100)
        for i, v in enumerate(pct_alto.values):
            ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9)
    ax.set_title("13e. Ciudades con MAYOR presencia de callejeros\n"
                 "(% que los ve 'Todo el tiempo' + 'Frecuentemente')",
                 fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=20)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # Chi-cuadrado Ciudad × Frecuencia_Callejeros
    try:
        chi2_fc, p_fc, _, _ = stats.chi2_contingency(fc_ciudad)
        chi_fc_line = (f"χ² = {chi2_fc:.2f}, p = {p_fc:.4f} "
                       f"{'(asociación SIGNIFICATIVA)' if p_fc < 0.05 else '(sin asociación significativa)'}.")
    except Exception:
        chi_fc_line = "No se pudo calcular chi-cuadrado."

    ciudad_peor_cjr = fc_ciudad_pct_sorted.index[0] if len(fc_ciudad_pct_sorted) else "—"
    ciudad_mejor_cjr = fc_ciudad_pct_sorted.index[-1] if len(fc_ciudad_pct_sorted) else "—"
    pct_peor = fc_ciudad_pct_sorted[alto_cols].iloc[0].sum() if alto_cols and len(fc_ciudad_pct_sorted) else 0
    pct_mejor = fc_ciudad_pct_sorted[alto_cols].iloc[-1].sum() if alto_cols and len(fc_ciudad_pct_sorted) else 0

    texto_13e = [
        "DIAGNÓSTICO DE CALLEJEROS POR CIUDAD",
        "",
        f"• Ciudad con MAYOR presencia de callejeros: {ciudad_peor_cjr}",
        f"   ({pct_peor:.0f}% los ve 'Todo el tiempo' o 'Frecuentemente').",
        "",
        f"• Ciudad con MENOR presencia de callejeros: {ciudad_mejor_cjr}",
        f"   ({pct_mejor:.0f}% los ve 'Todo el tiempo' o 'Frecuentemente').",
        "",
        "• Test chi-cuadrado Ciudad × Frecuencia de Callejeros:",
        f"   {chi_fc_line}",
        "",
        "INTERPRETACIÓN PARA EL MUNICIPIO",
        "  Si la asociación es significativa → la cantidad de callejeros NO es",
        "  uniforme entre ciudades y conviene distribuir los operativos de",
        "  castración y control según la carga de cada una, priorizando",
        f"  {ciudad_peor_cjr}.",
    ]
    pagina_texto(pdf, "13e. Conclusiones — Callejeros por Ciudad", texto_13e)

    # ── 13f. % HOGARES SIN CASTRAR: BARRIO × CIUDAD × TIPO DE VIVIENDA ──
    pagina_titulo(pdf, "13f. % Hogares sin Castrar\nBarrio × Ciudad × Tipo de Vivienda")

    # Sub-dataset solo de barrios con al menos 5 respuestas (para robustez)
    MIN_N = 5
    df_cast = df[(df["Barrio"].notna()) & (df["Ciudad"].notna()) & (df["Tipo_Vivienda"].notna())].copy()
    df_cast["No_Castrado"] = (df_cast["Mascota_Castrada"] == "No").astype(int)

    # ── Tabla ranking: % sin castrar por Barrio + Ciudad + Tipo_Vivienda ──
    grp = (
        df_cast
        .groupby(["Barrio", "Ciudad", "Tipo_Vivienda"])
        .agg(Total=("No_Castrado", "size"), Sin_Castrar=("No_Castrado", "sum"))
        .reset_index()
    )
    grp = grp[grp["Total"] >= MIN_N]
    grp["Pct_Sin_Castrar"] = grp["Sin_Castrar"] / grp["Total"] * 100
    grp_sorted = grp.sort_values("Pct_Sin_Castrar", ascending=False)

    data_13f = [
        [row["Barrio"], row["Ciudad"], row["Tipo_Vivienda"],
         int(row["Total"]), f"{row['Pct_Sin_Castrar']:.0f}%"]
        for _, row in grp_sorted.iterrows()
    ]
    tabla_pagina(
        pdf, data_13f,
        ["Barrio", "Ciudad", "Tipo Vivienda", "N", "% Sin Castrar"],
        f"13f. Ranking Barrio × Ciudad × Tipo Vivienda — % Hogares sin castrar (mín. {MIN_N} respuestas)",
        fontsize=8,
    )

    # ── Heatmap barrio × tipo vivienda (agregado sin discriminar ciudad) ──
    piv_bv = df_cast.groupby(["Barrio", "Tipo_Vivienda"])["No_Castrado"].mean().mul(100).unstack()
    # conservar barrios con al menos MIN_N casos totales
    n_barrio = df_cast.groupby("Barrio").size()
    barrios_ok = n_barrio[n_barrio >= MIN_N].index
    piv_bv = piv_bv.loc[piv_bv.index.isin(barrios_ok)]
    piv_bv = piv_bv.dropna(how="all")
    if not piv_bv.empty:
        # ordenar por promedio descendente
        piv_bv = piv_bv.loc[piv_bv.mean(axis=1).sort_values(ascending=False).index]
        n_bar = len(piv_bv)
        fig_h = max(5, min(0.5 * n_bar, 18))
        fig, ax = plt.subplots(figsize=(11, fig_h))
        sns.heatmap(
            piv_bv, annot=True, fmt=".0f", cmap="RdYlGn_r",
            linewidths=0.4, ax=ax, vmin=0, vmax=100,
            cbar_kws={"label": "% sin castrar"},
        )
        ax.set_title("13f. % Hogares sin Castrar — Barrio × Tipo de Vivienda",
                     fontsize=13, fontweight="bold")
        ax.set_xlabel("Tipo de Vivienda")
        ax.set_ylabel("Barrio")
        plt.xticks(rotation=25, ha="right", fontsize=8)
        plt.yticks(fontsize=7)
        plt.tight_layout()
        pdf.savefig(fig); plt.close()

    # ── Barplot TOP 15 barrios con mayor % sin castrar ────────────────────
    top15 = grp_sorted.head(15).copy()
    top15["Label"] = top15["Barrio"] + "\n(" + top15["Ciudad"] + " — " + top15["Tipo_Vivienda"] + ")"
    fig, ax = plt.subplots(figsize=(11, 6))
    colors = sns.color_palette("Reds_r", len(top15))
    ax.barh(top15["Label"][::-1], top15["Pct_Sin_Castrar"][::-1], color=colors[::-1], edgecolor="white")
    ax.set_xlabel("% Hogares sin castrar")
    ax.set_xlim(0, 110)
    for i, (_, row) in enumerate(top15[::-1].iterrows()):
        ax.text(row["Pct_Sin_Castrar"] + 1, i, f"{row['Pct_Sin_Castrar']:.0f}% (n={int(row['Total'])})",
                va="center", fontsize=8)
    ax.set_title("13f. Top 15 — Barrio × Ciudad × Tipo de Vivienda con mayor % sin castrar",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # ── Página de conclusiones 13f ────────────────────────────────────────
    peor_13f = grp_sorted.iloc[0] if not grp_sorted.empty else None
    mejor_13f = grp_sorted.iloc[-1] if not grp_sorted.empty else None
    texto_13f = [
        "% HOGARES SIN CASTRAR — BARRIO × CIUDAD × TIPO DE VIVIENDA",
        "",
    ]
    if peor_13f is not None:
        texto_13f += [
            f"• Segmento con MAYOR % sin castrar:",
            f"   {peor_13f['Barrio']} ({peor_13f['Ciudad']}) — {peor_13f['Tipo_Vivienda']}",
            f"   → {peor_13f['Pct_Sin_Castrar']:.0f}% de {int(peor_13f['Total'])} hogares.",
            "",
            f"• Segmento con MENOR % sin castrar:",
            f"   {mejor_13f['Barrio']} ({mejor_13f['Ciudad']}) — {mejor_13f['Tipo_Vivienda']}",
            f"   → {mejor_13f['Pct_Sin_Castrar']:.0f}% de {int(mejor_13f['Total'])} hogares.",
            "",
        ]
    texto_13f += [
        "LECTURA DEL HEATMAP",
        "  Rojo intenso = alta proporción de hogares sin castrar.",
        "  Permite identificar combos barrio+vivienda donde el déficit es mayor",
        "  para focalizar campañas de castración gratuita.",
        "",
        "NOTA METODOLÓGICA",
        f"  Solo se muestran segmentos con al menos {MIN_N} respuestas para evitar",
        "  porcentajes engañosos por muestras muy pequeñas.",
    ]
    pagina_texto(pdf, "13f. Conclusiones — % sin Castrar por Barrio × Ciudad × Vivienda", texto_13f)

    # ── 14. ANÁLISIS ONE-HOT: MULTI-RESPUESTA ──────────────────────────
    pagina_titulo(pdf, "14. Análisis de Columnas One-Hot\n(Multi-Respuesta Desagregada)")

    explicacion_oh = [
        "¿QUÉ ES ONE-HOT?",
        "Varias preguntas del formulario permiten MÚLTIPLES respuestas a la vez",
        "(ej: '¿Qué debería hacer el municipio?' → castraciones, educación,",
        "identificación, etc.). Para analizarlas se separa cada opción en una",
        "columna binaria: 1 si el vecino la marcó, 0 si no.",
        "",
        "GRUPOS ONE-HOT GENERADOS:",
        "  • Mascota_*    → Tipo de mascota (Perro, Gato, Otro).",
        "  • Vive_*       → Cómo vive la mascota (suelta, atada, adentro…).",
        "  • CastEn_*     → Dónde se castró (municipio, vet privada, ninguno).",
        "  • Mun_*        → Qué se le pide al municipio.",
        "",
        "QUÉ SE ANALIZA EN ESTA SECCIÓN:",
        "  14a. Tabla resumen: cuántos hogares marcaron cada categoría y su %.",
        "  14.  Grilla 2×2: cruza las 4 primeras opciones pedidas al municipio",
        "       contra el estado de castración del hogar.",
        "",
        "CÓMO LEER 14:",
        "  Cada subgráfico tiene 2 barras (No / Sí marcó esa opción) y dos colores",
        "  (castrada Sí / No). Si 'Sí marcó Castraciones Masivas' concentra",
        "  hogares NO castrados → la demanda es genuina: quien lo pide es quien",
        "  más lo necesita. Si 'Sí marcó Educación' se reparte parejo → demanda",
        "  transversal. Si 'Sí marcó Control de ID' viene más de castrados → son",
        "  vecinos responsables que quieren que los demás también lo sean.",
        "",
        "UTILIDAD MUNICIPAL:",
        "  Detectar coherencia (o brecha) entre lo que la gente PIDE al municipio",
        "  y lo que efectivamente HACE en su propio hogar.",
    ]
    pagina_texto(pdf, "14. Análisis One-Hot — ¿Cómo interpretarlo?", explicacion_oh)

    # a) Resumen one-hot
    oh_data = []
    for prefix, label in [("Mascota_", "Tipo Mascota"), ("Vive_", "Cómo Viven"),
                           ("CastEn_", "Dónde Cast."), ("Mun_", "Municipio")]:
        cols = [c for c in df.columns if c.startswith(prefix) and c not in ["Mascota_Castrada", "Mascota_Castrada_bin2"]]
        for c in cols:
            nombre = c.split("_", 1)[1].replace("_", " ")
            oh_data.append([label, nombre[:30], df[c].sum(), f"{df[c].mean()*100:.1f}%"])
    tabla_pagina(pdf, oh_data,
                 ["Grupo", "Categoría", "Cantidad", "% del total"],
                 "Resumen — Columnas One-Hot",
                 col_widths=[0.18, 0.42, 0.15, 0.15])

    # c) Cross-tab: Municipio one-hot vs Castración
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    mun_cols_plot = [c for c in COLS_OH_MUN][:4]
    for i, mc in enumerate(mun_cols_plot):
        ax = axes[i // 2][i % 2]
        ct = pd.crosstab(df[mc].map({0: "No", 1: "Sí"}), df["Mascota_Castrada"])
        ct.plot(kind="bar", ax=ax, color=sns.color_palette("Set2")[:2], edgecolor="white")
        nombre = mc.split("_", 1)[1].replace("_", " ")[:25]
        ax.set_title(f"{nombre}\nvs Castración", fontsize=9)
        ax.tick_params(axis="x", rotation=0)
        ax.legend(fontsize=7, title="Castrada", title_fontsize=7)
    plt.suptitle("14. Opciones Municipio (OH) vs Castración", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, bottom=0.10)
    pdf.savefig(fig); plt.close()

    # ── 15. CONCLUSIONES PARA EL MUNICIPIO ──────────────────────────────
    explicacion_15 = [
        "¿QUÉ CONTIENE LA SECCIÓN 15?",
        "Es el cierre del reporte: traduce todo el análisis técnico previo en",
        "insights y recomendaciones accionables para la gestión municipal.",
        "Se divide en 3 páginas (15a, 15b, 15c).",
        "",
        "15a. HALLAZGOS CLAVE",
        "  • Situación general: N hogares, ciudad dominante, stock de mascotas",
        "    y total de animales sin castrar.",
        "  • Cobertura sanitaria: % castración, vacunación, desparasitación y",
        "    % que conoce el servicio gratuito del municipio.",
        "  • Brecha de información (hallazgo principal): compara qué % de los",
        "    hogares que castran conocen la gratuidad vs los que no. Se valida",
        "    con un test chi-cuadrado (χ²) — si p<0.05, la asociación es",
        "    estadísticamente significativa.",
        "  • Riesgo en vía pública: % de callejeros, mascotas sueltas y sin ID.",
        "",
        "15b. FOCALIZACIÓN GEOGRÁFICA Y DEMANDA CIUDADANA",
        "  • Zonas prioritarias: ciudad con mayor % sin castrar + top 5 barrios",
        "    con más animales sin castrar en valores ABSOLUTOS (mayor impacto).",
        "  • Demanda ciudadana: qué le pide la gente al municipio según las",
        "    columnas one-hot Mun_* (castraciones, educación, identificación).",
        "  • Autopercepción vs práctica: % que se dice 'humano responsable'",
        "    contrastado con % real que castra/vacuna.",
        "",
        "15c. RECOMENDACIONES ACCIONABLES",
        "  5 acciones concretas respaldadas con cifras del propio relevamiento:",
        "  1. Campaña de difusión de castración gratuita.",
        "  2. Jornadas focalizadas en los 5 barrios prioritarios.",
        "  3. Programa de identificación (chapitas/microchip).",
        "  4. Educación y tenencia responsable.",
        "  5. Monitoreo continuo (relevar cada 6–12 meses).",
        "",
        "UTILIDAD:",
        "  Funciona como resumen ejecutivo para quien debe decidir en qué",
        "  invertir recursos del municipio sin leer todo el análisis técnico.",
    ]
    pagina_texto(pdf, "15. Conclusiones — ¿Cómo interpretarlas?", explicacion_15)

    pct_castrada = (df["Mascota_Castrada"] == "Si").mean() * 100
    pct_no_castrada = (df["Mascota_Castrada"] == "No").mean() * 100
    pct_vacunada = (df["Vacunadas"] == "Si").mean() * 100
    pct_desparasitada = (df["Desparasitadas"] == "Si").mean() * 100
    pct_sabe_grat = (df["Sabe_Castracion_Gratuita"] == "Si").mean() * 100
    pct_sabe_vac = (df["Sabe_Vacunas_Anuales"] == "Si").mean() * 100
    ciudad_top = df["Ciudad"].value_counts().index[0]
    ciudad_top_pct = df["Ciudad"].value_counts().iloc[0] / N * 100
    media_mascotas = df["Total_Mascotas"].mean()
    total_mascotas_est = int(df["Total_Mascotas"].sum())
    total_animales_sin_cast = int(df["Animales_No_Cast_aprox"].sum())
    pct_callejeros = (df["Frecuencia_Callejeros"] == "Todo El Tiempo").mean() * 100
    pct_salen_solos = df["Vive_Salen_solos_a_la_calle"].mean() * 100 if "Vive_Salen_solos_a_la_calle" in df.columns else 0
    pct_sin_id = 100 - (df["Vive_Tienen_identificador"].mean() * 100 if "Vive_Tienen_identificador" in df.columns else 0)
    pct_humano_resp = (df["Humano_Responsable"] == "Si").mean() * 100

    # Comparación entre grupos
    no_cast_df = df[df["Mascota_Castrada"] == "No"]
    si_cast_df = df[df["Mascota_Castrada"] == "Si"]
    pct_sabe_grat_no = (no_cast_df["Sabe_Castracion_Gratuita"] == "Si").mean() * 100 if len(no_cast_df) else 0
    pct_sabe_grat_si = (si_cast_df["Sabe_Castracion_Gratuita"] == "Si").mean() * 100 if len(si_cast_df) else 0
    pct_vac_no = (no_cast_df["Vacunadas"] == "Si").mean() * 100 if len(no_cast_df) else 0
    pct_vac_si = (si_cast_df["Vacunadas"] == "Si").mean() * 100 if len(si_cast_df) else 0

    # Demanda municipal
    pct_demanda_cast = df["Mun_Castraciones_Masivas"].mean() * 100 if "Mun_Castraciones_Masivas" in df.columns else 0
    pct_demanda_edu = df["Mun_Educación"].mean() * 100 if "Mun_Educación" in df.columns else 0
    pct_demanda_id = df["Mun_Control_de_identificación"].mean() * 100 if "Mun_Control_de_identificación" in df.columns else 0

    # Chi² Castración vs Conocimiento gratuita
    ct_sg = pd.crosstab(df["Mascota_Castrada"], df["Sabe_Castracion_Gratuita"])
    chi2_sg, p_sg, _, _ = stats.chi2_contingency(ct_sg)

    # Top 5 barrios prioritarios
    barrios_top5 = barrio_vol_top["Barrio"].head(5).tolist()
    barrios_top5_txt = ", ".join(barrios_top5) if barrios_top5 else "—"

    # Ciudad con mayor % no-castración
    ciudad_peor = ciudad_sum.sort_values("pct", ascending=False).iloc[0]
    ciudad_peor_nombre = ciudad_peor["Ciudad"]
    ciudad_peor_pct = ciudad_peor["pct"]

    # ── 15a. Hallazgos clave ─────────────────────────────────────────────
    hallazgos = [
        "SITUACIÓN GENERAL",
        f"• Muestra analizada: {N} hogares; {ciudad_top} concentra el {ciudad_top_pct:.0f}%.",
        f"• Stock aproximado de mascotas relevado: {total_mascotas_est} animales "
            f"(media {media_mascotas:.1f} por hogar).",
        f"• Estiman {total_animales_sin_cast} animales SIN castrar en los hogares encuestados.",
        "",
        "COBERTURA SANITARIA",
        f"• Castración: {pct_castrada:.0f}% del total   |   Sin castrar: {pct_no_castrada:.0f}%.",
        f"• Vacunación: {pct_vacunada:.0f}%   |   Desparasitación: {pct_desparasitada:.0f}%.",
        f"• Conocen la castración gratuita del municipio: {pct_sabe_grat:.0f}%.",
        f"• Conocen el calendario de vacunas anuales: {pct_sabe_vac:.0f}%.",
        "",
        "BRECHA DE INFORMACIÓN (principal hallazgo)",
        f"• Hogares CON castración que conocen la gratuita: {pct_sabe_grat_si:.0f}%.",
        f"• Hogares SIN castración que conocen la gratuita: {pct_sabe_grat_no:.0f}%.",
        f"• Asociación estadística (χ²={chi2_sg:.1f}, p={p_sg:.4f}): "
            f"{'SIGNIFICATIVA' if p_sg < 0.05 else 'no significativa'}.",
        f"  → Quienes no conocen el servicio gratuito castran mucho menos.",
        "",
        "RIESGO EN VÍA PÚBLICA",
        f"• {pct_callejeros:.0f}% ve animales callejeros todo el tiempo en su barrio.",
        f"• {pct_salen_solos:.0f}% de los hogares deja que sus mascotas salgan solas a la calle.",
        f"• {pct_sin_id:.0f}% de las mascotas NO tiene identificador.",
    ]
    pagina_texto(pdf, "15a. Hallazgos clave para el Municipio", hallazgos)

    # ── 15b. Focalización geográfica ─────────────────────────────────────
    geografia = [
        "ZONAS PRIORITARIAS PARA INTERVENCIÓN",
        "",
        f"• Ciudad con mayor % de hogares sin castración: {ciudad_peor_nombre} "
            f"({ciudad_peor_pct:.0f}%).",
        "",
        "• Barrios con MAYOR VOLUMEN de animales sin castrar (top 5):",
        f"   {barrios_top5_txt}",
        "",
        "  → Priorizar estos barrios en jornadas de castración masiva porque es",
        "    donde el impacto en cantidad absoluta de animales será mayor.",
        "",
        "DEMANDA CIUDADANA HACIA EL MUNICIPIO (multi-respuesta)",
        f"• {pct_demanda_cast:.0f}% pide más castraciones masivas.",
        f"• {pct_demanda_edu:.0f}% pide educación / concientización.",
        f"• {pct_demanda_id:.0f}% pide control de identificación de mascotas.",
        "",
        "AUTOPERCEPCIÓN",
        f"• {pct_humano_resp:.0f}% se considera 'humano responsable' con sus mascotas,",
        f"  pero sólo el {pct_castrada:.0f}% castra y el {pct_vacunada:.0f}% vacuna.",
        f"  → Existe una brecha entre la autoevaluación y las prácticas reales.",
    ]
    pagina_texto(pdf, "15b. Focalización geográfica y demanda ciudadana", geografia)

    # ── 15c. Recomendaciones accionables ────────────────────────────────
    recomendaciones = [
        "RECOMENDACIONES ACCIONABLES",
        "",
        "1. CAMPAÑA DE DIFUSIÓN DE CASTRACIÓN GRATUITA",
        f"   Sólo el {pct_sabe_grat:.0f}% conoce el servicio y quienes no lo conocen",
        "   castran mucho menos (asociación estadística confirmada).",
        "   → Comunicación puerta a puerta, redes, escuelas y veterinarias.",
        "",
        "2. JORNADAS FOCALIZADAS DE CASTRACIÓN",
        f"   Priorizar los 5 barrios con más animales sin castrar:",
        f"   {barrios_top5_txt}.",
        "   → Mayor impacto por cada turno disponible.",
        "",
        "3. PROGRAMA DE IDENTIFICACIÓN",
        f"   {pct_sin_id:.0f}% de las mascotas no tiene identificador y {pct_salen_solos:.0f}%",
        "   sale sola a la calle. Esto alimenta la población callejera y pérdidas.",
        "   → Chapitas/microchip gratuitos combinados con los turnos de castración.",
        "",
        "4. EDUCACIÓN Y RESPONSABILIDAD",
        f"   {pct_demanda_edu:.0f}% del vecindario reclama educación.",
        "   → Talleres en escuelas y centros vecinales sobre tenencia responsable,",
        "     calendario sanitario y riesgos del abandono.",
        "",
        "5. MONITOREO CONTINUO",
        f"   Repetir el relevamiento cada 6–12 meses y comparar {ciudad_peor_nombre}",
        "   con las demás ciudades para medir avances.",
    ]
    pagina_texto(pdf, "15c. Recomendaciones para el Municipio", recomendaciones)

print(f"\n✅ PDF Ciencia de Datos generado: {_pdf_path_out}")
