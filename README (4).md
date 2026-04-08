# SUSTREND | Visualizador territorial premium

Aplicación en Streamlit para explorar estadísticas comunales con una capa visual más ejecutiva, filtros dinámicos y arquitectura pensada para **GitHub + Streamlit Cloud**.

La versión actual está optimizada para despliegue estable y por eso **excluye deliberadamente** las bases más pesadas:

- `PUB_COMU_SUBR.xlsb`
- `PUB_COMU_ACT.xlsb`

La interfaz y la paleta se alinean con el brandbook de SUSTREND, usando como base los colores corporativos digitales `#0033A0` y `#00A3E0` y la lógica visual del logo horizontal. fileciteturn0file0

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

## 3. Qué trae esta versión premium

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

## 9. Recomendaciones prácticas para GitHub

Para que Streamlit Cloud funcione fluido:

- mantén solo estas 7 bases en esta primera fase;
- deja fuera `PUB_COMU_SUBR.xlsb` y `PUB_COMU_ACT.xlsb`;
- evita nombres de archivo distintos a los definidos en `app.py`;
- usa `assets/logo_sustrend.png` para no depender de rutas locales;
- si luego crece el proyecto, conviene separar datos pesados a almacenamiento externo o preprocesarlos.

---

## 10. Próximo nivel sugerido

Si quieres llevarlo todavía más arriba, el siguiente paso lógico sería:

- crear una portada narrativa específica para **Huechuraba**;
- incorporar glosario de variables y fichas metodológicas;
- sumar comparaciones automáticas con comunas benchmark;
- construir una versión multi-página con secciones tipo informe ejecutivo.
