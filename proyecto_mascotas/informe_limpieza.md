# Informe de Limpieza — Relevamiento Cuidado de Mascotas
**Fecha de ejecución:** 2026-04-30 17:01:29

---

## 1. Carga del dataset
- **Archivo:** `Relevamiento Cuidado de Mascotas Actualizado.csv`
- **Filas:** 507
- **Columnas:** 22

## 2. Renombrado de columnas
Se renombraron las columnas originales a nombres cortos y manejables:

| # | Nombre asignado |
|---|-----------------|
| 0 | `Marca_Temporal` |
| 1 | `Ciudad` |
| 2 | `Barrio` |
| 4 | `Tipo_Vivienda` |
| 5 | `Integrantes_Familia` |
| 6 | `Tipo_Mascotas` |
| 7 | `Perros_Macho` |
| 8 | `Perros_Hembra` |
| 9 | `Gatos_Macho` |
| 10 | `Gatos_Hembra` |
| 11 | `Mascota_Castrada` |
| 12 | `Donde_Castracion` |
| 13 | `Sabe_Castracion_Gratuita` |
| 14 | `Vacunadas` |
| 15 | `Desparasitadas` |
| 16 | `Sabe_Vacunas_Anuales` |
| 17 | `Como_Viven_Mascotas` |
| 18 | `Frecuencia_Callejeros` |
| 19 | `Animal_Perdido_Frecuente` |
| 20 | `Municipio_Presente` |
| 21 | `Humano_Responsable` |

> Nota: se descartó la columna **Altura** (numeración de calle) porque no aporta valor al análisis del negocio.

## 3. Limpieza de espacios
Se eliminaron espacios iniciales/finales y caracteres Unicode invisibles (`\xa0`, `\u202f`, `\u200b`) en **682 celdas**.

## 4. Análisis de nulos por columna

| Columna | Nulos | Vacíos (`''`) |
|---------|------:|-------------:|
| `Perros_Macho` | 254 | 0 |
| `Perros_Hembra` | 200 | 0 |
| `Gatos_Macho` | 364 | 0 |
| `Gatos_Hembra` | 346 | 0 |

## 5. Filas completamente vacías
Se eliminaron **0** filas donde todas las columnas (excepto `Marca_Temporal`) estaban vacías.

## 6. Eliminación de duplicados

### 6a. Duplicados exactos
Se eliminaron **0** filas duplicadas exactas (ignorando `Marca_Temporal`).

### 6b. Cuasi-duplicados
*Paso desactivado:* al eliminar la columna `Altura` (numeración de calle) el criterio de cuasi-duplicados por `Ciudad+Barrio+Integrantes+Tipo_Mascotas+Tipo_Vivienda` ya no distingue casas distintas dentro de un mismo barrio, por lo que se omite para no eliminar encuestas válidas.

## 7. Normalización de Barrio

Se aplicó `title()` + diccionario de normalización para unificar variantes.

