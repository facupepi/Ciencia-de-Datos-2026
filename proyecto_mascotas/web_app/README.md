# Dashboard Web — Cuidado de Mascotas (Streamlit)

Versión web del dashboard de escritorio. Pensada para deploy gratuito en
**Streamlit Community Cloud**.

## 🚀 Probar localmente

```powershell
# desde la raíz del repo, con el venv activado
pip install -r proyecto_mascotas/web_app/requirements.txt
streamlit run proyecto_mascotas/web_app/app.py
```

Abre `http://localhost:8501` en el navegador.

## ☁️ Deploy en Streamlit Community Cloud

1. **Subí el proyecto a un repo público de GitHub** (Streamlit Cloud free
   requiere repos públicos).
   ```powershell
   git init
   git add .
   git commit -m "Dashboard web mascotas"
   git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
   git push -u origin main
   ```

2. Andá a **https://share.streamlit.io** e iniciá sesión con GitHub.

3. Click en **"New app"** y completá:
   - **Repository:** `<tu-usuario>/<tu-repo>`
   - **Branch:** `main`
   - **Main file path:** `proyecto_mascotas/web_app/app.py`

4. Click en **Deploy**. En ~2 minutos tenés URL pública tipo
   `https://<tu-app>.streamlit.app`.

5. Cada `git push` redeploya solo. ✅

## 📁 Estructura

```
web_app/
├── app.py                  ← dashboard
├── mascotas_limpio.csv     ← dataset por defecto
├── requirements.txt        ← deps mínimas para Streamlit Cloud
├── .streamlit/
│   └── config.toml         ← tema clínico/teal
└── README.md
```

## ✨ Funcionalidades

- Filtros reactivos por Ciudad, Barrio, Tipo de Vivienda y Tipo de Mascotas.
- 5 KPIs (encuestas, mascotas, % castradas, % vacunadas, % desparasitadas).
- 7 pestañas: Resumen, Castración, Geografía, Municipio, Cuidado, Callejeros, Tabla.
- Carga opcional de un CSV propio desde el panel lateral.
- Descarga del CSV filtrado.
- Generación y descarga de **PDF resumen** (matplotlib backend Agg).

## 🧠 Detalles técnicos

- `matplotlib.use("Agg")` antes de cualquier import de pyplot → indispensable
  para correr en servidor sin display.
- `@st.cache_data` cachea la carga del CSV.
- El PDF se construye en memoria con `io.BytesIO` + `PdfPages`, no toca disco.
- No usa Tkinter ni subprocess: 100% compatible con sandbox de Streamlit Cloud.
