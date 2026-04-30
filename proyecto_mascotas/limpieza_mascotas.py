"""
Script de limpieza del dataset "Relevamiento Cuidado de Mascotas"
Cada paso queda registrado en un informe Markdown (informe_limpieza.md)
y se genera el dataset limpio como CSV final.
"""

import pandas as pd
import os
from datetime import datetime

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ORIGINAL = os.path.join(BASE_DIR, "Relevamiento Cuidado de Mascotas Actualizado.csv")
CSV_LIMPIO = os.path.join(BASE_DIR, "mascotas_limpio.csv")
LOG_FILE = os.path.join(BASE_DIR, "informe_limpieza.md")

# ── Logger ──────────────────────────────────────────────────────────────────
md_lines: list[str] = []


def md(line: str = ""):
    """Agrega una línea al informe Markdown."""
    md_lines.append(line)
    try:
        print(line)
    except UnicodeEncodeError:
        # La consola de Windows (cp1252) no soporta algunos caracteres Unicode.
        # El informe Markdown sí los conserva intactos.
        print(line.encode("ascii", "replace").decode("ascii"))


def guardar_informe():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    msg = f"\nInforme guardado en: {LOG_FILE}"
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


# ── 1. Carga ────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_ORIGINAL, encoding="utf-8")
filas_orig, cols_orig = df.shape

md(f"# Informe de Limpieza — Relevamiento Cuidado de Mascotas")
md(f"**Fecha de ejecución:** {datetime.now():%Y-%m-%d %H:%M:%S}")
md()
md("---")
md()
md("## 1. Carga del dataset")
md(f"- **Archivo:** `{os.path.basename(CSV_ORIGINAL)}`")
md(f"- **Filas:** {filas_orig}")
md(f"- **Columnas:** {cols_orig}")

# ── 2. Renombrar columnas (nombres cortos y manejables) ────────────────────
NOMBRES_COLUMNAS = {
    df.columns[0]: "Marca_Temporal",
    df.columns[1]: "Ciudad",
    df.columns[2]: "Barrio",
    df.columns[3]: "Altura",
    df.columns[4]: "Tipo_Vivienda",
    df.columns[5]: "Integrantes_Familia",
    df.columns[6]: "Tipo_Mascotas",
    df.columns[7]: "Perros_Macho",
    df.columns[8]: "Perros_Hembra",
    df.columns[9]: "Gatos_Macho",
    df.columns[10]: "Gatos_Hembra",
    df.columns[11]: "Mascota_Castrada",
    df.columns[12]: "Donde_Castracion",
    df.columns[13]: "Sabe_Castracion_Gratuita",
    df.columns[14]: "Vacunadas",
    df.columns[15]: "Desparasitadas",
    df.columns[16]: "Sabe_Vacunas_Anuales",
    df.columns[17]: "Como_Viven_Mascotas",
    df.columns[18]: "Frecuencia_Callejeros",
    df.columns[19]: "Animal_Perdido_Frecuente",
    df.columns[20]: "Municipio_Presente",
    df.columns[21]: "Humano_Responsable",
}
df.rename(columns=NOMBRES_COLUMNAS, inplace=True)

# Descartamos la columna "Altura" (numeración de calle): no aporta valor al negocio.
df.drop(columns=["Altura"], inplace=True, errors="ignore")

md()
md("## 2. Renombrado de columnas")
md("Se renombraron las columnas originales a nombres cortos y manejables:")
md()
md("| # | Nombre asignado |")
md("|---|-----------------|")
for i, (orig, nuevo) in enumerate(NOMBRES_COLUMNAS.items()):
    if nuevo == "Altura":
        continue
    md(f"| {i} | `{nuevo}` |")
md()
md("> Nota: se descartó la columna **Altura** (numeración de calle) porque no aporta valor al análisis del negocio.")

# ── 3. Strip de espacios en todas las celdas de tipo texto ──────────────────
# También eliminamos non-breaking spaces (\xa0) y otros whitespace Unicode
cambios_strip = 0
for col in df.columns:
    if pd.api.types.is_string_dtype(df[col]):
        original = df[col].copy()
        # Reemplazar narrow no-break space (\u202f), no-break space (\xa0) y zero-width space
        # Usamos caracteres literales (no \u) por compatibilidad con pyarrow regex.
        df[col] = (df[col]
                   .str.replace("\xa0", " ", regex=False)
                   .str.replace("\u202f", " ", regex=False)
                   .str.replace("\u200b", "", regex=False)
                   .str.strip())
        # Contar cambios ignorando NaN
        mask = original.notna() & df[col].notna() & (original != df[col])
        cambios_strip += mask.sum()