| Valor original | Valor normalizado | Filas |
|----------------|-------------------|------:|
| Cottolengo | Cotolengo | 5 |
| Velez Sarsfield | Vélez Sársfield | 9 |
| Velez Sarfield | Vélez Sársfield | 9 |
| Vélez Sarfield | Vélez Sársfield | 4 |
| Vélez Sarsfield | Vélez Sársfield | 6 |
| Velez Sarfueld | Vélez Sársfield | 1 |
| Vélez Sardield | Vélez Sársfield | 1 |
| Jose Hernández | José Hernández | 1 |
| Jose Hernandez | José Hernández | 3 |
| José Hernandez | José Hernández | 3 |
| Hernandez | José Hernández | 2 |
| La Consolata | Consolata | 1 |
| La Milka (Loteo Procrear) | La Milka | 1 |
| La Milka - Sector Procrear | La Milka | 1 |
| La Milka - Procrear | La Milka | 1 |
| Milka - Procrear | La Milka | 1 |
| Los Palmares | Palmares | 4 |
| Los Palmares Iii | Palmares III | 1 |
| Palmarés Iii | Palmares III | 1 |
| Palmares Iii | Palmares III | 1 |
| Palmarés 3 | Palmares III | 1 |
| Palmares Ii | Palmares II | 1 |
| Palmare Ii | Palmares II | 1 |
| Palmares L | Palmares I | 1 |
| Palmares 1 | Palmares I | 4 |
| Palmares 2 | Palmares II | 3 |
| Palmares 3 | Palmares III | 5 |
| Palmares 4 | Palmares IV | 3 |
| Parque | Barrio Parque | 8 |
| Nuevo Barrio Parque | Barrio Parque | 1 |
| 30 Viviendas Barrio Parque | Barrio Parque | 1 |
| Parque Nortw | Parque Norte | 1 |
| Parque Las Rosas | Las Rosas | 3 |
| Parque De Las Rosas | Las Rosas | 2 |
| Casonas Del Bosque | Las Rosas | 3 |
| Casonas | Las Rosas | 3 |
| Villa Golf | Villa Golf | 5 |
| Ayres Del Golf | Aires Del Golf | 2 |
| Bv. Roca | Roca | 1 |
| Gral Roca | Roca | 1 |
| Rocca | Roca | 2 |
| B°Roca | Roca | 1 |
| Jardin | Jardín | 2 |
| Maipu | Maipú | 1 |
| Nuevo Parque Maipú | Maipú | 1 |
| Residencial Maipu | Maipú | 1 |
| Catedral 2134 | Catedral | 1 |
| Cateedral | Catedral | 1 |
| 2 Hermanos | Dos Hermanos | 1 |
| Independecia | Independencia | 1 |
| San Martin | San Martín | 5 |
| San Jose | San José | 1 |
| Corradi/ Colonizadores | Corradi | 1 |
| Brisa Del Sur | Brisas Del Sur | 1 |
| Emprendimiento Del Sur | Brisas Del Sur | 1 |
| 400 Viviendas | Las 400 | 1 |
| Loteo Manantiales | Manantiales | 1 |
| Loteo Los Manantiales | Manantiales | 1 |
| Procrear | La Milka | 4 |
| Plaza San Fco | Plaza San Francisco | 1 |
| Magdalena 1 | Magdalena I | 2 |
| Magdalena 2 | Magdalena II | 3 |
| Magdalena Dos | Magdalena II | 1 |
| Barrio Francucci | Francucci | 1 |
| Timbues | Timbúes | 1 |
| Boero Romano | 20 De Junio | 1 |
| Nueva Cordoba | Nueva Córdoba | 1 |
| Libertador Sur | Bouchard | 1 |
| Buchar | Bouchard | 1 |
| 9 De Sepriembre | 9 De Septiembre | 1 |
| Barrio Jardín | Jardín | 1 |
| Villa Luján Santo Tomé | Villa Luján | 1 |
| Barrio Ciudad (Las 400) | Las 400 | 1 |

**Total de cambios:** 151
**Valores únicos tras limpieza:** 72

## 8. Normalización de Ciudad
- `Plaza San Francisco` (barrio mal cargado como Ciudad) → Ciudad=`San Francisco`, Barrio=`Plaza San Francisco` en **1 fila(s)** (de las cuales 0 tenían Barrio vacío y se completaron).
Valores únicos: `Frontera`, `Josefina`, `Otra`, `San Francisco`

### 8a. Reasignaciones por barrio
- Barrios `Nuevo Centro`, `Manantiales` → Ciudad = `Córdoba` en **4 fila(s)** (corresponden a Córdoba Capital, no a San Francisco).
- Barrio `Timbúes` (localidad de Santa Fe) → Ciudad = `Otra` en **1 fila(s)**.
- Barrio `Zona Urbana` (genérico no informativo) → Barrio = `Otro` en **1 fila(s)**.
Valores únicos de Ciudad tras reasignación: `Córdoba`, `Frontera`, `Josefina`, `Otra`, `San Francisco`

- Ciudad = `Otra` → se unifica `Barrio = Otro` en **11 fila(s)** (barrios fuera del recorte geográfico, no comparables).

## 9. Normalización de Tipo de Vivienda
Valores únicos: `Casa En Alquiler`, `Casa Propia`, `Departamento En Alquiler`, `Departamento Propio`

## 10. Limpieza de columnas numéricas
- **Integrantes_Familia:** 0 valores no numéricos convertidos a `NaN` (NaN totales tras conversión: 0)
- ⚠️ **3 fila(s)** con 0 integrantes (posible error de carga)

