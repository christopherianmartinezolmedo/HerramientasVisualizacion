"""Ejecuta el análisis del tablero fuera de Streamlit y guarda todo en resultados/."""
import os, sys, types
from datetime import date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import dashboard_banxico_lib as lib

OUT = "resultados"
os.makedirs(OUT, exist_ok=True)
ini, fin = "2023-01-01", date.today().isoformat()
token = lib.token()
fuente = "Banxico SIE (reales)" if token else "SINTÉTICOS (sin token)"
resumen = []
for clave, nombre in lib.SERIES.items():
    s = lib.descargar(clave, ini, fin, token) if token else lib.datos_demo(clave, ini, fin)
    s.rename("dato").to_csv(f"{OUT}/{clave}.csv")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(s.index, s, color=lib.GRIS, label="Observado")
    ax.plot(s.index, s.rolling(30).mean(), color=lib.AZUL, lw=2, label="Media móvil 30d")
    ax.axhline(s.mean(), color=lib.ROJO, ls="--", lw=1, label="Promedio")
    ax.set_title(f"{nombre} — {fuente}"); ax.legend()
    fig.savefig(f"{OUT}/{clave}_serie.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    sns.histplot(s, bins=30, color=lib.AZUL_POS, ax=ax); ax.set_title(f"Distribución {clave}")
    fig.savefig(f"{OUT}/{clave}_hist.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    resumen.append({"serie": clave, "nombre": nombre, "fuente": fuente, "n": len(s),
                    "ultimo": s.iloc[-1], "max": s.max(), "min": s.min(), "promedio": s.mean()})
pd.DataFrame(resumen).to_csv(f"{OUT}/resumen.csv", index=False)
print(pd.DataFrame(resumen).to_string())