md()
md("## 3. Limpieza de espacios")
md(f"Se eliminaron espacios iniciales/finales y caracteres Unicode invisibles (`\\xa0`, `\\u202f`, `\\u200b`) en **{cambios_strip} celdas**.")

# ── 4. Reporte de nulos por columna ─────────────────────────────────────────
md()
md("## 4. Análisis de nulos por columna")
md()
md("| Columna | Nulos | Vacíos (`''`) |")
md("|---------|------:|-------------:|")
nulos_por_col = df.isnull().sum()
hay_nulos = False
for col, n in nulos_por_col.items():
    vacios = (df[col] == "").sum() if pd.api.types.is_string_dtype(df[col]) else 0
    if n > 0 or vacios > 0:
        md(f"| `{col}` | {n} | {vacios} |")
        hay_nulos = True
if not hay_nulos:
    md("| *(ninguna)* | 0 | 0 |")

# ── 5. Eliminar filas completamente vacías ──────────────────────────────────
df_replaced = df.replace("", pd.NA)
filas_antes = len(df)
df = df[~df_replaced.drop(columns=["Marca_Temporal"]).isna().all(axis=1)]
filas_vacias = filas_antes - len(df)
md()
md("## 5. Filas completamente vacías")
md(f"Se eliminaron **{filas_vacias}** filas donde todas las columnas (excepto `Marca_Temporal`) estaban vacías.")

# ── 6. Eliminar duplicados ─────────────────────────────────────────────────
# 6a. Duplicados exactos (todas las columnas excepto Marca_Temporal)
cols_sin_ts = [c for c in df.columns if c != "Marca_Temporal"]
filas_antes = len(df)
df.drop_duplicates(subset=cols_sin_ts, keep="first", inplace=True)
duplicados = filas_antes - len(df)
md()
md("## 6. Eliminación de duplicados")
md()
md("### 6a. Duplicados exactos")
md(f"Se eliminaron **{duplicados}** filas duplicadas exactas (ignorando `Marca_Temporal`).")

# 6b. Cuasi-duplicados: DESACTIVADO — al eliminar la columna `Altura` ya no
# podemos distinguir casas distintas dentro del mismo barrio con los mismos
# atributos básicos, por lo que el criterio perdió precisión.
md()
md("### 6b. Cuasi-duplicados")
md("*Paso desactivado:* al eliminar la columna `Altura` (numeración de calle) "
   "el criterio de cuasi-duplicados por `Ciudad+Barrio+Integrantes+Tipo_Mascotas+Tipo_Vivienda` "
   "ya no distingue casas distintas dentro de un mismo barrio, por lo que se omite "
   "para no eliminar encuestas válidas.")

# ── 7. Normalización de la columna "Barrio" ────────────────────────────────
# 7a. Title case general
md()
md("## 7. Normalización de Barrio")
df["Barrio"] = df["Barrio"].str.title()

