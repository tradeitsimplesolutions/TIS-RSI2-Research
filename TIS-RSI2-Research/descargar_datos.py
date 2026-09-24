"""
Descarga el histórico diario de QQQ (ETF del Nasdaq 100) desde Yahoo Finance y lo guarda en data/QQQ_D1.csv.

Precios ajustados por dividendos y splits (auto_adjust=True), que es lo más parecido a una serie
de retorno total. Es el dataset con el que se generaron todas las cifras y gráficos de la guía.

Uso:  python descargar_datos.py
"""
from pathlib import Path
import yfinance as yf

DESTINO = Path(__file__).resolve().parent / "data" / "QQQ_D1.csv"

d = yf.download("QQQ", start="1999-01-01", auto_adjust=True, progress=False)
d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
d = d[["Open", "High", "Low", "Close", "Volume"]].round(4)
d.index.name = "Date"
DESTINO.parent.mkdir(exist_ok=True)
d.to_csv(DESTINO)
print(f"{len(d)} velas diarias · {d.index[0].date()} → {d.index[-1].date()} · guardado en {DESTINO}")
