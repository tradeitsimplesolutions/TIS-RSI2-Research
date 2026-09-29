"""
Descarga el histórico diario de QQQ (ETF del Nasdaq 100) y lo guarda en data/QQQ_D1.csv.

Dos fuentes:
  --norgate   Norgate Data, precios de retorno total (splits y dividendos). Es la fuente con la que se
              generaron las cifras y gráficos de la guía. Requiere licencia y el paquete norgatedata.
  (por defecto) Yahoo Finance, ajustado por dividendos y splits (auto_adjust=True). Gratuito; las cifras
              salen muy parecidas pero no idénticas (el ajuste de dividendos difiere ligeramente).

Uso:  python descargar_datos.py            # Yahoo
      python descargar_datos.py --norgate  # Norgate
"""
import argparse
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "data" / "QQQ_D1.csv"
ap = argparse.ArgumentParser(); ap.add_argument("--norgate", action="store_true"); args = ap.parse_args()
DESTINO.parent.mkdir(exist_ok=True)

if args.norgate:
    import norgatedata as ng
    d = ng.price_timeseries("QQQ", stock_price_adjustment_setting=ng.StockPriceAdjustmentType.TOTALRETURN,
                            padding_setting=ng.PaddingType.NONE, timeseriesformat="pandas-dataframe")
    d = d[["Open", "High", "Low", "Close", "Volume"]].round(4); d.index.name = "Date"; fuente = "Norgate (retorno total)"
else:
    import yfinance as yf
    d = yf.download("QQQ", start="1999-01-01", auto_adjust=True, progress=False)
    d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
    d = d[["Open", "High", "Low", "Close", "Volume"]].round(4); d.index.name = "Date"; fuente = "Yahoo Finance (ajustado)"

d.to_csv(DESTINO)
print(f"{fuente}: {len(d)} velas diarias · {d.index[0].date()} → {d.index[-1].date()} · guardado en {DESTINO}")
