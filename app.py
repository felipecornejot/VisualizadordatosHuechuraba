from __future__ import annotations

import io
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from urllib.request import urlopen

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="SUSTREND | Visualizador territorial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BRAND = {
    "blue": "#0033A0",    # Brandbook SUSTREND
    "cyan": "#00A3E0",    # Brandbook SUSTREND
    "navy": "#001B5E",
    "deep": "#071B3B",
    "ice": "#EAF7FD",
    "mist": "#F5F9FC",
    "slate": "#5F7188",
    "line": "#D7E3EF",
    "white": "#FFFFFF",
    "success": "#0F8B5F",
    "warning": "#D97706",
    "danger": "#B42318",
    "neutral": "#8A94A6",
}

# Versión repo-first excluyendo las bases más pesadas.
DATA_FILES = {
    "Resumen comunal": "PUB_COMU.xlsb",
    "Empresas por género asociado al RUT": "PUB_GEN_COMU.xlsb",
    "Rubro económico": "PUB_COMU_RUBR.xlsb",
    "Tramo según trabajadores": "PUB_COMU_TRTRAB.xlsb",
    "Tramo ventas (13 y 5)": "PUB_TRAM_COMU.xlsb",
    "Tramo ventas (5)": "PUB_TRAM5_COMU.xlsb",
    "Tramo ventas (18, 13 y 5)": "PUB_TRINT_COMU.xlsb",
}

DISPLAY_NAME_OVERRIDES = {
    "Año Comercial": "Año",
    "Comuna del domicilio o casa matriz": "Comuna",
    "Provincia del domicilio o casa matriz": "Provincia",
    "Región del domicilio o casa matriz": "Región",
}

DEFAULT_DIMENSION_PRIORITY = [
    "Género asociado al RUT",
    "Rubro económico",
    "Tramo según trabajadores dependientes informados",
    "Tramo según ventas (18 tramos)",
    "Tramo según ventas (13 tramos)",
    "Tramo según ventas (5 tramos)",
]

DEFAULT_METRICS_PRIORITY = [
    "Número de empresas",
    "Ventas anuales en UF",
    "Número de trabajadores dependientes informados",
    "Renta neta informada en UF",
    "Trabajadores ponderados por meses trabajados",
    "Número de trabajadores a honorarios informados",
    "Honorarios pagados informados en UF",
]

METRIC_FORMAT_HINTS = {
    "Número de empresas": "count",
    "Ventas anuales en UF": "uf",
    "Número de trabajadores dependientes informados": "count",
    "Renta neta informada en UF": "uf",
    "Trabajadores ponderados por meses trabajados": "count",
    "Número de trabajadores a honorarios informados": "count",
    "Honorarios pagados informados en UF": "uf",
}

PLOTLY_SEQUENCE = [
    BRAND["blue"],
    BRAND["cyan"],
    BRAND["navy"],
    "#3C6FD1",
    "#5CC9F0",
    "#23407C",
    "#7D8FB3",
    "#90D9F5",
]