# 7b. Diccionario de normalización para unificar variantes
BARRIO_MAP = {
    # Cotolengo / Cottolengo
    "Cottolengo": "Cotolengo",
    # Vélez Sarsfield y variantes
    "Velez Sarsfield": "Vélez Sársfield",
    "Velez Sarfield": "Vélez Sársfield",
    "Vélez Sarfield": "Vélez Sársfield",
    "Vélez Sarsfield": "Vélez Sársfield",
    "Velez Sarfueld": "Vélez Sársfield",
    "Vélez Sardield": "Vélez Sársfield",
    # José Hernández y variantes
    "Jose Hernández": "José Hernández",
    "Jose Hernandez": "José Hernández",
    "José Hernandez": "José Hernández",
    "Hernandez": "José Hernández",
    # Consolata
    "La Consolata": "Consolata",
    # La Milka variantes (con sub-sector se unifica a La Milka)
    "La Milka (Loteo Procrear)": "La Milka",
    "La Milka - Sector Procrear": "La Milka",
    "La Milka - Procrear": "La Milka",
    "Milka - Procrear": "La Milka",
    # Palmares variantes (genérico sin número → Palmares I)
    "Los Palmares": "Palmares I",
    "Palmares": "Palmares I",
    "Los Palmares Iii": "Palmares III",
    "Palmarés Iii": "Palmares III",
    "Palmares Iii": "Palmares III",
    "Palmarés 3": "Palmares III",
    "Palmares Ii": "Palmares II",
    "Palmare Ii": "Palmares II",
    "Palmares L": "Palmares I",
    "Palmares 1": "Palmares I",
    "Palmares 2": "Palmares II",
    "Palmares 3": "Palmares III",
    "Palmares 4": "Palmares IV",
    # Parque → Barrio Parque (nombre oficial)
    "Parque": "Barrio Parque",
    "Nuevo Barrio Parque": "Barrio Parque",
    "30 Viviendas Barrio Parque": "Barrio Parque",
    "Parque Nortw": "Barrio Parque",
    "Parque Norte": "Barrio Parque",
    # Parque De Las Rosas y Casonas Del Bosque → Las Rosas (mismo barrio)
    "Parque Las Rosas": "Las Rosas",
    "Parque De Las Rosas": "Las Rosas",
    "Casonas Del Bosque": "Las Rosas",
    "Casonas": "Las Rosas",
    # Villa Golf
    "Villa Golf": "Villa Golf",
    # Aires Del Golf (typo Ayres → Aires)
    "Ayres Del Golf": "Aires Del Golf",
    # Roca y variantes
    "Bv. Roca": "Roca",
    "Gral Roca": "Roca",
    "General Roca": "Roca",
    "Rocca": "Roca",
    "B°Roca": "Roca",
    "B° Roca": "Roca",
    # Jardín
    "Jardin": "Jardín",
    # Maipú (Residencial Maipú es el mismo barrio Maipú)
    "Maipu": "Maipú",
    "Nuevo Parque Maipú": "Maipú",
    "Residencial Maipu": "Maipú",
    "Residencial Maipú": "Maipú",
    # Catedral (limpiar número pegado)
    "Catedral 2134": "Catedral",
    "Cateedral": "Catedral",
    # Dos Hermanos
    "2 Hermanos": "Dos Hermanos",
    # Independencia
    "Independecia": "Independencia",
    # San Martín
    "San Martin": "San Martín",
    # San José
    "San Jose": "San José",
    # Corradi
    "Corradi/ Colonizadores": "Corradi",
    # Brisas Del Sur (incluye Emprendimiento Del Sur)
    "Brisa Del Sur": "Brisas Del Sur",
    "Emprendimiento Del Sur": "Brisas Del Sur",
    # Las 400
    "400 Viviendas": "Las 400",
    # Loteos Manantiales
    "Loteo Manantiales": "Manantiales",
    "Loteo Los Manantiales": "Manantiales",
    # Procrear dentro de La Milka
    "Procrear": "La Milka",
    # Plaza San Fco
    "Plaza San Fco": "Plaza San Francisco",
    # Magdalena variantes (genérico sin número → Magdalena I)
    "Magdalena": "Magdalena I",
    "Magdalena 1": "Magdalena I",
    "Magdalena 2": "Magdalena II",
    "Magdalena Dos": "Magdalena II",
    # Francucci / Barrio Francucci
    "Barrio Francucci": "Francucci",
    # Timbues → Timbúes (ortografía correcta)
    "Timbues": "Timbúes",
    # Boero Romano → 20 De Junio (mismo barrio)
    "Boero Romano": "20 De Junio",
    # Savio (todas las variantes son el mismo barrio)
    "General Savio": "Savio",
    "Senderos Del Savio": "Savio",
    # Nueva Córdoba
    "Nueva Cordoba": "Nueva Córdoba",
    # Libertador Sur es una calle, no un barrio: corresponde al barrio Bouchard
    "Libertador Sur": "Bouchard",
    "Av. Libertador Sur": "Bouchard",
    "Avenida Libertador Sur": "Bouchard",
    "Buchar": "Bouchard",
    # 9 de Septiembre (typo)
    "9 De Sepriembre": "9 De Septiembre",
    # Barrio Jardín → Jardín (ya pasa por title())
    "Barrio Jardín": "Jardín",
    # Villa Luján Santo Tomé: Ciudad="Santo Tomé" pegada al Barrio. Se separa.
    "Villa Luján Santo Tomé": "Villa Luján",
    "Villa Lujan Santo Tome": "Villa Luján",
    # Barrio Ciudad (Las 400)
    "Barrio Ciudad (Las 400)": "Las 400",
}