### Columnas de cantidad de mascotas
- `Perros_Macho`: `"> 5"` reemplazado por `6` en **3 filas**
- `Perros_Hembra`: `"> 5"` reemplazado por `6` en **1 filas**
- `Gatos_Macho`: `"> 5"` reemplazado por `6` en **1 filas**

## 11. Normalización columnas Sí/No

| Columna | Valores resultantes |
|---------|---------------------|
| `Mascota_Castrada` | No, Si |
| `Sabe_Castracion_Gratuita` | No, Si |
| `Vacunadas` | No, Si |
| `Desparasitadas` | No, Si |
| `Sabe_Vacunas_Anuales` | No, Si |

## 12. Normalización de Humano Responsable
Valores únicos: `No`, `Si`, `Un Poco`

## 13. Normalización de Frecuencia Callejeros
Valores únicos: `A Veces`, `Nunca`, `Todo El Tiempo`

## 14. Normalización de Donde Castración

⚠️ **4 filas** con `Mascota_Castrada = No` pero `Donde_Castracion` tiene un lugar:

| Fila | Castrada | Donde |
|-----:|----------|-------|
| 179 | No | En forma particular |
| 206 | No | En forma particular;No se encuentra castrada. |
| 304 | No | Municipio |
| 369 | No | En forma particular |

Valores únicos (6):
- `En forma particular`
- `En forma particular;No se encuentra castrada.`
- `Municipio`
- `Municipio;En forma particular`
- `Municipio;No se encuentra castrada.`
- `No se encuentra castrada.`

## 15. Normalización de columnas multi-valor
Columnas con opciones separadas por `;`: se normalizaron (strip + orden alfabético + sin duplicados internos).

### `Tipo_Mascotas` — 3 valores únicos

| Valor | Cantidad |
|-------|--------:|
| Gatos | 74 |
| Gatos;Perros | 163 |
| Perros | 270 |

### `Como_Viven_Mascotas` — 6 valores únicos

| Valor | Cantidad |
|-------|--------:|
| Salen solos a la calle | 11 |
| Salen solos a la calle;Tienen identificador;Viven dentro de su hogar | 15 |
| Salen solos a la calle;Viven dentro de su hogar | 43 |
| Tienen identificador | 2 |
| Tienen identificador;Viven dentro de su hogar | 59 |
| Viven dentro de su hogar | 377 |

### `Animal_Perdido_Frecuente` — 3 valores únicos

| Valor | Cantidad |
|-------|--------:|
| Gatos | 28 |
| Gatos;Perros | 74 |
| Perros | 405 |

### `Municipio_Presente` — 10 valores únicos

| Valor | Cantidad |
|-------|--------:|
| Castraciones Masivas | 63 |
| Castraciones Masivas;Control de identificación | 57 |
| Castraciones Masivas;Control de identificación;Educación | 152 |
| Castraciones Masivas;Control de identificación;Educación;No es necesaria la participación del municipio | 1 |
| Castraciones Masivas;Educación | 101 |
| Control de identificación | 50 |
| Control de identificación;Educación | 30 |
| Educación | 43 |
| Educación;No es necesaria la participación del municipio | 1 |
| No es necesaria la participación del municipio | 9 |

### `Donde_Castracion` — 6 valores únicos

| Valor | Cantidad |
|-------|--------:|
| En forma particular | 176 |
| En forma particular;Municipio | 44 |
| En forma particular;No se encuentra castrada. | 1 |
| Municipio | 198 |
| Municipio;No se encuentra castrada. | 5 |
| No se encuentra castrada. | 83 |


## 15b. One-hot encoding de columnas multi-respuesta
Por cada categoría individual se crea una columna binaria (1/0).

### `Tipo_Mascotas` → 2 columnas nuevas (prefijo `Mascota_`)

| Columna nueva | Cantidad (=1) |
|---------------|-------------:|
| `Mascota_Gatos` | 237 |
| `Mascota_Perros` | 433 |

### `Como_Viven_Mascotas` → 3 columnas nuevas (prefijo `Vive_`)

