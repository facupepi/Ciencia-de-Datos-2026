"""
Genera datasets planos listos para Google Looker Studio (ex Data Studio).

Salidas (en carpeta `looker_studio/`):
  1. mascotas_hechos.csv      → tabla de HECHOS (1 fila = 1 encuesta) con
                                dimensiones limpias, métricas numéricas y
                                flags 1/0 listos para sumar/promediar.
  2. mascotas_multivalor.csv  → formato LARGO (long) con una fila por cada
                                opción seleccionada en columnas multi-valor.
                                Ideal para gráficos de barras de "respuestas
                                múltiples" en Looker.
  3. mascotas_resumen_geo.csv → métricas pre-agregadas por Ciudad+Barrio.
  4. diccionario_campos.csv   → diccionario de variables (campo, tipo,
                                descripción) para documentar el data source.

Cómo usar en Looker Studio:
  - Subí los CSV a Google Sheets (o conectá vía "Subida de archivo").
  - Crea un data source por cada CSV. Looker autodetecta tipos.
  - Marca `Marca_Temporal` como Date & Time.
  - Para gráficos de respuesta múltiple usá `mascotas_multivalor.csv`
    con dimensión = `Opcion` y métrica = `Cantidad` (SUM).
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_LIMPIO = os.path.join(BASE_DIR, "mascotas_limpio.csv")
OUT_DIR = os.path.join(BASE_DIR, "looker_studio")
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_LIMPIO, encoding="utf-8")
df["Marca_Temporal"] = pd.to_datetime(df["Marca_Temporal"], errors="coerce")

# ── 1. TABLA DE HECHOS ─────────────────────────────────────────────────────
hechos = df.copy()
hechos["Encuesta_ID"] = range(1, len(hechos) + 1)

# Métricas numéricas auxiliares
for c in ["Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"]:
    hechos[c] = pd.to_numeric(hechos[c], errors="coerce").fillna(0)

hechos["Total_Perros"] = hechos["Perros_Macho"] + hechos["Perros_Hembra"]
hechos["Total_Gatos"] = hechos["Gatos_Macho"] + hechos["Gatos_Hembra"]
hechos["Total_Mascotas"] = hechos["Total_Perros"] + hechos["Total_Gatos"]

# Flags 1/0 a partir de Si/No (suman directo en Looker)
SI_NO = ["Mascota_Castrada", "Sabe_Castracion_Gratuita", "Vacunadas",
         "Desparasitadas", "Sabe_Vacunas_Anuales"]
for c in SI_NO:
    hechos[f"{c}_Flag"] = (hechos[c].astype(str).str.strip().str.title() == "Si").astype(int)

# Dimensiones de fecha (para filtros y agrupaciones temporales)
hechos["Fecha"] = hechos["Marca_Temporal"].dt.date
hechos["Año"] = hechos["Marca_Temporal"].dt.year
hechos["Mes"] = hechos["Marca_Temporal"].dt.month
hechos["AñoMes"] = hechos["Marca_Temporal"].dt.strftime("%Y-%m")
hechos["DiaSemana"] = hechos["Marca_Temporal"].dt.day_name()

# Reordenar: ID + dimensiones + métricas
cols_orden = (
    ["Encuesta_ID", "Marca_Temporal", "Fecha", "Año", "Mes", "AñoMes", "DiaSemana",
     "Ciudad", "Barrio", "Tipo_Vivienda", "Integrantes_Familia",
     "Tipo_Mascotas", "Total_Perros", "Total_Gatos", "Total_Mascotas",
     "Perros_Macho", "Perros_Hembra", "Gatos_Macho", "Gatos_Hembra"]
    + SI_NO + [f"{c}_Flag" for c in SI_NO]
    + ["Donde_Castracion", "Como_Viven_Mascotas", "Frecuencia_Callejeros",
       "Animal_Perdido_Frecuente", "Municipio_Presente", "Humano_Responsable"]
)
# One-hot que ya están en el CSV limpio
oh_cols = [c for c in df.columns if c.startswith(("Mascota_", "Vive_", "CastEn_", "Mun_"))
           and c not in cols_orden and c not in SI_NO]
cols_orden += oh_cols
hechos = hechos[[c for c in cols_orden if c in hechos.columns]]

hechos.to_csv(os.path.join(OUT_DIR, "mascotas_hechos.csv"),
              index=False, encoding="utf-8")
print(f"✔ mascotas_hechos.csv       → {len(hechos)} filas, {len(hechos.columns)} columnas")

# ── 2. TABLA LARGA (multi-valor) ───────────────────────────────────────────
COLS_MULTI = {
    "Tipo_Mascotas": "Tipo de mascota",
    "Como_Viven_Mascotas": "Cómo viven",
    "Donde_Castracion": "Dónde castraron",
    "Municipio_Presente": "Pedido al municipio",
    "Animal_Perdido_Frecuente": "Animal perdido",
}
filas_long = []
for col, etiqueta in COLS_MULTI.items():
    for idx, val in df[col].dropna().items():
        for parte in str(val).split(";"):
            parte = parte.strip()
            if not parte:
                continue
            filas_long.append({
                "Encuesta_ID": idx + 1,
                "Marca_Temporal": df.loc[idx, "Marca_Temporal"],
                "Ciudad": df.loc[idx, "Ciudad"],
                "Barrio": df.loc[idx, "Barrio"],
                "Tipo_Vivienda": df.loc[idx, "Tipo_Vivienda"],
                "Categoria": etiqueta,
                "Opcion": parte,
                "Cantidad": 1,
            })
multi = pd.DataFrame(filas_long)
multi.to_csv(os.path.join(OUT_DIR, "mascotas_multivalor.csv"),
             index=False, encoding="utf-8")
print(f"✔ mascotas_multivalor.csv   → {len(multi)} filas")

# ── 3. RESUMEN GEOGRÁFICO ──────────────────────────────────────────────────
g = hechos.groupby(["Ciudad", "Barrio"], dropna=False)
resumen = g.agg(
    Encuestas=("Encuesta_ID", "count"),
    Total_Perros=("Total_Perros", "sum"),
    Total_Gatos=("Total_Gatos", "sum"),
    Total_Mascotas=("Total_Mascotas", "sum"),
    Castradas=("Mascota_Castrada_Flag", "sum"),
    Vacunadas=("Vacunadas_Flag", "sum"),
    Desparasitadas=("Desparasitadas_Flag", "sum"),
    Saben_Castracion_Gratis=("Sabe_Castracion_Gratuita_Flag", "sum"),
    Saben_Vacunas_Anuales=("Sabe_Vacunas_Anuales_Flag", "sum"),
).reset_index()

for c in ["Castradas", "Vacunadas", "Desparasitadas",
          "Saben_Castracion_Gratis", "Saben_Vacunas_Anuales"]:
    resumen[f"Pct_{c}"] = (resumen[c] / resumen["Encuestas"] * 100).round(1)

resumen.to_csv(os.path.join(OUT_DIR, "mascotas_resumen_geo.csv"),
               index=False, encoding="utf-8")
print(f"✔ mascotas_resumen_geo.csv  → {len(resumen)} filas")

# ── 4. DICCIONARIO DE CAMPOS ──────────────────────────────────────────────
descripciones = {
    "Encuesta_ID": "Identificador único de la encuesta.",
    "Marca_Temporal": "Fecha y hora en que se completó la encuesta.",
    "Fecha": "Fecha (YYYY-MM-DD).",
    "Año": "Año de la encuesta.",
    "Mes": "Mes (1-12).",
    "AñoMes": "Año-Mes en formato YYYY-MM.",
    "DiaSemana": "Día de la semana en inglés.",
    "Ciudad": "Ciudad donde reside el encuestado.",
    "Barrio": "Barrio (ya normalizado).",
    "Tipo_Vivienda": "Tipo de vivienda (Casa Propia, Alquiler, etc.).",
    "Integrantes_Familia": "Cantidad de integrantes del hogar.",
    "Tipo_Mascotas": "Texto original (Perros / Gatos / mixto).",
    "Total_Perros": "Suma de perros macho + hembra.",
    "Total_Gatos": "Suma de gatos macho + hembra.",
    "Total_Mascotas": "Total de mascotas en el hogar.",
    "Perros_Macho": "Cantidad de perros macho.",
    "Perros_Hembra": "Cantidad de perros hembra.",
    "Gatos_Macho": "Cantidad de gatos macho.",
    "Gatos_Hembra": "Cantidad de gatos hembra.",
    "Mascota_Castrada": "Sí / No — la mascota está castrada.",
    "Sabe_Castracion_Gratuita": "Sí / No — sabe que el municipio ofrece castración gratuita.",
    "Vacunadas": "Sí / No — vacunadas.",
    "Desparasitadas": "Sí / No — desparasitadas.",
    "Sabe_Vacunas_Anuales": "Sí / No — sabe que se recomiendan vacunas anuales.",
    "Mascota_Castrada_Flag": "1 si Castrada=Si, 0 si No (sumable en Looker).",
    "Sabe_Castracion_Gratuita_Flag": "1/0 sumable.",
    "Vacunadas_Flag": "1/0 sumable.",
    "Desparasitadas_Flag": "1/0 sumable.",
    "Sabe_Vacunas_Anuales_Flag": "1/0 sumable.",
    "Donde_Castracion": "Lugar(es) donde se realizó la castración.",
    "Como_Viven_Mascotas": "Cómo viven (multi-valor separado por ;).",
    "Frecuencia_Callejeros": "Frecuencia con que se observan animales callejeros.",
    "Animal_Perdido_Frecuente": "Animal que más se ve perdido (multi-valor).",
    "Municipio_Presente": "Qué se le pide al municipio (multi-valor).",
    "Humano_Responsable": "Auto-percepción de responsabilidad (Si / Un poco / No).",
}
diccionario = []
for col in hechos.columns:
    diccionario.append({
        "Campo": col,
        "Tipo": str(hechos[col].dtype),
        "Descripcion": descripciones.get(
            col,
            "One-hot de columna multi-valor (1 si seleccionó la opción)."
            if any(col.startswith(p) for p in ("Mascota_", "Vive_", "CastEn_", "Mun_"))
            else ""
        ),
    })
pd.DataFrame(diccionario).to_csv(
    os.path.join(OUT_DIR, "diccionario_campos.csv"),
    index=False, encoding="utf-8")
print(f"✔ diccionario_campos.csv    → {len(diccionario)} campos")

print(f"\n📁 Archivos guardados en: {OUT_DIR}")