cambios_barrio = 0
barrio_cambios_detalle = []
for viejo, nuevo in BARRIO_MAP.items():
    mask = df["Barrio"] == viejo
    n = mask.sum()
    if n > 0:
        df.loc[mask, "Barrio"] = nuevo
        cambios_barrio += n
        barrio_cambios_detalle.append((viejo, nuevo, n))

# Registrar valores únicos de Barrio para revisión
barrios_unicos = sorted(df["Barrio"].dropna().unique())
md()
md("Se aplicó `title()` + diccionario de normalización para unificar variantes.")
md()
if barrio_cambios_detalle:
    md("| Valor original | Valor normalizado | Filas |")
    md("|----------------|-------------------|------:|")
    for viejo, nuevo, n in barrio_cambios_detalle:
        md(f"| {viejo} | {nuevo} | {n} |")
md()
md(f"**Total de cambios:** {cambios_barrio}")
md(f"**Valores únicos tras limpieza:** {len(barrios_unicos)}")

# ── 8. Normalización de la columna "Ciudad" ────────────────────────────────
md()
md("## 8. Normalización de Ciudad")
df["Ciudad"] = df["Ciudad"].str.title()

# "Plaza San Francisco" cargado como Ciudad es en realidad un barrio de San Francisco:
# se reasigna Ciudad = "San Francisco" y se traslada el valor al Barrio (si está vacío).
mask_psf = df["Ciudad"] == "Plaza San Francisco"
n_psf = mask_psf.sum()
if n_psf > 0:
    barrio_vacio = mask_psf & (df["Barrio"].isna() | (df["Barrio"].astype(str).str.strip() == ""))
    df.loc[barrio_vacio, "Barrio"] = "Plaza San Francisco"
    df.loc[mask_psf, "Ciudad"] = "San Francisco"
    md(f"- `Plaza San Francisco` (barrio mal cargado como Ciudad) → Ciudad=`San Francisco`, "
       f"Barrio=`Plaza San Francisco` en **{n_psf} fila(s)** "
       f"(de las cuales {barrio_vacio.sum()} tenían Barrio vacío y se completaron).")

ciudades_unicas = sorted(df["Ciudad"].dropna().unique())
md(f"Valores únicos: `{'`, `'.join(ciudades_unicas)}`")

# 8a. Reasignaciones por Barrio:
#  - Barrios de Córdoba Capital (Nuevo Centro, Manantiales) → Ciudad = "Córdoba"
#  - Timbúes (localidad de Santa Fe) → Ciudad = "Otra"
#  - Barrio "Zona Urbana" (genérico no informativo) → Barrio = "Otro"
md()
md("### 8a. Reasignaciones por barrio")
barrios_cordoba = ["Nuevo Centro", "Manantiales"]
mask_cba = df["Barrio"].isin(barrios_cordoba)
n_cba = int(mask_cba.sum())
if n_cba > 0:
    df.loc[mask_cba, "Ciudad"] = "Córdoba"
    md(f"- Barrios `{'`, `'.join(barrios_cordoba)}` → Ciudad = `Córdoba` "
       f"en **{n_cba} fila(s)** (corresponden a Córdoba Capital, no a San Francisco).")

mask_timb = df["Barrio"].astype(str) == "Timbúes"
n_timb = int(mask_timb.sum())
if n_timb > 0:
    df.loc[mask_timb, "Ciudad"] = "Otra"
    md(f"- Barrio `Timbúes` (localidad de Santa Fe) → Ciudad = `Otra` "
       f"en **{n_timb} fila(s)**.")

mask_zu = df["Barrio"].astype(str) == "Zona Urbana"
n_zu = int(mask_zu.sum())
if n_zu > 0:
    df.loc[mask_zu, "Barrio"] = "Otro"
    md(f"- Barrio `Zona Urbana` (genérico no informativo) → Barrio = `Otro` "
       f"en **{n_zu} fila(s)**.")

# Recalcular ciudades únicas tras la reasignación
ciudades_unicas = sorted(df["Ciudad"].dropna().unique())
md(f"Valores únicos de Ciudad tras reasignación: `{'`, `'.join(ciudades_unicas)}`")

