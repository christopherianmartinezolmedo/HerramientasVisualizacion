"""Lógica de datos sin interfaz (para generar_resultados.py)."""
import os
import numpy as np
import pandas as pd
import requests

GRIS, AZUL, ROJO, AZUL_POS = "#B9C3D1", "#1C4C9A", "#B2182B", "#2166AC"
SIE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
SERIES = {
    "SF43718": "Tipo de cambio FIX (MXN/USD)",
    "SF61745": "Tasa objetivo de Banxico (%)",
    "SP68257": "UDIS (valor en pesos)",
    "SF43783": "TIIE a 28 días (%)",
}
BASES = {"SF43718": 18, "SF61745": 10, "SP68257": 7.5, "SF43783": 10.2}

def token():
    return os.environ.get("BANXICO_TOKEN")

def descargar(serie, ini, fin, tk):
    r = requests.get(f"{SIE}/{serie}/datos/{ini}/{fin}", headers={"Bmx-Token": tk}, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["bmx"]["series"][0].get("datos", []))
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df["dato"] = pd.to_numeric(df["dato"].str.replace(",", ""), errors="coerce")
    return df.dropna().set_index("fecha")["dato"]

def datos_demo(serie, ini, fin):
    idx = pd.bdate_range(ini, fin)
    rng = np.random.default_rng(list(SERIES).index(serie))
    return pd.Series(BASES[serie] + rng.normal(0, 0.02, len(idx)).cumsum(), index=idx)