| Columna nueva | Cantidad (=1) |
|---------------|-------------:|
| `Vive_Salen_solos_a_la_calle` | 69 |
| `Vive_Tienen_identificador` | 76 |
| `Vive_Viven_dentro_de_su_hogar` | 494 |

### `Donde_Castracion` → 3 columnas nuevas (prefijo `CastEn_`)

| Columna nueva | Cantidad (=1) |
|---------------|-------------:|
| `CastEn_En_forma_particular` | 221 |
| `CastEn_Municipio` | 247 |
| `CastEn_No_se_encuentra_castrada.` | 89 |

### `Municipio_Presente` → 4 columnas nuevas (prefijo `Mun_`)

| Columna nueva | Cantidad (=1) |
|---------------|-------------:|
| `Mun_Castraciones_Masivas` | 374 |
| `Mun_Control_de_identificación` | 290 |
| `Mun_Educación` | 328 |
| `Mun_No_es_necesaria_la_participación_del_municipio` | 11 |

## 16. Barrios inválidos o sospechosos
Valores que no representan un barrio real — se reemplazan por `NaN`.

| Valor | Filas afectadas |
|-------|----------------:|
| `Ciudad` | 2 |
| `Josefina` | 1 |
| `Municipal` | 1 |
| `San Francisco` | 3 |

## 17. Conversión de Marca Temporal
Formato original: `YYYY/MM/DD H:MM:SS p. m. GMT-3`
- Ejemplo tras limpieza: `2026/03/05 9:40:00 PM`
- Timestamps no parseados: **0**

## 18. Validación de consistencia lógica
- ⚠️ **2 fila(s)** dicen tener Gatos pero no cargaron cantidad:
  - Fila 72: `Tipo_Mascotas` = Gatos
  - Fila 318: `Tipo_Mascotas` = Gatos
- `Integrantes_Familia = 0` reemplazado por `NaN` en **3 filas**

---

## 19. Resumen final

| Métrica | Valor |
|---------|------:|
| Filas originales | 507 |
| Filas después de limpiar | 507 |
| Filas eliminadas | 0 |
| Columnas | 33 |

### Nulos restantes por columna

| Columna | Nulos |
|---------|------:|
| `Barrio` | 7 |
| `Integrantes_Familia` | 3 |
| `Perros_Macho` | 254 |
| `Perros_Hembra` | 200 |
| `Gatos_Macho` | 364 |
| `Gatos_Hembra` | 346 |

### Tipos de datos finales

| Columna | Tipo |
|---------|------|
| `Marca_Temporal` | `datetime64[us]` |
| `Ciudad` | `str` |
| `Barrio` | `str` |
| `Tipo_Vivienda` | `str` |
| `Integrantes_Familia` | `float64` |
| `Tipo_Mascotas` | `str` |
| `Perros_Macho` | `float64` |
| `Perros_Hembra` | `float64` |
| `Gatos_Macho` | `float64` |
| `Gatos_Hembra` | `float64` |
| `Mascota_Castrada` | `str` |
| `Donde_Castracion` | `str` |
| `Sabe_Castracion_Gratuita` | `str` |
| `Vacunadas` | `str` |
| `Desparasitadas` | `str` |
| `Sabe_Vacunas_Anuales` | `str` |
| `Como_Viven_Mascotas` | `str` |
| `Frecuencia_Callejeros` | `str` |
| `Animal_Perdido_Frecuente` | `str` |
| `Municipio_Presente` | `str` |
| `Humano_Responsable` | `str` |
| `Mascota_Gatos` | `int64` |
| `Mascota_Perros` | `int64` |
| `Vive_Salen_solos_a_la_calle` | `int64` |
| `Vive_Tienen_identificador` | `int64` |
| `Vive_Viven_dentro_de_su_hogar` | `int64` |
| `CastEn_En_forma_particular` | `int64` |
| `CastEn_Municipio` | `int64` |
| `CastEn_No_se_encuentra_castrada.` | `int64` |
| `Mun_Castraciones_Masivas` | `int64` |
| `Mun_Control_de_identificación` | `int64` |
| `Mun_Educación` | `int64` |
| `Mun_No_es_necesaria_la_participación_del_municipio` | `int64` |

---

✅ **Dataset limpio guardado en:** `mascotas_limpio.csv`