# 8b. Cuando la Ciudad es "Otra", el Barrio reportado no es relevante para
# el análisis comparativo (ciudad fuera del recorte). Se unifica a "Otro"
# para evitar que un único registro genere un barrio "fantasma".
mask_otra = df["Ciudad"].astype(str) == "Otra"
n_otra = int(mask_otra.sum())
if n_otra > 0:
    df.loc[mask_otra, "Barrio"] = "Otro"
    md()
    md(f"- Ciudad = `Otra` → se unifica `Barrio = Otro` en **{n_otra} fila(s)** "
       f"(barrios fuera del recorte geográfico, no comparables).")

# ── 9. Normalización "Tipo_Vivienda" ───────────────────────────────────────
md()
md("## 9. Normalización de Tipo de Vivienda")
df["Tipo_Vivienda"] = df["Tipo_Vivienda"].str.title()
tipos_viv = sorted(df["Tipo_Vivienda"].dropna().unique())
md(f"Valores únicos: `{'`, `'.join(tipos_viv)}`")

# ── 10. Limpieza de columnas numéricas ──────────────────────────────────────
md()
md("## 10. Limpieza de columnas numéricas")

# 10a. Integrantes_Familia: limpiar y convertir
integrantes_orig_na = df["Integrantes_Familia"].isna().sum()
df["Integrantes_Familia"] = df["Integrantes_Familia"].astype(str).str.strip()
df["Integrantes_Familia"] = df["Integrantes_Familia"].mask(
    df["Integrantes_Familia"].isin(["", "nan"])
)
df["Integrantes_Familia"] = pd.to_numeric(df["Integrantes_Familia"], errors="coerce")
integrantes_convertidos_na = df["Integrantes_Familia"].isna().sum() - integrantes_orig_na
md(f"- **Integrantes_Familia:** {max(integrantes_convertidos_na, 0)} valores no numéricos convertidos a `NaN` "
   f"(NaN totales tras conversión: {df['Integrantes_Familia'].isna().sum()})")

# Detectar Integrantes = 0
ceros_integrantes = (df["Integrantes_Familia"] == 0).sum()
if ceros_integrantes > 0:
    md(f"- ⚠️ **{ceros_integrantes} fila(s)** con 0 integrantes (posible error de carga)")

# 10b. Columnas de cantidad de mascotas
md()
md("### Columnas de cantidad de mascotas")
COLS_MASCOTAS = ["Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"]
for col in COLS_MASCOTAS:
    original = df[col].copy()
    mask_mayor5 = df[col].astype(str).str.strip() == "> 5"
    n_mayor5 = mask_mayor5.sum()
    if n_mayor5 > 0:
        df.loc[mask_mayor5, col] = "6"
        md(f"- `{col}`: `\"> 5\"` reemplazado por `6` en **{n_mayor5} filas**")

    df[col] = df[col].astype(str).str.strip().replace("", pd.NA)
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ── 11. Normalización de columnas categóricas con Si/No ────────────────────
md()
md("## 11. Normalización columnas Sí/No")
md()
md("| Columna | Valores resultantes |")
md("|---------|---------------------|")
COLS_SI_NO = [
    "Mascota_Castrada",
    "Sabe_Castracion_Gratuita",
    "Vacunadas",
    "Desparasitadas",
    "Sabe_Vacunas_Anuales",
]
for col in COLS_SI_NO:
    df[col] = df[col].str.strip().str.title()
    valores = sorted(df[col].dropna().unique())
    md(f"| `{col}` | {', '.join(valores)} |")

# ── 12. Normalización "Humano_Responsable" ──────────────────────────────────
md()
md("## 12. Normalización de Humano Responsable")
df["Humano_Responsable"] = df["Humano_Responsable"].str.strip().str.title()
vals_hr = sorted(df["Humano_Responsable"].dropna().unique())
md(f"Valores únicos: `{'`, `'.join(vals_hr)}`")

# ── 13. Normalización "Frecuencia_Callejeros" ──────────────────────────────
md()
md("## 13. Normalización de Frecuencia Callejeros")
df["Frecuencia_Callejeros"] = df["Frecuencia_Callejeros"].str.strip().str.title()
vals_fc = sorted(df["Frecuencia_Callejeros"].dropna().unique())
md(f"Valores únicos: `{'`, `'.join(vals_fc)}`")

# ── 14. Normalización "Donde_Castracion" ───────────────────────────────────
md()
md("## 14. Normalización de Donde Castración")
df["Donde_Castracion"] = df["Donde_Castracion"].str.strip()