# =========================================================
# ESTILO
# =========================================================
def inject_css() -> None:
    st.markdown(
        f"""
        <style>
            :root {{
                --s-blue: {BRAND['blue']};
                --s-cyan: {BRAND['cyan']};
                --s-navy: {BRAND['navy']};
                --s-deep: {BRAND['deep']};
                --s-ice: {BRAND['ice']};
                --s-mist: {BRAND['mist']};
                --s-slate: {BRAND['slate']};
                --s-line: {BRAND['line']};
                --s-white: {BRAND['white']};
            }}

            .stApp {{
                background:
                    radial-gradient(circle at 10% 0%, rgba(0,163,224,.10), transparent 24%),
                    radial-gradient(circle at 100% 0%, rgba(0,51,160,.10), transparent 30%),
                    linear-gradient(180deg, #f7fbfe 0%, #f3f8fc 46%, #eff5fa 100%);
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, rgba(0,27,94,0.98) 0%, rgba(0,51,160,0.98) 60%, rgba(0,163,224,0.95) 100%);
                border-right: 1px solid rgba(255,255,255,0.08);
            }}

            [data-testid="stSidebar"] * {{
                color: white;
            }}

            .hero-shell {{
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, rgba(0,27,94,.98) 0%, rgba(0,51,160,.97) 52%, rgba(0,163,224,.92) 100%);
                border-radius: 28px;
                padding: 1.5rem 1.55rem 1.55rem 1.55rem;
                box-shadow: 0 24px 60px rgba(0,51,160,.18);
                color: white;
                margin-bottom: 1rem;
                border: 1px solid rgba(255,255,255,.10);
            }}

            .hero-shell:before {{
                content: "";
                position: absolute;
                width: 360px;
                height: 360px;
                right: -120px;
                top: -120px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(255,255,255,.22) 0%, rgba(255,255,255,0) 72%);
            }}

            .hero-eyebrow {{
                text-transform: uppercase;
                letter-spacing: .13em;
                font-size: .78rem;
                font-weight: 700;
                opacity: .84;
                margin-bottom: .45rem;
            }}

            .hero-title {{
                font-size: 2.25rem;
                line-height: 1.02;
                font-weight: 850;
                margin-bottom: .35rem;
                letter-spacing: -0.04em;
                color: white;
            }}

            .hero-subtitle {{
                font-size: 1rem;
                opacity: .97;
                margin-bottom: .65rem;
                max-width: 900px;
            }}

            .hero-chip {{
                display: inline-block;
                padding: .38rem .70rem;
                border-radius: 999px;
                background: rgba(255,255,255,.13);
                border: 1px solid rgba(255,255,255,.16);
                font-size: .82rem;
                margin-right: .35rem;
                margin-top: .25rem;
                color: white;
            }}

            .section-title {{
                font-size: 1.02rem;
                font-weight: 850;
                color: var(--s-blue);
                margin: .2rem 0 .7rem 0;
                letter-spacing: -.02em;
            }}

            .metric-card, .soft-card {{
                background: rgba(255,255,255,.96);
                border: 1px solid var(--s-line);
                border-radius: 18px;
                padding: 1rem 1rem .95rem 1rem;
                box-shadow: 0 14px 28px rgba(16,42,67,.06);
            }}

            .metric-label {{
                font-size: .83rem;
                color: var(--s-slate);
                margin-bottom: .3rem;
            }}

            .metric-value {{
                font-size: 1.75rem;
                line-height: 1.02;
                font-weight: 850;
                color: var(--s-blue);
                margin-bottom: .18rem;
                letter-spacing: -.02em;
            }}

            .metric-foot {{
                font-size: .81rem;
                color: var(--s-slate);
            }}

            .insight-box {{
                background: linear-gradient(180deg, rgba(255,255,255,.95), rgba(234,247,253,.88));
                border: 1px solid var(--s-line);
                border-left: 5px solid var(--s-cyan);
                border-radius: 16px;
                padding: 1rem 1rem;
                color: #334e68;
                margin-top: .8rem;
            }}

            .mini-kicker {{
                text-transform: uppercase;
                font-size: .72rem;
                letter-spacing: .10em;
                color: var(--s-cyan);
                font-weight: 800;
                margin-bottom: .25rem;
            }}

            .footer-note {{
                color: var(--s-slate);
                font-size: .82rem;
                margin-top: .75rem;
            }}

            .pill-note {{
                display: inline-block;
                padding: .28rem .55rem;
                border-radius: 999px;
                background: rgba(0,163,224,.08);
                color: var(--s-blue);
                border: 1px solid rgba(0,163,224,.16);
                font-size: .78rem;
                margin-right: .3rem;
                margin-top: .25rem;
            }}

            div[data-testid="metric-container"] {{
                background: white;
                border: 1px solid var(--s-line);
                padding: 10px 14px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(16,42,67,.05);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CARGA Y NORMALIZACIÓN
# =========================================================
@st.cache_data(show_spinner=False)
def resolve_binary_source(filename: str) -> bytes:
    search_roots = [
        Path(os.getenv("DATA_DIR", "data")),
        Path("."),
        Path("./data"),
        Path("./datasets"),
        Path("/mnt/data"),
    ]

    for root in search_roots:
        candidate = root / filename
        if candidate.exists():
            return candidate.read_bytes()

    base_url = os.getenv("DATA_BASE_URL", "").strip()
    if base_url:
        url = urljoin(base_url.rstrip("/") + "/", filename)
        with urlopen(url) as response:
            return response.read()

    raise FileNotFoundError(
        f"No se encontró '{filename}'. Súbelo a /data o define DATA_BASE_URL apuntando a tus archivos raw."
    )


@st.cache_data(show_spinner=False)
def load_logo_bytes() -> Optional[bytes]:
    candidates = [
        os.getenv("SUSTREND_LOGO", "").strip(),
        "assets/logo_sustrend.png",
        "assets/logo.png",
        "logo_sustrend.png",
        "LOGO_SUSTREND_HORIZONTAL[7939].png",
        "/mnt/data/LOGO_SUSTREND_HORIZONTAL[7939].png",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path.read_bytes()
        if candidate.startswith("http://") or candidate.startswith("https://"):
            with urlopen(candidate) as response:
                return response.read()
    return None


def clean_column_name(name: str) -> str:
    name = re.sub(r"\s+", " ", str(name)).strip()
    return DISPLAY_NAME_OVERRIDES.get(name, name)


def clean_text_value(value):
    if isinstance(value, str):
        value = re.sub(r"\s+", " ", value).strip()
    return value


@st.cache_data(show_spinner=False)
def load_dataset(dataset_label: str) -> pd.DataFrame:
    filename = DATA_FILES[dataset_label]
    file_bytes = resolve_binary_source(filename)
    buffer = io.BytesIO(file_bytes)

    df = pd.read_excel(
        buffer,
        sheet_name="Datos",
        engine="pyxlsb",
        skiprows=4,
    )

    df.columns = [clean_column_name(c) for c in df.columns]
    df = df.replace({"*": np.nan, "Sin info": np.nan, "SIN INFO": np.nan})

    for col in df.columns:
        df[col] = df[col].apply(clean_text_value)

    for col in df.columns:
        if col == "Año":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            continue

        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().mean() >= 0.8:
            df[col] = converted

    return df.dropna(how="all").copy()


@st.cache_data(show_spinner=False)
def get_dataset_meta(dataset_label: str) -> Dict[str, List[str]]:
    df = load_dataset(dataset_label)
    fixed_geo = {"Año", "Comuna", "Provincia", "Región"}
    dimensions: List[str] = []
    metrics: List[str] = []

    for col in df.columns:
        if col in fixed_geo:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            metrics.append(col)
        else:
            dimensions.append(col)

    ordered_dimensions = [
        d for d in DEFAULT_DIMENSION_PRIORITY if d in dimensions
    ] + [d for d in dimensions if d not in DEFAULT_DIMENSION_PRIORITY]

    ordered_metrics = [
        m for m in DEFAULT_METRICS_PRIORITY if m in metrics
    ] + [m for m in metrics if m not in DEFAULT_METRICS_PRIORITY]

    return {"dimensions": ordered_dimensions, "metrics": ordered_metrics}


# =========================================================
# UTILIDADES DE NEGOCIO
# =========================================================
def infer_metric_format(metric: str) -> str:
    for key, value in METRIC_FORMAT_HINTS.items():
        if key.lower() in metric.lower():
            return value
    metric_lower = metric.lower()
    if "uf" in metric_lower or "venta" in metric_lower or "honorario" in metric_lower or "renta" in metric_lower:
        return "uf"
    if "número" in metric_lower or "trabajador" in metric_lower or "empresa" in metric_lower:
        return "count"
    return "generic"


def human_format(value: float | int | None, decimals: int = 0, kind: str = "generic") -> str:
    if value is None or pd.isna(value):
        return "—"

    value = float(value)
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        base = f"{value/1_000_000_000:.{decimals}f}B"
    elif abs_val >= 1_000_000:
        base = f"{value/1_000_000:.{decimals}f}M"
    elif abs_val >= 1_000:
        base = f"{value/1_000:.{decimals}f}k"
    elif decimals == 0:
        base = f"{value:,.0f}".replace(",", ".")
    else:
        base = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if kind == "uf":
        return f"UF {base}"
    return base


def safe_delta(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None:
        return None
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current - previous) / previous


def calculate_cagr(series: pd.Series) -> Optional[float]:
    clean = series.dropna()
    if len(clean) < 2:
        return None
    first = clean.iloc[0]
    last = clean.iloc[-1]
    periods = len(clean) - 1
    if first <= 0 or periods <= 0:
        return None
    return (last / first) ** (1 / periods) - 1


def infer_default_region_index(regions: List[str]) -> int:
    for target in ["Región Metropolitana de Santiago", "Metropolitana de Santiago", "Todas"]:
        if target in regions:
            return regions.index(target)
    return 0


def infer_default_comuna_index(communes: List[str]) -> int:
    for target in ["Huechuraba", "Guachuraba", "Todas"]:
        if target in communes:
            return communes.index(target)
    return 0


def apply_filters(
    df: pd.DataFrame,
    years: Tuple[int, int],
    region: Optional[str],
    province: Optional[str],
    comuna: Optional[str],
    extra_filters: Dict[str, List[str]],
) -> pd.DataFrame:
    out = df.copy()

    if "Año" in out.columns:
        out = out[out["Año"].between(years[0], years[1], inclusive="both")]
    if region and region != "Todas" and "Región" in out.columns:
        out = out[out["Región"] == region]
    if province and province != "Todas" and "Provincia" in out.columns:
        out = out[out["Provincia"] == province]
    if comuna and comuna != "Todas" and "Comuna" in out.columns:
        out = out[out["Comuna"] == comuna]

    for col, values in extra_filters.items():
        if values and col in out.columns:
            out = out[out[col].isin(values)]

    return out


def aggregate_series(df: pd.DataFrame, group_col: str, metric: str) -> pd.DataFrame:
    if df.empty or group_col not in df.columns or metric not in df.columns:
        return pd.DataFrame(columns=[group_col, metric])
    return (
        df.groupby(group_col, dropna=False, as_index=False)[metric]
        .sum(min_count=1)
        .sort_values(group_col)
    )


def aggregate_table(df: pd.DataFrame, group_col: str, metric: str, top_n: int = 15) -> pd.DataFrame:
    if df.empty or group_col not in df.columns or metric not in df.columns:
        return pd.DataFrame(columns=[group_col, metric])
    out = (
        df.groupby(group_col, dropna=False, as_index=False)[metric]
        .sum(min_count=1)
        .sort_values(metric, ascending=False)
    )
    return out.head(top_n)


def compute_rank_table(df: pd.DataFrame, label_col: str, metric: str) -> pd.DataFrame:
    if df.empty:
        return df
    table = df.copy().reset_index(drop=True)
    total = table[metric].sum(min_count=1)
    table.insert(0, "Ranking", range(1, len(table) + 1))
    table[label_col] = table[label_col].fillna("Sin información")
    table["Participación %"] = np.nan if pd.isna(total) or total == 0 else (table[metric] / total) * 100
    return table


def get_latest_year(df: pd.DataFrame) -> Optional[int]:
    if "Año" not in df.columns or df["Año"].dropna().empty:
        return None
    return int(df["Año"].dropna().max())


def get_previous_year(df: pd.DataFrame) -> Optional[int]:
    if "Año" not in df.columns:
        return None
    years = sorted(df["Año"].dropna().unique())
    return int(years[-2]) if len(years) >= 2 else None


def build_executive_insight(df_filtered: pd.DataFrame, metric: str, composition_dim: str) -> str:
    if df_filtered.empty:
        return "La selección actual no contiene registros para construir una lectura ejecutiva."

    metric_kind = infer_metric_format(metric)
    ts = aggregate_series(df_filtered, "Año", metric)
    latest_year = get_latest_year(df_filtered)
    previous_year = get_previous_year(df_filtered)

    current = ts[metric].iloc[-1] if not ts.empty else None
    previous = ts[metric].iloc[-2] if len(ts) >= 2 else None
    delta = safe_delta(current, previous)
    cagr = calculate_cagr(ts[metric]) if not ts.empty else None

    text = f"En la selección activa, **{metric}** alcanza **{human_format(current, 1, metric_kind)}**"
    if latest_year is not None:
        text += f" en **{latest_year}**"

    if delta is not None and previous_year is not None:
        sign = "crece" if delta >= 0 else "retrocede"
        text += f", y **{sign} {abs(delta)*100:.1f}%** frente a **{previous_year}**"

    if cagr is not None and len(ts) >= 3:
        text += f". En la trayectoria observada, la tasa media anual estimada es de **{cagr*100:.1f}%**"
    else:
        text += "."

    if composition_dim in df_filtered.columns and latest_year is not None:
        latest_df = df_filtered[df_filtered["Año"] == latest_year]
        top_df = aggregate_table(latest_df, composition_dim, metric, top_n=2)
        if len(top_df) >= 1:
            leader = top_df.iloc[0][composition_dim]
            leader_value = top_df.iloc[0][metric]
            text += f" El principal aporte proviene de **{leader}**, con **{human_format(leader_value, 1, metric_kind)}**"
        if len(top_df) >= 2:
            runner = top_df.iloc[1][composition_dim]
            text += f", seguido por **{runner}**"
        text += "."

    return text


def build_signal_summary(df_filtered: pd.DataFrame, metric: str, composition_dim: str) -> List[str]:
    signals: List[str] = []
    metric_kind = infer_metric_format(metric)
    ts = aggregate_series(df_filtered, "Año", metric)
    latest_year = get_latest_year(df_filtered)

    if not ts.empty:
        peak_row = ts.sort_values(metric, ascending=False).head(1)
        if not peak_row.empty:
            peak_year = int(peak_row.iloc[0]["Año"])
            peak_value = peak_row.iloc[0][metric]
            signals.append(f"Máximo observado: {human_format(peak_value, 1, metric_kind)} en {peak_year}.")

    if latest_year is not None and composition_dim in df_filtered.columns:
        latest_df = df_filtered[df_filtered["Año"] == latest_year]
        rank = aggregate_table(latest_df, composition_dim, metric, top_n=3)
        if not rank.empty:
            pieces = []
            total = rank[metric].sum(min_count=1)
            for _, row in rank.iterrows():
                label = row[composition_dim] if pd.notna(row[composition_dim]) else "Sin información"
                part = (row[metric] / total * 100) if total and pd.notna(total) else np.nan
                if pd.notna(part):
                    pieces.append(f"{label} ({part:.1f}%)")
                else:
                    pieces.append(str(label))
            signals.append("Concentración principal: " + ", ".join(pieces) + ".")

    if len(df_filtered) > 0:
        signals.append(f"Cobertura activa: {len(df_filtered):,} registros filtrados.".replace(",", "."))

    return signals


# =========================================================
# CHARTS
# =========================================================
def base_layout(title: str, height: int = 430) -> Dict:
    return dict(
        title=title,
        height=height,
        margin=dict(l=20, r=20, t=64, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.92)",
        title_font=dict(size=20, color=BRAND["blue"]),
        legend_title="",
    )


def apply_fig_style(fig: go.Figure, title: str, height: int = 430) -> go.Figure:
    fig.update_layout(**base_layout(title, height))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,51,160,0.08)", zeroline=False)
    return fig


def build_line_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.line(df, x=x, y=y, markers=True, template="plotly_white")
    fig.update_traces(line=dict(color=BRAND["blue"], width=3), marker=dict(size=7, color=BRAND["cyan"]))
    fig.update_layout(hovermode="x unified")
    return apply_fig_style(fig, title, 430)


def build_bar_chart(df: pd.DataFrame, x: str, y: str, title: str, horizontal: bool = False) -> go.Figure:
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h", template="plotly_white")
    else:
        fig = px.bar(df, x=x, y=y, template="plotly_white")
    fig.update_traces(marker_color=BRAND["cyan"], marker_line_color=BRAND["blue"], marker_line_width=1)
    return apply_fig_style(fig, title, 470)


def build_area_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> go.Figure:
    fig = px.area(df, x=x, y=y, color=color, template="plotly_white", color_discrete_sequence=PLOTLY_SEQUENCE)
    return apply_fig_style(fig, title, 470)


def build_comparison_chart(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    fig = px.line(df, x="Año", y=metric, color="Territorio", markers=True, template="plotly_white", color_discrete_sequence=PLOTLY_SEQUENCE)
    fig.update_layout(hovermode="x unified")
    return apply_fig_style(fig, title, 480)


def build_share_heatmap(df: pd.DataFrame, metric: str, composition_dim: str, title: str) -> go.Figure:
    heat_df = df.pivot(index=composition_dim, columns="Año", values=metric).fillna(0)
    fig = go.Figure(
        data=go.Heatmap(
            z=heat_df.values,
            x=list(heat_df.columns),
            y=list(heat_df.index),
            colorscale=[[0, BRAND["ice"]], [0.45, BRAND["cyan"]], [1, BRAND["blue"]]],
            hoverongaps=False,
        )
    )
    return apply_fig_style(fig, title, 500)


# =========================================================
# SIDEBAR
# =========================================================
def sidebar_controls(dataset_label: str) -> Dict[str, object]:
    df = load_dataset(dataset_label)
    meta = get_dataset_meta(dataset_label)

    years_list = sorted([int(y) for y in df["Año"].dropna().unique().tolist()]) if "Año" in df.columns else []
    if years_list:
        years = st.sidebar.select_slider("Rango de años", options=years_list, value=(years_list[0], years_list[-1]))
    else:
        years = (0, 0)

    regions = ["Todas"]
    if "Región" in df.columns:
        regions += sorted([str(v) for v in df["Región"].dropna().unique().tolist()])
    region = st.sidebar.selectbox("Región", regions, index=infer_default_region_index(regions))

    province_options = ["Todas"]
    if "Provincia" in df.columns:
        province_base = df.copy()
        if region != "Todas" and "Región" in province_base.columns:
            province_base = province_base[province_base["Región"] == region]
        province_options += sorted([str(v) for v in province_base["Provincia"].dropna().unique().tolist()])
    province = st.sidebar.selectbox("Provincia", province_options, index=0)

    commune_options = ["Todas"]
    if "Comuna" in df.columns:
        commune_base = df.copy()
        if region != "Todas" and "Región" in commune_base.columns:
            commune_base = commune_base[commune_base["Región"] == region]
        if province != "Todas" and "Provincia" in commune_base.columns:
            commune_base = commune_base[commune_base["Provincia"] == province]
        commune_options += sorted([str(v) for v in commune_base["Comuna"].dropna().unique().tolist()])
    comuna = st.sidebar.selectbox("Comuna", commune_options, index=infer_default_comuna_index(commune_options))

    metric = st.sidebar.selectbox("Métrica principal", meta["metrics"], index=0 if meta["metrics"] else None)
    composition_dim = st.sidebar.selectbox("Dimensión de composición", meta["dimensions"], index=0 if meta["dimensions"] else None)
    compare_scope = st.sidebar.radio("Comparación", ["Comuna vs región", "Comuna vs país"], index=0)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filtros avanzados")

    extra_filters: Dict[str, List[str]] = {}
    if meta["dimensions"]:
        default_multiselect_dims = meta["dimensions"][: min(3, len(meta["dimensions"]))]
        selected_filter_dims = st.sidebar.multiselect(
            "Activar filtros por dimensión",
            options=meta["dimensions"],
            default=default_multiselect_dims,
        )
        for col in selected_filter_dims:
            values = df[col].dropna().unique().tolist()
            values = [v for v in values if str(v).strip() != ""]
            selected = st.sidebar.multiselect(col, options=sorted(values), default=[])
            if selected:
                extra_filters[col] = selected

    st.sidebar.markdown("---")
    st.sidebar.caption("Versión premium repo-first. Bases pesadas excluidas para despliegue más estable en GitHub + Streamlit Cloud.")

    return {
        "years": years,
        "region": region,
        "province": province,
        "comuna": comuna,
        "metric": metric,
        "composition_dim": composition_dim,
        "compare_scope": compare_scope,
        "extra_filters": extra_filters,
    }


# =========================================================
# UI COMPONENTS
# =========================================================
def render_metric_card(label: str, value: str, foot: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(dataset_label: str, controls: Dict[str, object], df_filtered: pd.DataFrame) -> None:
    logo_bytes = load_logo_bytes()

    col_logo, col_main = st.columns([1.2, 5.3])
    with col_logo:
        if logo_bytes:
            st.image(logo_bytes, use_container_width=True)

    with col_main:
        st.markdown(
            f"""
            <div class="hero-shell">
                <div class="hero-eyebrow">SUSTREND · visual analytics</div>
                <div class="hero-title">Visualizador territorial premium</div>
                <div class="hero-subtitle">
                    Exploración comunal con lectura ejecutiva, comparación territorial, filtros dinámicos y diseño preparado para despliegue directo desde GitHub hacia Streamlit Cloud.
                </div>
                <span class="hero-chip">Base: {dataset_label}</span>
                <span class="hero-chip">Comuna: {controls['comuna']}</span>
                <span class="hero-chip">Métrica: {controls['metric']}</span>
                <span class="hero-chip">Periodo: {controls['years'][0]}–{controls['years'][1]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    metric = controls["metric"]
    metric_kind = infer_metric_format(metric)
    ts = aggregate_series(df_filtered, "Año", metric)
    current = ts[metric].iloc[-1] if len(ts) >= 1 else None
    previous = ts[metric].iloc[-2] if len(ts) >= 2 else None
    delta = safe_delta(current, previous)
    latest_year = get_latest_year(df_filtered)
    rows = len(df_filtered)
    years_count = ts["Año"].nunique() if not ts.empty else 0
    cagr = calculate_cagr(ts[metric]) if not ts.empty else None

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card(metric, human_format(current, 1, metric_kind), f"Último año disponible: {latest_year if latest_year is not None else '—'}")
    with c2:
        render_metric_card("Variación interanual", f"{delta*100:+.1f}%" if delta is not None else "—", "Comparada con el año previo" if delta is not None else "Sin base comparable")
    with c3:
        render_metric_card("Tasa media anual", f"{cagr*100:.1f}%" if cagr is not None else "—", "Estimación CAGR sobre la serie" if cagr is not None else "Serie insuficiente")
    with c4:
        render_metric_card("Observaciones activas", human_format(rows), "Registros tras aplicar filtros")
    with c5:
        render_metric_card("Cobertura temporal", human_format(years_count), "Años distintos en la selección")


# =========================================================
# TABS
# =========================================================
def render_summary_tab(df_filtered: pd.DataFrame, metric: str, composition_dim: str) -> None:
    st.markdown('<div class="section-title">Lectura ejecutiva</div>', unsafe_allow_html=True)

    left, right = st.columns([1.7, 1.0])
    with left:
        ts = aggregate_series(df_filtered, "Año", metric)
        st.plotly_chart(build_line_chart(ts, "Año", metric, f"Evolución temporal de {metric}"), use_container_width=True)

    with right:
        latest_year = get_latest_year(df_filtered)
        latest_df = df_filtered[df_filtered["Año"] == latest_year] if latest_year is not None else df_filtered.copy()
        rank = aggregate_table(latest_df, composition_dim, metric, top_n=10)
        st.plotly_chart(
            build_bar_chart(rank.sort_values(metric), composition_dim, metric, f"Top 10 por {composition_dim} ({latest_year if latest_year is not None else 'selección'})", horizontal=True),
            use_container_width=True,
        )

    insight = build_executive_insight(df_filtered, metric, composition_dim)
    st.markdown(f'<div class="insight-box"><div class="mini-kicker">Insight automático</div>{insight}</div>', unsafe_allow_html=True)

    signals = build_signal_summary(df_filtered, metric, composition_dim)
    if signals:
        st.markdown('<div class="section-title">Señales clave</div>', unsafe_allow_html=True)
        cols = st.columns(len(signals))
        for idx, signal in enumerate(signals):
            with cols[idx]:
                st.markdown(f'<div class="soft-card">{signal}</div>', unsafe_allow_html=True)


def render_timeseries_tab(df_filtered: pd.DataFrame, metric: str, composition_dim: str) -> None:
    st.markdown('<div class="section-title">Evolución temporal y trayectoria</div>', unsafe_allow_html=True)

    ts = aggregate_series(df_filtered, "Año", metric)
    st.plotly_chart(build_line_chart(ts, "Año", metric, f"Serie histórica de {metric}"), use_container_width=True)

    if composition_dim and composition_dim in df_filtered.columns:
        top_labels = (
            df_filtered.groupby(composition_dim, as_index=False)[metric]
            .sum(min_count=1)
            .sort_values(metric, ascending=False)
            .head(6)[composition_dim]
            .tolist()
        )
        by_dim = (
            df_filtered[df_filtered[composition_dim].isin(top_labels)]
            .groupby(["Año", composition_dim], as_index=False)[metric]
            .sum(min_count=1)
        )
        if not by_dim.empty:
            fig = px.line(by_dim, x="Año", y=metric, color=composition_dim, markers=True, template="plotly_white", color_discrete_sequence=PLOTLY_SEQUENCE)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(apply_fig_style(fig, f"Trayectoria por {composition_dim} (Top 6)", 500), use_container_width=True)


def render_composition_tab(df_filtered: pd.DataFrame, metric: str, composition_dim: str) -> None:
    st.markdown('<div class="section-title">Estructura y composición</div>', unsafe_allow_html=True)

    latest_year = get_latest_year(df_filtered)
    current_df = df_filtered[df_filtered["Año"] == latest_year] if latest_year is not None else df_filtered.copy()
    top_comp = aggregate_table(current_df, composition_dim, metric, top_n=15)
    rank_table = compute_rank_table(top_comp, composition_dim, metric)
    metric_kind = infer_metric_format(metric)

    left, right = st.columns([1.2, 1.0])
    with left:
        st.plotly_chart(build_bar_chart(top_comp.sort_values(metric), composition_dim, metric, f"Ranking por {composition_dim}", horizontal=True), use_container_width=True)
    with right:
        if not top_comp.empty:
            pie_df = top_comp.head(8).copy()
            fig = px.pie(pie_df, names=composition_dim, values=metric, hole=0.58, color_discrete_sequence=PLOTLY_SEQUENCE)
            st.plotly_chart(apply_fig_style(fig, f"Participación relativa ({latest_year if latest_year is not None else 'selección'})", 450), use_container_width=True)

    st.dataframe(
        rank_table.style.format({metric: lambda v: human_format(v, 1, metric_kind), "Participación %": "{:.2f}%"}),
        use_container_width=True,
        hide_index=True,
    )

    if composition_dim in df_filtered.columns and "Año" in df_filtered.columns and not rank_table.empty:
        top_labels = rank_table[composition_dim].head(6).tolist()
        share_df = (
            df_filtered[df_filtered[composition_dim].isin(top_labels)]
            .groupby(["Año", composition_dim], as_index=False)[metric]
            .sum(min_count=1)
        )
        if not share_df.empty:
            st.plotly_chart(build_area_chart(share_df, "Año", metric, composition_dim, f"Evolución por {composition_dim} (Top 6)"), use_container_width=True)
            latest_top = share_df[share_df["Año"] == share_df["Año"].max()].copy()
            if not latest_top.empty:
                st.plotly_chart(build_share_heatmap(share_df, metric, composition_dim, f"Mapa de intensidad por {composition_dim}"), use_container_width=True)


def render_compare_tab(dataset_label: str, controls: Dict[str, object]) -> None:
    st.markdown('<div class="section-title">Benchmark territorial</div>', unsafe_allow_html=True)

    df_all = load_dataset(dataset_label)
    metric = controls["metric"]
    comuna = controls["comuna"]
    years = controls["years"]
    extra_filters = controls["extra_filters"]
    metric_kind = infer_metric_format(metric)

    if comuna == "Todas":
        st.info("Selecciona una comuna específica para activar esta comparación.")
        return

    commune_df = apply_filters(df_all, years, None, None, comuna, extra_filters)
    if commune_df.empty:
        st.warning("No hay registros para la comuna seleccionada bajo los filtros actuales.")
        return

    region_name = None
    if "Región" in commune_df.columns and not commune_df["Región"].dropna().empty:
        region_name = commune_df["Región"].dropna().iloc[0]

    region_df = apply_filters(df_all, years, region_name, None, "Todas", extra_filters)
    country_df = apply_filters(df_all, years, None, None, "Todas", extra_filters)

    commune_series = aggregate_series(commune_df, "Año", metric).rename(columns={metric: comuna})
    region_series = aggregate_series(region_df, "Año", metric).rename(columns={metric: region_name or "Región"})
    country_series = aggregate_series(country_df, "Año", metric).rename(columns={metric: "Chile"})

    if controls["compare_scope"] == "Comuna vs región":
        merged = commune_series.merge(region_series, on="Año", how="outer")
        value_vars = [comuna, region_name or "Región"]
    else:
        merged = commune_series.merge(country_series, on="Año", how="outer")
        value_vars = [comuna, "Chile"]

    long_df = merged.melt(id_vars="Año", value_vars=value_vars, var_name="Territorio", value_name=metric)
    st.plotly_chart(build_comparison_chart(long_df, metric, f"Comparación territorial de {metric}"), use_container_width=True)

    latest_year = get_latest_year(long_df)
    if latest_year is not None:
        latest_df = long_df[long_df["Año"] == latest_year].sort_values(metric, ascending=False).copy()
        latest_df["Valor formateado"] = latest_df[metric].apply(lambda v: human_format(v, 1, metric_kind))
        st.dataframe(latest_df[["Territorio", "Año", "Valor formateado", metric]], use_container_width=True, hide_index=True)


def render_quality_tab(df_filtered: pd.DataFrame, dataset_label: str, controls: Dict[str, object]) -> None:
    st.markdown('<div class="section-title">Calidad de datos y exportación</div>', unsafe_allow_html=True)

    metric = controls["metric"]
    metric_kind = infer_metric_format(metric)
    null_share = float(df_filtered[metric].isna().mean() * 100) if metric in df_filtered.columns and len(df_filtered) else 0.0
    latest_year = get_latest_year(df_filtered)
    previous_year = get_previous_year(df_filtered)

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        render_metric_card("Columnas", human_format(len(df_filtered.columns)), "Variables disponibles")
    with q2:
        render_metric_card("Filas", human_format(len(df_filtered)), "Registros tras filtros")
    with q3:
        render_metric_card("Nulos en métrica", f"{null_share:.1f}%", metric)
    with q4:
        span_text = f"{previous_year}–{latest_year}" if latest_year is not None else "—"
        render_metric_card("Ventana observada", span_text, "Años comparables recientes")

    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8-sig")
    export_name = f"sustrend_{dataset_label.lower().replace(' ', '_')}.csv"
    st.download_button("Descargar selección en CSV", data=csv_bytes, file_name=export_name, mime="text/csv")

    numeric_preview = df_filtered.select_dtypes(include=[np.number]).copy()
    if not numeric_preview.empty:
        desc = numeric_preview.describe().T.reset_index().rename(columns={"index": "Variable"})
        for col in ["mean", "std", "min", "50%", "max"]:
            if col in desc.columns:
                desc[col] = desc[col].apply(lambda v: human_format(v, 1, metric_kind if col == "mean" else "generic"))
        st.markdown('<div class="section-title">Resumen estadístico rápido</div>', unsafe_allow_html=True)
        st.dataframe(desc, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Vista de tabla</div>', unsafe_allow_html=True)
    st.dataframe(df_filtered, use_container_width=True, height=560, hide_index=True)


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    inject_css()

    st.sidebar.markdown("# SUSTREND")
    st.sidebar.markdown("Visualizador territorial premium")

    dataset_label = st.sidebar.selectbox("Base de datos", list(DATA_FILES.keys()), index=0)

    try:
        controls = sidebar_controls(dataset_label)
        df = load_dataset(dataset_label)
    except Exception as exc:
        st.error(f"No fue posible cargar la base seleccionada: {exc}")
        st.stop()

    df_filtered = apply_filters(
        df=df,
        years=controls["years"],
        region=controls["region"],
        province=controls["province"],
        comuna=controls["comuna"],
        extra_filters=controls["extra_filters"],
    )

    render_header(dataset_label, controls, df_filtered)

    if df_filtered.empty:
        st.warning("La combinación de filtros no devuelve registros. Ajusta años, territorio o filtros avanzados.")
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Resumen ejecutivo",
        "Evolución temporal",
        "Composición",
        "Benchmark",
        "Calidad y datos",
    ])

    with tab1:
        render_summary_tab(df_filtered, controls["metric"], controls["composition_dim"])
    with tab2:
        render_timeseries_tab(df_filtered, controls["metric"], controls["composition_dim"])
    with tab3:
        render_composition_tab(df_filtered, controls["metric"], controls["composition_dim"])
    with tab4:
        render_compare_tab(dataset_label, controls)
    with tab5:
        render_quality_tab(df_filtered, dataset_label, controls)

    st.markdown(
        """
        <div class="footer-note">
            Implementación recomendada: mantener este archivo como <b>app.py</b>, las bases en <b>/data</b> y el logo en <b>/assets/logo_sustrend.png</b>.
            Si no deseas guardar binarios en el repositorio, puedes usar <b>DATA_BASE_URL</b> apuntando a los archivos raw de GitHub.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
