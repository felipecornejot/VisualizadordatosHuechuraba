# SUSTREND | Visualizador territorial

---

## 1. Bases consideradas

Sube estos archivos al repositorio dentro de `data/`:

- `PUB_COMU.xlsb`
- `PUB_GEN_COMU.xlsb`
- `PUB_COMU_RUBR.xlsb`
- `PUB_COMU_TRTRAB.xlsb`
- `PUB_TRAM_COMU.xlsb`
- `PUB_TRAM5_COMU.xlsb`
- `PUB_TRINT_COMU.xlsb`

---

## 2. Estructura recomendada del repo

```text
tu-repo/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── PUB_COMU.xlsb
│   ├── PUB_GEN_COMU.xlsb
│   ├── PUB_COMU_RUBR.xlsb
│   ├── PUB_COMU_TRTRAB.xlsb
│   ├── PUB_TRAM_COMU.xlsb
│   ├── PUB_TRAM5_COMU.xlsb
│   └── PUB_TRINT_COMU.xlsb
└── assets/
    └── logo_sustrend.png
```

---

## 3. Qué trae esta versión

### Diseño y experiencia
- hero principal más corporativo;
- tarjetas KPI con mejor jerarquía visual;
- línea gráfica más cercana a dashboard ejecutivo;
- mejor uso de contraste, espaciado y lectura en Streamlit Cloud.

### Analítica
- lectura ejecutiva automática;
- KPIs de último valor, variación interanual, CAGR, cobertura temporal y volumen filtrado;
- evolución temporal por métrica;
- composición por dimensión con ranking, torta y área acumulada;
- benchmark comuna vs región o comuna vs país;
- mapa de intensidad por dimensión;
- resumen rápido de calidad de datos y exportación CSV.

### Arquitectura técnica
- enfoque **repo-first**;
- fallback opcional vía `DATA_BASE_URL`;
- lectura de `.xlsb` con `pyxlsb`;
- limpieza automática de encabezados y conversión numérica robusta;
- caché con `st.cache_data` para mejorar rendimiento.

---

## 4. Instalación local

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 5. Despliegue en Streamlit Cloud

1. Sube este proyecto a GitHub.
2. Verifica que `app.py` esté en la raíz.
3. Verifica que `requirements.txt` esté en la raíz.
4. En Streamlit Cloud, conecta el repositorio.
5. Selecciona la rama y como archivo principal `app.py`.

---

## 6. Lógica de carga de archivos

La app busca los archivos en este orden:

1. `data/`
2. raíz del repo
3. `datasets/`
4. variable de entorno `DATA_BASE_URL`

### Ejemplo de respaldo con GitHub raw

```bash
DATA_BASE_URL=https://raw.githubusercontent.com/USUARIO/REPO/main/data/
```

Eso permite dos escenarios:

### Escenario A · Todo dentro del repo
La app lee directamente desde `data/`.

### Escenario B · Archivos servidos por URL
La app descarga los `.xlsb` desde la URL raw si definiste `DATA_BASE_URL`.

---

## 7. Logo

La app intenta cargar el logo en este orden:

- `assets/logo_sustrend.png`
- `assets/logo.png`
- `logo_sustrend.png`

Recomendación:

```text
assets/logo_sustrend.png
```

---

## 8. Variables normalizadas automáticamente

La app estandariza estos encabezados:

- `Año Comercial` → `Año`
- `Comuna del domicilio o casa matriz` → `Comuna`
- `Provincia del domicilio o casa matriz` → `Provincia`
- `Región del domicilio o casa matriz` → `Región`

Además:
- `*`, `Sin info` y `SIN INFO` se transforman en nulos;
- las columnas con alta consistencia numérica se convierten automáticamente a formato numérico.

---