# Corregir inconsistencia: Mascota_Castrada=No pero Donde_Castracion tiene un lugar
incons_cast = (
    (df["Mascota_Castrada"] == "No")
    & df["Donde_Castracion"].notna()
    & (df["Donde_Castracion"] != "No se encuentra castrada.")
)
n_incons = incons_cast.sum()
if n_incons > 0:
    md()
    md(f"⚠️ **{n_incons} filas** con `Mascota_Castrada = No` pero `Donde_Castracion` tiene un lugar:")
    md()
    md("| Fila | Castrada | Donde |")
    md("|-----:|----------|-------|")
    for idx in df[incons_cast].index:
        md(f"| {idx} | {df.loc[idx, 'Mascota_Castrada']} | {df.loc[idx, 'Donde_Castracion']} |")

vals_dc = sorted(df["Donde_Castracion"].dropna().unique())
md()
md(f"Valores únicos ({len(vals_dc)}):")
for v in vals_dc:
    md(f"- `{v}`")

# ── 15. Normalización multi-valor (columnas con ";") ───────────────────────
md()
md("## 15. Normalización de columnas multi-valor")
md("Columnas con opciones separadas por `;`: se normalizaron (strip + orden alfabético + sin duplicados internos).")
md()
COLS_MULTI = [
    "Tipo_Mascotas",
    "Como_Viven_Mascotas",
    "Animal_Perdido_Frecuente",
    "Municipio_Presente",
    "Donde_Castracion",
]
for col in COLS_MULTI:
    if pd.api.types.is_string_dtype(df[col]):
        df[col] = df[col].apply(
            lambda x: ";".join(
                sorted(set(op.strip() for op in x.split(";")))
            ) if pd.notna(x) else x
        )
        vals = sorted(df[col].dropna().unique())
        md(f"### `{col}` — {len(vals)} valores únicos")
        md()
        md("| Valor | Cantidad |")
        md("|-------|--------:|")
        for v in vals:
            cnt = (df[col] == v).sum()
            md(f"| {v} | {cnt} |")
        md()

# ── 15b. One-hot encoding de columnas multi-valor ──────────────────────────
md()
md("## 15b. One-hot encoding de columnas multi-respuesta")
md("Por cada categoría individual se crea una columna binaria (1/0).")
md()

COLS_ONEHOT = {
    "Tipo_Mascotas": "Mascota",
    "Como_Viven_Mascotas": "Vive",
    "Donde_Castracion": "CastEn",
    "Municipio_Presente": "Mun",
}

for col, prefijo in COLS_ONEHOT.items():
    categorias = set()
    for val in df[col].dropna():
        for parte in val.split(";"):
            categorias.add(parte.strip())
    categorias = sorted(categorias)
    for cat in categorias:
        nueva_col = f"{prefijo}_{cat.replace(' ', '_')}"
        df[nueva_col] = df[col].apply(
            lambda x: 1 if pd.notna(x) and cat in [p.strip() for p in x.split(";")] else 0
        )
    md(f"### `{col}` → {len(categorias)} columnas nuevas (prefijo `{prefijo}_`)")
    md()
    md("| Columna nueva | Cantidad (=1) |")
    md("|---------------|-------------:|")
    for cat in categorias:
        nueva_col = f"{prefijo}_{cat.replace(' ', '_')}"
        md(f"| `{nueva_col}` | {df[nueva_col].sum()} |")
    md()

# ── 16. Revisión por barrios inválidos ──────────────────────────────────────
md("## 16. Barrios inválidos o sospechosos")
md("Valores que no representan un barrio real — se reemplazan por `NaN`.")
md()
BARRIOS_INVALIDOS = [".", "-", "Ciudad", "Josefina", "Municipal", "San Francisco"]
barrios_removidos = []
for barrio in BARRIOS_INVALIDOS:
    mask = df["Barrio"] == barrio
    n = mask.sum()
    if n > 0:
        barrios_removidos.append((barrio, n))
        df.loc[mask, "Barrio"] = pd.NA
if barrios_removidos:
    md("| Valor | Filas afectadas |")
    md("|-------|----------------:|")
    for barrio, n in barrios_removidos:
        md(f"| `{barrio}` | {n} |")
else:
    md("No se encontraron barrios inválidos.")

