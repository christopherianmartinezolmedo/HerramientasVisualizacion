# Tablero del SIE de Banxico, con token
# Herramientas de Visualización · IDIA224 · Unidad III
#
#     pip install -r requirements.txt
#     streamlit run dashboard_banxico.py
#
# EL TOKEN NO VA EN ESTE ARCHIVO.
# En tu equipo: crea la carpeta .streamlit y dentro un archivo secrets.toml
# con una sola línea:
#     banxico_token = "pega-aqui-tu-token"
# Al publicar: pega esa misma línea en la sección de secretos de la app.
# El archivo secrets.toml nunca se sube al repositorio.

import os
from datetime import date, datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
import streamlit as st

# ─── Paleta del curso ──────────────────────────────────────────────────
GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"
AZUL_POS = "#2166AC"
CUALI = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]
sns.set_theme(style="whitegrid")

SIE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"

st.set_page_config(page_title="Tablero del SIE", layout="wide")



# ─── Catálogo de series ────────────────────────────────────────────────
SERIES = {
    "SF43718": "Tipo de cambio FIX (MXN/USD)",
    "SF61745": "Tasa objetivo de Banxico (%)",
    "SP68257": "UDIS (valor en pesos)",
    "SF43783": "TIIE a 28 días (%)",
}


def obtener_token():
    """Lee el token de secrets.toml o de la variable de entorno."""
    try:
        if "banxico_token" in st.secrets:
            return st.secrets["banxico_token"]
    except Exception:
        pass
    return os.environ.get("BANXICO_TOKEN")


@st.cache_data(ttl=3600, show_spinner="Consultando el SIE...")
def descargar(serie, ini, fin, token):
    url = f"{SIE}/{serie}/datos/{ini}/{fin}"
    r = requests.get(url, headers={"Bmx-Token": token}, timeout=30)
    r.raise_for_status()
    datos = r.json()["bmx"]["series"][0].get("datos", [])
    df = pd.DataFrame(datos)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df["dato"] = pd.to_numeric(df["dato"].str.replace(",", ""), errors="coerce")
    return df.dropna().set_index("fecha")["dato"]


def datos_demo(serie, ini, fin):
    """Datos SINTÉTICOS para probar el tablero sin token (no son reales)."""
    import numpy as np
    idx = pd.bdate_range(ini, fin)
    rng = np.random.default_rng(abs(hash(serie)) % 2**32)
    base = {"SF43718": 18, "SF61745": 10, "SP68257": 7.5, "SF43783": 10.2}[serie]
    return pd.Series(base + rng.normal(0, 0.02, len(idx)).cumsum(), index=idx)


# ─── Barra lateral ─────────────────────────────────────────────────────
st.title("Tablero del SIE de Banxico")
token = obtener_token()
with st.sidebar:
    st.header("Parámetros")
    clave = st.selectbox("Serie", list(SERIES), format_func=lambda k: f"{k} · {SERIES[k]}")
    ini = st.date_input("Desde", date(2023, 1, 1))
    fin = st.date_input("Hasta", date.today())
    ventana = st.slider("Media móvil (días)", 5, 120, 30)

if token:
    try:
        serie = descargar(clave, ini.isoformat(), fin.isoformat(), token)
    except Exception as e:
        st.error(f"No se pudo consultar el SIE: {e}")
        st.stop()
else:
    st.warning("No se encontró token de Banxico: se muestran datos SINTÉTICOS de demostración.")
    serie = datos_demo(clave, ini, fin)

if serie.empty:
    st.info("Sin datos para el rango elegido.")
    st.stop()

# ─── Indicadores ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Último dato", f"{serie.iloc[-1]:.4f}", f"{serie.iloc[-1] - serie.iloc[0]:+.4f} vs inicio")
c2.metric("Máximo", f"{serie.max():.4f}")
c3.metric("Mínimo", f"{serie.min():.4f}")
c4.metric("Promedio", f"{serie.mean():.4f}")

# ─── Gráficas ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(serie.index, serie, color=GRIS, label="Observado")
ax.plot(serie.index, serie.rolling(ventana).mean(), color=AZUL, lw=2, label=f"Media móvil {ventana}d")
ax.axhline(serie.mean(), color=ROJO, ls="--", lw=1, label="Promedio")
ax.set_title(SERIES[clave])
ax.legend()
st.pyplot(fig)

col_a, col_b = st.columns(2)
with col_a:
    fig2, ax2 = plt.subplots(figsize=(5, 3.5))
    sns.histplot(serie, bins=30, color=AZUL_POS, ax=ax2)
    ax2.set_title("Distribución")
    st.pyplot(fig2)
with col_b:
    mensual = serie.resample("ME").last()
    fig3, ax3 = plt.subplots(figsize=(5, 3.5))
    cambio = mensual.pct_change().dropna() * 100
    ax3.bar(cambio.index, cambio, width=20, color=[AZUL_POS if v >= 0 else ROJO for v in cambio])
    ax3.set_title("Cambio mensual (%)")
    fig3.autofmt_xdate()
    st.pyplot(fig3)

with st.expander("Ver datos"):
    st.dataframe(serie.rename("dato"))
    st.download_button("Descargar CSV", serie.to_csv().encode(), f"{clave}.csv", "text/csv")