# ── 17. Convertir Marca_Temporal a datetime ─────────────────────────────────
md()
md("## 17. Conversión de Marca Temporal")
md("Formato original: `YYYY/MM/DD H:MM:SS p. m. GMT-3`")
# El formato es "2026/03/05 9:40:00 p. m. GMT-3"
df["Marca_Temporal"] = (
    df["Marca_Temporal"]
    .str.replace(r"\s*GMT-3", "", regex=True)
    .str.replace("\u202f", " ", regex=False)
    .str.replace("\xa0", " ", regex=False)
    .str.replace("a. m.", "AM", regex=False)
    .str.replace("p. m.", "PM", regex=False)
    .str.strip()
)
muestra = df["Marca_Temporal"].dropna().iloc[0] if len(df) > 0 else "N/A"
md(f"- Ejemplo tras limpieza: `{muestra}`")
df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"], format="%Y/%m/%d %I:%M:%S %p", errors="coerce")
invalidos_ts = df["Marca_Temporal"].isna().sum()
md(f"- Timestamps no parseados: **{invalidos_ts}**")

# ── 18. Validación de consistencia lógica ───────────────────────────────────
md()
md("## 18. Validación de consistencia lógica")

# 18a. Dice tener gatos pero no cargó ningún dato de gatos
tiene_gatos = df["Tipo_Mascotas"].str.contains("Gatos", na=False)
sin_datos_gatos = df["Gatos_Macho"].isna() & df["Gatos_Hembra"].isna()
incons_gatos = df[tiene_gatos & sin_datos_gatos]
if len(incons_gatos) > 0:
    md(f"- ⚠️ **{len(incons_gatos)} fila(s)** dicen tener Gatos pero no cargaron cantidad:")
    for idx in incons_gatos.index:
        md(f"  - Fila {idx}: `Tipo_Mascotas` = {df.loc[idx, 'Tipo_Mascotas']}")

# 18b. Integrantes = 0 → se reemplaza por NaN
mask_cero = df["Integrantes_Familia"] == 0
n_cero = mask_cero.sum()
if n_cero > 0:
    df.loc[mask_cero, "Integrantes_Familia"] = pd.NA
    md(f"- `Integrantes_Familia = 0` reemplazado por `NaN` en **{n_cero} filas**")

# 18c. Reset del índice final
df.reset_index(drop=True, inplace=True)

# ── 19. Resumen final ───────────────────────────────────────────────────────
md()
md("---")
md()
md("## 19. Resumen final")
md()
md("| Métrica | Valor |")
md("|---------|------:|")
md(f"| Filas originales | {filas_orig} |")
md(f"| Filas después de limpiar | {len(df)} |")
md(f"| Filas eliminadas | {filas_orig - len(df)} |")
md(f"| Columnas | {len(df.columns)} |")

md()
md("### Nulos restantes por columna")
md()
md("| Columna | Nulos |")
md("|---------|------:|")
hay_nulos_final = False
for col in df.columns:
    n = df[col].isna().sum()
    if n > 0:
        md(f"| `{col}` | {n} |")
        hay_nulos_final = True
if not hay_nulos_final:
    md("| *(ninguna)* | 0 |")

md()
md("### Tipos de datos finales")
md()
md("| Columna | Tipo |")
md("|---------|------|")
for col in df.columns:
    md(f"| `{col}` | `{df[col].dtype}` |")

# ── 20. Guardar CSV limpio y log ────────────────────────────────────────────
md()
md("---")
md()
md(f"✅ **Dataset limpio guardado en:** `{os.path.basename(CSV_LIMPIO)}`")
# Guardar informe primero (no depende de permisos del CSV)
guardar_informe()

try:
    df.to_csv(CSV_LIMPIO, index=False, encoding="utf-8")
    msg = f"\nDataset limpio guardado en: {CSV_LIMPIO}"
except PermissionError:
    alt = CSV_LIMPIO.replace(".csv", "_nuevo.csv")
    df.to_csv(alt, index=False, encoding="utf-8")
    msg = (f"\nNo se pudo escribir {os.path.basename(CSV_LIMPIO)} (archivo bloqueado).\n"
           f"  Se guardo como: {os.path.basename(alt)}")

try:
    print(msg)
    print("\nLimpieza completada con exito.")
except UnicodeEncodeError:
    print(msg.encode("ascii", "replace").decode("ascii"))
    print("\nLimpieza completada con exito.")
