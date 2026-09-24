"""
RSI(2) Mean Reversion sobre el Nasdaq 100 — motor de backtest y validación (Trade It Simple).

Replica la lógica de señal y salida del EA TIS_RSI2_MeanReversion v2.01 (codigo/):
  Entrada : RSI(2) < 15  Y  Close > SMA(200), evaluado al cierre de T  → compra en la apertura de T+1
  Salida  : dos velas verdes consecutivas (Close > Open), evaluado al cierre de T → venta en la apertura de T+1
  Solo largos. Sin stop de precio. Costes: 5 bps por lado (10 bps ida y vuelta), comisión 0.

Dos formas de dimensionar (mismas señales, mismas operaciones):
  "capital"  → 100 % del capital en cada operación (regla de investigación)
  "atr"      → 1 % de riesgo por operación con stop virtual ATR(14)×2 (lo que hace el EA), sin apalancamiento (>100 % se recorta a 100 %)

Uso:
  python motor/rsi2_motor.py                       # QQQ (data/QQQ_D1.csv, baja con descargar_datos.py)
  python motor/rsi2_motor.py --csv otro.csv --etiqueta NDX --solo-metricas
Salidas en resultados/: metricas.json, trades.csv, equity_diaria.csv y graficos/*.png
"""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

RSI_THR, SMA_LEN, SLIP, IS_FRAC = 15, 200, 0.0005, 0.70
RISK_PCT, ATR_LEN, ATR_MULT = 0.01, 14, 2.0
RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "resultados"
rng = np.random.default_rng(42)


# ----------------------------------------------------------------- datos e indicadores
def cargar(csv):
    df = pd.read_csv(csv, parse_dates=["Date"]).set_index("Date").sort_index()
    return df[["Open", "High", "Low", "Close"]].astype(float)


def rsi_wilder(s, n=2):
    d = s.diff(); g = d.clip(lower=0); l = (-d).clip(lower=0)
    ag = g.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    al = l.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    return 100 - 100 / (1 + ag / al.replace(0, np.nan))


def preparar(raw, sma_len=SMA_LEN):
    df = raw.copy()
    df["sma"] = df["Close"].rolling(sma_len).mean()
    df["rsi2"] = rsi_wilder(df["Close"], 2)
    df["verde"] = (df["Close"] > df["Open"]).astype(int)          # definición del EA
    df["ma5"] = df["Close"].rolling(5).mean()                      # solo para la versión del libro
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - df["Close"].shift()).abs(),
                    (df["Low"] - df["Close"].shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1 / ATR_LEN, min_periods=ATR_LEN, adjust=False).mean()
    return df.dropna(subset=["sma", "rsi2", "atr"])


# ----------------------------------------------------------------- backtest
def backtest(df, rsi_thr=RSI_THR, slip=SLIP, salida="2verdes", estricto=True):
    """Devuelve lista de trades. salida: '2verdes' (EA) | 'ma5' (Connors: Close > MA5)."""
    o, c, sma, rsi = df["Open"].values, df["Close"].values, df["sma"].values, df["rsi2"].values
    verde, ma5, atr, idx = df["verde"].values, df["ma5"].values, df["atr"].values, df.index
    trades, en_pos = [], False
    for i in range(2, len(df)):
        if not en_pos:
            cond_rsi = rsi[i - 1] < rsi_thr if estricto else rsi[i - 1] <= rsi_thr
            if cond_rsi and c[i - 1] > sma[i - 1]:
                ep, ei = o[i] * (1 + slip), i
                expo = RISK_PCT * o[i] / (ATR_MULT * atr[i - 1])   # exposición con 1 % de riesgo (sin recortar)
                en_pos = True
        else:
            if salida == "2verdes":
                sal = verde[i - 1] == 1 and verde[i - 2] == 1
            elif salida == "rsi70":
                sal = rsi[i - 1] > 70
            else:
                sal = c[i - 1] > ma5[i - 1]
            if sal:
                xp = o[i] * (1 - slip)
                trades.append(dict(entrada=idx[ei], salida=idx[i], i_ent=ei, i_sal=i, px_ent=ep, px_sal=xp,
                                   ret=xp / ep - 1, expo=expo, barras=i - ei, rsi_senal=rsi[ei - 1]))
                en_pos = False
    if en_pos:  # posición abierta al final: se valora al último cierre
        xp = c[-1] * (1 - slip)
        trades.append(dict(entrada=idx[ei], salida=idx[-1], i_ent=ei, i_sal=len(df) - 1, px_ent=ep, px_sal=xp,
                           ret=xp / ep - 1, expo=expo, barras=len(df) - 1 - ei, rsi_senal=rsi[ei - 1], abierta=True))
    return trades


def expo_de(t, sizing):
    """Fracción del capital en la operación: 'capital' = 100 %; 'x2' = 200 % (apalancamiento 1:2);
    'atr' = 1 % de riesgo; 'atr2' = 2 % de riesgo (tope 100 %); 'fijo' = 100 % del capital inicial, sin reinvertir."""
    if sizing in ("capital", "fijo"): return 1.0
    if sizing == "x2": return 2.0
    return min(1.0, t["expo"] * (2.0 if sizing == "atr2" else 1.0))


def equity_fija(df, trades):
    """Siempre la misma cantidad por operación (el capital inicial), sin reinvertir: la curva es aditiva."""
    r = equity_diaria(df, trades).pct_change().fillna(0)
    return 1 + r.cumsum()


def equity_diaria(df, trades, sizing="capital"):
    """Retorno diario marcado a mercado (0 fuera de posición)."""
    c = df["Close"].values; r = np.zeros(len(df))
    for t in trades:
        e = expo_de(t, sizing)
        i, j = t["i_ent"], t["i_sal"]
        if j == i:
            r[i] = e * (t["px_sal"] / t["px_ent"] - 1); continue
        r[i] = e * (c[i] / t["px_ent"] - 1)
        for k in range(i + 1, j):
            r[k] = e * (c[k] / c[k - 1] - 1)
        r[j] = e * (t["px_sal"] / c[j - 1] - 1)
    return pd.Series(np.cumprod(1 + r), index=df.index)


def metricas(trades, eq=None, sizing="capital"):
    if not trades:
        return None
    r = np.array([t["ret"] * expo_de(t, sizing) for t in trades])
    g, l = r[r > 0], np.abs(r[r <= 0])
    pf = g.sum() / (l.sum() if l.sum() > 0 else 1e-12)
    nb = np.delete(r, r.argmax()); lnb = np.abs(nb[nb <= 0]).sum() or 1e-12
    pfnb = nb[nb > 0].sum() / lnb if len(r) > 1 else None
    eqt = np.cumprod(1 + r); mdd_t = float(((eqt - np.maximum.accumulate(eqt)) / np.maximum.accumulate(eqt)).min())
    m = dict(n=int(len(r)), pf=float(pf), pfnb=(float(pfnb) if pfnb is not None else None),
             mdd=mdd_t, wr=float((r > 0).mean()), expectancy=float(r.mean()),
             ret_total=float(eqt[-1] - 1), barras_media=float(np.mean([t["barras"] for t in trades])),
             mejor=float(r.max()), peor=float(r.min()))
    if eq is not None:
        anos = (eq.index[-1] - eq.index[0]).days / 365.25
        m["cagr"] = float(eq.iloc[-1] ** (1 / anos) - 1) if anos > 0 else None
        m["mdd_diario"] = float(((eq - eq.cummax()) / eq.cummax()).min())
        m["exposicion"] = float((eq.pct_change().fillna(0) != 0).mean())
    return m


def fase1_ok(m):
    return bool(m and m["pf"] >= 1.3 and m["n"] >= 30 and m["mdd"] > -0.20 and (m["pfnb"] or 0) > 1.0)


def episodios_dd(eq, top=5):
    dd = (eq - eq.cummax()) / eq.cummax(); eps = []; en = False
    for d, v in dd.items():
        if not en and v < 0:
            en, ini, fondo, vmin = True, d, d, v
        elif en:
            if v < vmin: fondo, vmin = d, v
            if v == 0:
                eps.append(dict(inicio=str(ini.date()), fondo=str(fondo.date()), fin=str(d.date()),
                                prof=float(vmin), dias=(d - ini).days)); en = False
    if en:
        eps.append(dict(inicio=str(ini.date()), fondo=str(fondo.date()), fin=None, prof=float(vmin),
                        dias=(dd.index[-1] - ini).days))
    eps.sort(key=lambda e: e["prof"])
    return dict(n=len(eps), recuperados=sum(e["fin"] is not None for e in eps),
                dias_medio=float(np.mean([e["dias"] for e in eps])) if eps else None, peores=eps[:top])


# ----------------------------------------------------------------- fases
def fase2_walkforward(df, is_anos=3):
    """Reglas fijas: ventanas rodantes IS 3 años / OOS 1 año natural."""
    anos = sorted(set(df.index.year)); vent = []
    for y in anos:
        if y - is_anos < anos[0] or y == anos[-1] and df.index[-1].month < 12:
            continue
        d_is = df[(df.index.year >= y - is_anos) & (df.index.year < y)]; d_oos = df[df.index.year == y]
        if len(d_is) < 600 or len(d_oos) < 200: continue
        ti, to = backtest(d_is), backtest(d_oos)
        mi, mo = metricas(ti), metricas(to)
        ri = (mi["ret_total"] if mi else 0) / is_anos; ro = mo["ret_total"] if mo else 0
        vent.append(dict(ano=y, ret_is_anual=float(ri), ret_oos=float(ro), n_oos=(mo["n"] if mo else 0),
                         pf_oos=(mo["pf"] if mo else None), mdd_oos=(mo["mdd"] if mo else 0)))
    if not vent: return dict(ventanas=[], pasa=False)
    ri = np.mean([v["ret_is_anual"] for v in vent]); ro = np.mean([v["ret_oos"] for v in vent])
    ef = float(ro / ri) if ri > 0 else None
    pct_pos = float(np.mean([v["ret_oos"] > 0 for v in vent]))
    peor_mdd = float(min(v["mdd_oos"] for v in vent))
    pasa = bool(ef is not None and ef >= 0.5 and pct_pos >= 0.6 and peor_mdd > -0.20)
    return dict(ventanas=vent, eficiencia=ef, pct_positivas=pct_pos, peor_mdd=peor_mdd, pasa=pasa)


def fase3_grid(raw, n_is):
    RS, SM = [5, 10, 15, 20, 25, 30], [100, 150, 200, 250, 300]
    pf = np.full((len(RS), len(SM)), np.nan); nn = np.zeros_like(pf)
    for a, rt in enumerate(RS):
        for b, sl in enumerate(SM):
            d2 = preparar(raw, sl); d2 = d2[d2.index <= n_is]
            m = metricas(backtest(d2, rsi_thr=rt))
            if m: pf[a, b], nn[a, b] = m["pf"], m["n"]
    a, b = RS.index(RSI_THR), SM.index(SMA_LEN)
    vec = pf[a - 1:a + 2, b - 1:b + 2]; centro = pf[a, b]
    meseta = bool(np.all(vec >= 1.3) and np.all(nn[a - 1:a + 2, b - 1:b + 2] >= 30))
    caida = float((1 - vec / centro).max() * 100)
    ia, ib = np.unravel_index(np.nanargmax(pf), pf.shape)
    return dict(rsi=RS, sma=SM, pf=np.round(pf, 3).tolist(), n=nn.astype(int).tolist(),
                centro=float(centro), meseta_3x3=meseta, peor_caida_vecino_pct=caida,
                anticliff=bool(caida <= 30), pct_celdas_pf13=float(np.nanmean(pf >= 1.3)),
                optimo=dict(rsi=RS[ia], sma=SM[ib], pf=float(pf[ia, ib])),
                pasa=bool(meseta and caida <= 30))


def aed(df):
    """Análisis exploratorio del Nasdaq 100: ¿revierte tras caídas rápidas? ¿cuánto pesa la tendencia?"""
    c = df["Close"]; r = c.pct_change(); H = [1, 2, 3, 5, 10]
    sobre = df["Close"] > df["sma"]; senal = df["rsi2"] < RSI_THR
    grupos = {"Todos los días": pd.Series(True, index=df.index), "Días sobre la SMA 200": sobre,
              "RSI(2) < 15 sobre la SMA 200 (nuestra señal)": senal & sobre, "RSI(2) < 15 bajo la SMA 200": senal & ~sobre}
    fwd = {}
    for nombre, m in grupos.items():
        fila = {}
        for h in H:
            f = (c.shift(-h) / c - 1)[m].dropna()
            fila[h] = dict(media=float(f.mean()), pct_pos=float((f > 0).mean()), n=int(len(f)))
        fwd[nombre] = fila
    autocorr = [float(r.autocorr(k)) for k in range(1, 11)]
    # rachas de días de caída consecutivos (sobre la SMA 200) → retorno de los 3 días siguientes
    baja = (r < 0).astype(int); racha = baja.groupby((baja != baja.shift()).cumsum()).cumsum()
    f3 = c.shift(-3) / c - 1; rachas = {}
    for k in [1, 2, 3, 4]:
        m = (racha == k) & sobre; s = f3[m].dropna()
        rachas[k] = dict(media=float(s.mean()), pct_pos=float((s > 0).mean()), n=int(len(s)))
    por_ano = (senal & sobre).groupby(df.index.year).sum()
    vol_anual = r.groupby(df.index.year).std() * np.sqrt(252)
    atr_pct = (df["atr"] / c)
    return dict(horizontes=H, forward=fwd, autocorr=autocorr, rachas=rachas,
                pct_sobre_sma=float(sobre.mean()), senales_ano_media=float(por_ano.mean()), senales_ano=por_ano.astype(int).to_dict(),
                retorno=dict(media_dia=float(r.mean()), std_dia=float(r.std()), asimetria=float(r.skew()), curtosis=float(r.kurt()),
                             mejor_dia=float(r.max()), peor_dia=float(r.min()), pct_dias_pos=float((r > 0).mean())),
                atr_pct=dict(media=float(atr_pct.mean()), min=float(atr_pct.min()), max=float(atr_pct.max())),
                vol_anual={int(k): float(v) for k, v in vol_anual.items()},
                _atr_pct=atr_pct, _sobre=sobre)


def robustez_4d(raw, n_is):
    """Cuatro dimensiones sobre IS: umbral RSI × periodo SMA × tipo de salida × coste por lado."""
    RS, SM = [5, 10, 15, 20, 25, 30], [100, 150, 200, 250, 300]
    SAL = [("2verdes", "Dos velas verdes"), ("ma5", "Cierre > MA(5)"), ("rsi70", "RSI(2) > 70")]
    SLIP = [(0.0005, "5 bps"), (0.0010, "10 bps")]
    preps = {sl: preparar(raw, sl) for sl in SM}
    cubos, todos = {}, []
    for sk, sn in SAL:
        for sp, spn in SLIP:
            pf = np.full((len(RS), len(SM)), np.nan)
            for a, rt in enumerate(RS):
                for b, sl in enumerate(SM):
                    d2 = preps[sl]; d2 = d2[d2.index <= n_is]
                    m = metricas(backtest(d2, rsi_thr=rt, slip=sp, salida=sk))
                    if m:
                        pf[a, b] = m["pf"]
                        todos.append(dict(rsi=rt, sma=sl, salida=sn, coste=spn, pf=m["pf"], n=m["n"], mdd=m["mdd"]))
            cubos[f"{sn} · {spn}"] = np.round(pf, 3).tolist()
    pfs = np.array([x["pf"] for x in todos])
    viva = [x for x in todos if x["rsi"] == RSI_THR and x["sma"] == SMA_LEN and x["salida"] == "Dos velas verdes" and x["coste"] == "5 bps"][0]["pf"]
    return dict(rsi=RS, sma=SM, salidas=[s for _, s in SAL], costes=[s for _, s in SLIP], cubos=cubos,
                n_combos=int(len(todos)), pct_pf13=float((pfs >= 1.3).mean()), pct_pf1=float((pfs >= 1.0).mean()),
                pf_min=float(pfs.min()), pf_mediana=float(np.median(pfs)), pf_max=float(pfs.max()),
                pf_vigente=float(viva), percentil_vigente=float((pfs < viva).mean()),
                por_salida={s: float(np.mean([x["pf"] for x in todos if x["salida"] == s])) for _, s in SAL},
                por_coste={c: float(np.mean([x["pf"] for x in todos if x["coste"] == c])) for _, c in SLIP},
                _todos=todos)


def fase4_montecarlo(trades, n_sim=5000, bloque=5, sizing="capital"):
    r = np.array([t["ret"] * expo_de(t, sizing) for t in trades]); n = len(r)
    rets, mdds, ruina = [], [], 0
    for _ in range(n_sim):
        starts = rng.integers(0, n, size=int(np.ceil(n / bloque)))
        idx = np.concatenate([np.arange(s, s + bloque) % n for s in starts])[:n]
        eq = np.cumprod(1 + r[idx]); pk = np.maximum.accumulate(eq)
        rets.append(eq[-1] - 1); mdds.append(((eq - pk) / pk).min()); ruina += eq.min() < 0.5
    rets, mdds = np.array(rets), np.array(mdds)
    out = dict(n_sim=n_sim, bloque=bloque, p5_ret=float(np.percentile(rets, 5)), p50_ret=float(np.median(rets)),
               p95_ret=float(np.percentile(rets, 95)), mdd_p5=float(np.percentile(mdds, 5)),
               mdd_p50=float(np.median(mdds)), mdd_p95=float(np.percentile(mdds, 95)),
               prob_mdd_25=float((mdds < -0.25).mean()), prob_ruina=float(ruina / n_sim),
               prob_ret_pos=float((rets > 0).mean()))
    out["pasa"] = bool(out["p5_ret"] > 0 and out["mdd_p5"] > -0.25 and out["prob_ruina"] < 0.05)
    out["_rets"], out["_mdds"] = rets, mdds
    return out


def fase5_stress(df, dfo, trades_oos):
    esc = {}
    m = metricas(backtest(dfo, slip=SLIP * 2)); esc["costes_x2"] = dict(**m, pasa=bool(m["pf"] >= 1.1))
    por_ano = {}
    for t in trades_oos: por_ano[t["salida"].year] = por_ano.get(t["salida"].year, 0) + t["ret"]
    mejores = sorted(por_ano, key=por_ano.get, reverse=True)[:2]
    sin = [t for t in trades_oos if t["salida"].year not in mejores]
    m = metricas(sin); esc["sin_2_mejores_anos"] = dict(**m, anos=mejores, pasa=bool(m["pf"] >= 1.1))
    for nombre, (a, b) in {"regimen_2000_2002": (2000, 2002), "regimen_2008": (2008, 2008),
                           "regimen_2022": (2022, 2022)}.items():
        d = df[(df.index.year >= a) & (df.index.year <= b)]
        m = metricas(backtest(d)) if len(d) else None
        esc[nombre] = dict(**m, pasa=bool(m["pf"] >= 1.1)) if m else dict(n=0, pasa=None)
    esc["pasa"] = bool(esc["costes_x2"]["pasa"] and esc["sin_2_mejores_anos"]["pasa"])
    return esc


def monkey_test(df, trades, n_sim=2000):
    """Entradas al azar en días con Close > SMA200, mismo nº de trades y misma duración; mismos costes."""
    o, c, sma = df["Open"].values, df["Close"].values, df["sma"].values
    elig = np.where(c[:-1] > sma[:-1])[0] + 1              # el día siguiente a un cierre sobre la SMA
    dur = np.array([t["barras"] for t in trades]); n = len(trades)
    real = metricas(trades); pfs, rets, mdds = [], [], []
    for _ in range(n_sim):
        ent = rng.choice(elig, size=n, replace=False); d = rng.choice(dur, size=n)
        sal = np.minimum(ent + d, len(df) - 1)
        r = (o[sal] * (1 - SLIP)) / (o[ent] * (1 + SLIP)) - 1
        g, l = r[r > 0].sum(), np.abs(r[r <= 0]).sum() or 1e-12
        eq = np.cumprod(1 + r); pk = np.maximum.accumulate(eq)
        pfs.append(g / l); rets.append(eq[-1] - 1); mdds.append(((eq - pk) / pk).min())
    pfs, rets, mdds = np.array(pfs), np.array(rets), np.array(mdds)
    return dict(n_sim=n_sim, pf_real=real["pf"], pct_pf=float((pfs < real["pf"]).mean()),
                pct_ret=float((rets < real["ret_total"]).mean()), pct_mdd=float((mdds < real["mdd"]).mean()),
                pf_mono_mediana=float(np.median(pfs)), _pfs=pfs)


def edge_decay(trades, is_fin):
    anos = {}
    for t in trades:
        y = t["salida"].year; anos.setdefault(y, []).append(t)
    filas = []
    for y in sorted(anos):
        m = metricas(anos[y]); filas.append(dict(ano=y, n=m["n"], pf=m["pf"], expectancy=m["expectancy"],
                                                ret=m["ret_total"], wr=m["wr"]))
    is_rows = [f for f in filas if f["ano"] < is_fin.year]
    ult = [f for f in filas if f["ano"] >= pd.Timestamp.today().year - 3 and f["ano"] < pd.Timestamp.today().year]
    def agg(rows):
        tr = [t for f in rows for t in anos[f["ano"]]]; m = metricas(tr)
        return dict(freq=len(tr) / len(rows), expectancy=m["expectancy"], pf=m["pf"])
    return dict(anual=filas, is_medio=agg(is_rows), ultimos_3=agg(ult), anos_ultimos=[f["ano"] for f in ult])


# ----------------------------------------------------------------- gráficos
def t_str(t):
    return f"{t['entrada'].strftime('%d %b %Y')} → {t['salida'].strftime('%d %b %Y')} · {t['barras']} días · {t['ret']*100:+.2f} %"


def graficos(df, tr_all, eq_cap, eq_atr, sp_date, res, raw):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.dates as mdates
    G = OUT / "graficos"; G.mkdir(parents=True, exist_ok=True)
    VERDE, VERDE2, GRIS, ROJO, TINTA, AZUL = "#0e9c58", "#26d97e", "#95a29b", "#c8512f", "#132620", "#2b6cb0"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": "#c2d0c8",
                         "axes.labelcolor": "#3a4b44", "xtick.color": "#3a4b44", "ytick.color": "#3a4b44",
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": "#e2ede8", "grid.linewidth": 0.6, "figure.facecolor": "white",
                         "axes.titleweight": "bold", "axes.titlesize": 14, "axes.titlelocation": "left"})

    def guardar(fig, nombre):
        fig.savefig(G / nombre, dpi=150, bbox_inches="tight"); plt.close(fig)

    # 1. equity dos sizings + drawdown
    def eje_log(ax, top):
        ax.set_yscale("log"); ticks = [t for t in [1, 1.5, 2, 3, 4, 5, 6, 8] if t <= top * 1.15]
        ax.set_yticks(ticks); ax.set_yticklabels([f"{t:g}×" for t in ticks]); ax.minorticks_off()

    eq_fijo = res["_eq_fijo"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.8), height_ratios=[3, 1.2], sharex=True)
    a1.axvspan(sp_date, eq_cap.index[-1], color="#eef6f1", zorder=0)
    l1, = a1.plot(eq_cap.index, eq_cap.values, color=VERDE, lw=1.8)
    l3, = a1.plot(eq_fijo.index, eq_fijo.values, color="#c97d1e", lw=1.6)
    l2, = a1.plot(eq_atr.index, eq_atr.values, color=AZUL, lw=1.8)
    eje_log(a1, eq_cap.max()); a1.set_ylabel("Capital (1 = inicial, escala log)")
    a1.text(eq_cap.index[-1], eq_cap.iloc[-1], f"  100 % capital · {eq_cap.iloc[-1]:.2f}×", color=VERDE, va="center", fontweight="bold")
    a1.text(eq_fijo.index[-1], eq_fijo.iloc[-1], f"  10.000 $ fijos · {eq_fijo.iloc[-1]:.2f}×", color="#c97d1e", va="center", fontweight="bold")
    a1.text(eq_atr.index[-1], eq_atr.iloc[-1], f"  Riesgo 1 % (ATR) · {eq_atr.iloc[-1]:.2f}×", color=AZUL, va="center", fontweight="bold")
    a1.text(sp_date, a1.get_ylim()[1], "  fuera de muestra →", va="top", color="#3a4b44", fontsize=10)
    a1.set_title("RSI(2) sobre QQQ — curva de capital con tres tamaños de posición")
    a1.legend([l1, l3, l2], ["100 % del capital por operación (reinvirtiendo)", "10.000 $ fijos por operación (sin reinvertir)", "1 % de riesgo por operación (ATR×2)"], loc="upper left", frameon=False)
    a1.set_xlim(eq_cap.index[0], eq_cap.index[-1] + pd.Timedelta(days=800))
    dd = (eq_cap - eq_cap.cummax()) / eq_cap.cummax() * 100
    a2.fill_between(dd.index, dd.values, 0, color=ROJO, alpha=0.25, lw=0); a2.plot(dd.index, dd.values, color=ROJO, lw=1)
    a2.set_ylabel("Drawdown %"); a2.xaxis.set_major_locator(mdates.YearLocator(2))
    guardar(fig, "01_equity.png")

    # 2. operaciones de un año sobre el precio
    y = pd.Timestamp.today().year - 1
    d = raw[(raw.index >= f"{y}-01-01") & (raw.index <= f"{y}-12-31")]
    tr_y = [t for t in tr_all if t["entrada"].year == y]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(d.index, d["Close"], color=GRIS, lw=1.2)
    ax.plot(d.index, df.loc[d.index, "sma"], color="#3a4b44", lw=1, ls="--")
    ax.scatter([t["entrada"] for t in tr_y], [t["px_ent"] for t in tr_y], marker="^", s=90, color=VERDE, zorder=5, label="Entrada")
    ax.scatter([t["salida"] for t in tr_y], [t["px_sal"] for t in tr_y], marker="v", s=90, color=ROJO, zorder=5, label="Salida")
    for t in tr_y:
        ax.plot([t["entrada"], t["salida"]], [t["px_ent"], t["px_sal"]], color=VERDE if t["ret"] > 0 else ROJO, lw=2, alpha=0.7)
    ax.set_title(f"Así se ven las operaciones — QQQ en {y} ({len(tr_y)} operaciones)")
    ax.legend(["Cierre QQQ", "SMA 200", "Entrada (apertura)", "Salida (apertura)"], frameon=False, loc="upper left")
    ax.set_ylabel("Precio QQQ (USD)")
    guardar(fig, "02_operaciones_ano.png")

    # 3. libro vs nuestra
    eq_libro = res["_eq_libro"]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.axvspan(sp_date, eq_cap.index[-1], color="#eef6f1", zorder=0)
    l1, = ax.plot(eq_cap.index, eq_cap.values, color=VERDE, lw=1.8); l2, = ax.plot(eq_libro.index, eq_libro.values, color=AZUL, lw=1.8)
    eje_log(ax, eq_cap.max())
    ax.text(eq_cap.index[-1], eq_cap.iloc[-1], f"  TIS · {eq_cap.iloc[-1]:.1f}×", color=VERDE, fontweight="bold", va="center")
    ax.text(eq_libro.index[-1], eq_libro.iloc[-1], f"  Libro · {eq_libro.iloc[-1]:.1f}×", color=AZUL, fontweight="bold", va="center")
    ax.legend([l1, l2], ["TIS: RSI(2) < 15, salida 2 velas verdes", "Connors: RSI(2) ≤ 5, salida al cruzar la MA(5)"], frameon=False, loc="upper left")
    ax.set_title("La versión del libro frente a la nuestra — mismos datos, mismos costes")
    ax.set_xlim(eq_cap.index[0], eq_cap.index[-1] + pd.Timedelta(days=800)); ax.set_ylabel("Capital (escala log)")
    guardar(fig, "03_libro_vs_tis.png")

    # 4. grid
    g = res["fase3"]; pf = np.array(g["pf"]); nn = np.array(g["n"])
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(pf, cmap="Greens", vmin=1.0, vmax=max(2.5, np.nanmax(pf)), aspect="auto")
    ax.set_xticks(range(len(g["sma"]))); ax.set_xticklabels([f"SMA {s}" for s in g["sma"]])
    ax.set_yticks(range(len(g["rsi"]))); ax.set_yticklabels([f"RSI < {r}" for r in g["rsi"]]); ax.grid(False)
    for a in range(pf.shape[0]):
        for b in range(pf.shape[1]):
            ax.text(b, a, f"{pf[a,b]:.2f}\nN={int(nn[a,b])}", ha="center", va="center", fontsize=9,
                    color="white" if pf[a, b] > 1.9 else TINTA)
    a, b = g["rsi"].index(RSI_THR), g["sma"].index(SMA_LEN)
    ax.add_patch(plt.Rectangle((b - 0.5, a - 0.5), 1, 1, fill=False, ec=TINTA, lw=3))
    ax.set_title("Zonas robustas — Profit Factor en construcción (IS) al mover los dos parámetros")
    fig.colorbar(im, ax=ax, label="Profit Factor (IS)", shrink=0.8)
    guardar(fig, "04_grid.png")

    # 5. Monte Carlo
    mc = res["fase4"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.hist(mc["_rets"] * 100, bins=50, color=VERDE2, alpha=0.8, ec="white")
    a1.axvline(mc["p5_ret"] * 100, color=TINTA, ls="--"); a1.text(mc["p5_ret"] * 100, a1.get_ylim()[1] * 0.9, f" p5 = {mc['p5_ret']*100:.0f} %", color=TINTA)
    a1.set_title("Retorno total en 5.000 reordenaciones"); a1.set_xlabel("Retorno total (%)")
    a2.hist(mc["_mdds"] * 100, bins=50, color="#f0a860", alpha=0.85, ec="white")
    a2.axvline(-25, color=ROJO, ls="--"); a2.text(-25, a2.get_ylim()[1] * 0.9, " límite −25 %", color=ROJO, ha="right")
    a2.axvline(mc["mdd_p5"] * 100, color=TINTA, ls="--"); a2.text(mc["mdd_p5"] * 100, a2.get_ylim()[1] * 0.75, f" p5 = {mc['mdd_p5']*100:.1f} %", color=TINTA)
    a2.set_title("Drawdown máximo en las mismas reordenaciones"); a2.set_xlabel("Drawdown máximo (%)")
    guardar(fig, "05_montecarlo.png")

    # 6. monkey
    mk = res["monkey"]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.hist(mk["_pfs"], bins=50, color="#c2d0c8", ec="white")
    ax.axvline(mk["pf_real"], color=VERDE, lw=3)
    ax.text(mk["pf_real"], ax.get_ylim()[1] * 0.85, f"  Estrategia real · PF {mk['pf_real']:.2f}\n  supera al {mk['pct_pf']*100:.1f} % de los monos", color=VERDE, fontweight="bold")
    ax.set_title(f"Monkey test — {mk['n_sim']} entradas al azar dentro de la misma tendencia"); ax.set_xlabel("Profit Factor de cada mono")
    guardar(fig, "06_monkey.png")

    # 7. PF por año
    ed = res["edge_decay"]["anual"]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    cols = [VERDE if f["pf"] >= 1 else ROJO for f in ed]
    ax.bar([f["ano"] for f in ed], [min(f["pf"], 6) for f in ed], color=cols, width=0.7)
    ax.axhline(1, color=TINTA, lw=1); ax.axvspan(sp_date.year - 0.5, ed[-1]["ano"] + 0.5, color="#eef6f1", zorder=0)
    for f in ed:
        ax.text(f["ano"], min(f["pf"], 6) + 0.08, f"{f['n']} op." + (" · PF>6" if f["pf"] > 6 else ""), ha="center", fontsize=7.5, color="#6b7a72", rotation=90 if f["pf"] > 6 else 0, va="bottom")
    ax.set_ylim(0, 7.6)
    ax.set_title("¿Se desgasta el edge? Profit Factor por año (sombreado = fuera de muestra)"); ax.set_ylabel("Profit Factor (tope 6)")
    guardar(fig, "07_pf_anual.png")

    # 8. underwater
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.fill_between(dd.index, dd.values, 0, color=ROJO, alpha=0.25, lw=0); ax.plot(dd.index, dd.values, color=ROJO, lw=1)
    ax.axvline(sp_date, color=TINTA, ls=":", lw=1); ax.set_ylabel("Caída desde el máximo (%)")
    ax.set_title("Curva submarina — cuánto tiempo pasa la cuenta por debajo de su máximo (100 % capital)")
    guardar(fig, "08_underwater.png")

    # 10. tres niveles de riesgo
    eq2, eqx = res["_eq_atr2"], res["_eq_x2"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.4), height_ratios=[3, 1.3], sharex=True)
    a1.axvspan(sp_date, eq_cap.index[-1], color="#eef6f1", zorder=0)
    la, = a1.plot(eq_atr.index, eq_atr.values, color=AZUL, lw=1.8)
    lb, = a1.plot(eq2.index, eq2.values, color="#f0a860", lw=1.8)
    lc, = a1.plot(eq_cap.index, eq_cap.values, color=VERDE, lw=1.8)
    ld, = a1.plot(eqx.index, eqx.values, color=ROJO, lw=1.6)
    eje_log(a1, max(eq_cap.max(), eqx.max())); a1.set_ylabel("Capital (1 = inicial, escala log)")
    for eq, col, nom in [(eq_atr, AZUL, "Conservador · 1 % riesgo"), (eq2, "#c97d1e", "Intermedio · 2 % riesgo"), (eq_cap, VERDE, "Decidido · 100 %"), (eqx, ROJO, "Arriesgado · 1:2")]:
        a1.text(eq.index[-1], eq.iloc[-1], f"  {nom} · {eq.iloc[-1]:.2f}×", color=col, va="center", fontweight="bold", fontsize=10)
    a1.legend([la, lb, lc, ld], ["Conservador: 1 % de riesgo por operación (ATR×2) — lo que hace el robot", "Intermedio: 2 % de riesgo por operación (ATR×2)", "Decidido: 100 % del capital en cada operación", "Arriesgado: 200 % del capital (apalancamiento 1:2)"], loc="upper left", frameon=False)
    a1.set_title("La misma señal con cuatro tamaños de posición")
    a1.set_xlim(eq_cap.index[0], eq_cap.index[-1] + pd.Timedelta(days=1100))
    for eq, col in [(eqx, ROJO), (eq_cap, VERDE), (eq2, "#f0a860"), (eq_atr, AZUL)]:
        d = (eq - eq.cummax()) / eq.cummax() * 100
        a2.fill_between(d.index, d.values, 0, color=col, alpha=0.18, lw=0); a2.plot(d.index, d.values, color=col, lw=0.9)
    a2.set_ylabel("Drawdown %"); a2.xaxis.set_major_locator(mdates.YearLocator(2))
    guardar(fig, "10_riesgo.png")

    # 16. dos operaciones en velas (una ganadora y una perdedora, fuera de muestra)
    def panel_rsi(ax, d, t):
        sig = d.index[d.index.get_loc(t["entrada"]) - 1]
        ax.fill_between(d.index, 0, RSI_THR, color="#e6faef", zorder=0)
        ax.plot(d.index, d["rsi2"], color="#7a4fb8", lw=1.6)
        ax.axhline(RSI_THR, color=VERDE, lw=1, ls="--"); ax.axhline(70, color=GRIS, lw=0.8, ls=":")
        ax.axvspan(mdates.date2num(sig) - 0.5, mdates.date2num(sig) + 0.5, color="#fff5e9", zorder=0)
        ax.scatter([sig], [d.loc[sig, "rsi2"]], color="#9a5a15", s=40, zorder=5)
        ax.text(d.index[0], RSI_THR + 3, f" zona de compra: RSI(2) < {RSI_THR}", fontsize=8, color=VERDE)
        ax.set_ylim(0, 100); ax.set_yticks([0, 15, 50, 70, 100]); ax.set_ylabel("RSI(2)", fontsize=9); ax.tick_params(labelsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b")); ax.grid(axis="x", visible=False)

    def velas(ax, d, t, titulo):
        for i, (dt, row) in enumerate(d.iterrows()):
            col = VERDE if row["Close"] >= row["Open"] else ROJO
            ax.plot([dt, dt], [row["Low"], row["High"]], color=col, lw=1)
            ax.add_patch(plt.Rectangle((mdates.date2num(dt) - 0.3, min(row["Open"], row["Close"])), 0.6, abs(row["Close"] - row["Open"]) or 0.01, color=col))
        ax.plot(d.index, d["sma"], color=GRIS, lw=1, ls="--")
        sig = d.index[d.index.get_loc(t["entrada"]) - 1]
        ax.axvspan(mdates.date2num(sig) - 0.5, mdates.date2num(sig) + 0.5, color="#fff5e9", zorder=0)
        ax.annotate(f"señal al cierre\nRSI(2) = {t['rsi_senal']:.0f}", (sig, d.loc[sig, "Low"]), xytext=(0, -38), textcoords="offset points", ha="center", fontsize=8.5, color="#9a5a15", arrowprops=dict(arrowstyle="-", color="#9a5a15"))
        bb = dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9)
        ax.annotate(f"compra {t['px_ent']:.2f}", (t["entrada"], t["px_ent"]), xytext=(-62, -48), textcoords="offset points", fontsize=9, color=VERDE, fontweight="bold", bbox=bb, arrowprops=dict(arrowstyle="->", color=VERDE))
        ax.annotate(f"venta {t['px_sal']:.2f}\n{t['ret']*100:+.2f} %", (t["salida"], t["px_sal"]), xytext=(14, -52), textcoords="offset points", fontsize=9, color=ROJO if t["ret"] < 0 else VERDE, fontweight="bold", bbox=bb, arrowprops=dict(arrowstyle="->", color=ROJO if t["ret"] < 0 else VERDE))
        ax.set_title(titulo, fontsize=10.5, loc="left"); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.set_xlim(mdates.date2num(d.index[0]) - 0.7, mdates.date2num(d.index[-1]) + 0.7); ax.grid(axis="x", visible=False)
        ax.margins(y=0.18); ax.set_ylabel("QQQ (USD)", fontsize=9); ax.tick_params(labelbottom=False)
    oos_tr = [t for t in tr_all if t["entrada"] >= sp_date and not t.get("abierta")]
    gan = max((t for t in oos_tr[-40:]), key=lambda t: t["ret"]); per = min((t for t in oos_tr[-40:]), key=lambda t: t["ret"])

    def tit(nombre, t):
        e1 = min(1, t["expo"]); return (f"{nombre} · {t['entrada'].strftime('%d %b %Y')} → {t['salida'].strftime('%d %b %Y')} · {t['barras']} días\n"
                                        f"movimiento del precio: {t['ret']*100:+.2f} %\n"
                                        f"sobre el capital → 100 %: {t['ret']*100:+.2f} %  ·  robot (1 % riesgo, ATR): {t['ret']*e1*100:+.2f} %")
    fig, axs = plt.subplots(2, 2, figsize=(13, 7.2), height_ratios=[3, 1.1], sharex="col")
    for j, (t, nombre) in enumerate([(gan, "GANADORA"), (per, "PERDEDORA")]):
        i0, i1 = max(0, t["i_ent"] - 7), min(len(df) - 1, t["i_sal"] + 4)
        d = df.iloc[i0:i1 + 1]; velas(axs[0, j], d, t, tit(nombre, t)); panel_rsi(axs[1, j], d, t)
    fig.suptitle("Así se ve una operación, vela a vela: la señal, la compra en la apertura, las dos velas verdes y la venta", fontweight="bold", x=0.01, ha="left", y=1.0)
    fig.tight_layout()
    guardar(fig, "16_operacion_ejemplo.png")

    # 17. qué calcula el ATR
    j = tr_all[-1]["i_ent"] - 1; d = df.iloc[j - 13:j + 1]; c_prev = df["Close"].iloc[j - 14:j].values
    tr = np.maximum.reduce([d["High"].values - d["Low"].values, np.abs(d["High"].values - c_prev), np.abs(d["Low"].values - c_prev)])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw=dict(width_ratios=[1.6, 1]))
    for k, (dt, row) in enumerate(d.iterrows()):
        col = VERDE if row["Close"] >= row["Open"] else ROJO
        a1.plot([k, k], [row["Low"], row["High"]], color=col, lw=1)
        a1.add_patch(plt.Rectangle((k - 0.3, min(row["Open"], row["Close"])), 0.6, abs(row["Close"] - row["Open"]) or 0.01, color=col))
        lo, hi = min(row["Low"], c_prev[k]), max(row["High"], c_prev[k])
        a1.plot([k + 0.42, k + 0.42], [lo, hi], color="#c97d1e", lw=3, alpha=0.7)
    a1.set_xticks(range(len(d))); a1.set_xticklabels([dt.strftime("%d/%m") for dt in d.index], fontsize=8, rotation=45)
    a1.set_title("Las 14 velas anteriores a la última señal\nbarra naranja = rango verdadero de cada día", fontsize=10.5, loc="left"); a1.set_ylabel("QQQ (USD)")
    a2.bar(range(len(tr)), tr, color="#f0a860"); a2.axhline(d["atr"].iloc[-1], color=TINTA, lw=2)
    a2.text(0.02, 0.95, f"ATR(14) = {d['atr'].iloc[-1]:.2f} $  ({d['atr'].iloc[-1]/d['Close'].iloc[-1]*100:.2f} % del precio)", transform=a2.transAxes, va="top", fontsize=10, fontweight="bold", color=TINTA, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e2ede8"))
    a2.set_xticks(range(len(d))); a2.set_xticklabels([dt.strftime("%d/%m") for dt in d.index], fontsize=8, rotation=45); a2.set_ylabel("Rango verdadero (USD)")
    a2.set_title("La media de esos 14 rangos es el ATR\n(línea negra)", fontsize=10.5, loc="left"); a2.set_ylim(0, tr.max() * 1.3)
    fig.tight_layout()
    guardar(fig, "17_atr.png")

    # 13. AED: retornos a plazo tras la señal
    ae = res["aed"]; H = ae["horizontes"]; nombres = list(ae["forward"].keys())
    cols_g = [GRIS, AZUL, VERDE, ROJO]
    fig, ax = plt.subplots(figsize=(11, 4.8)); w = 0.2
    for k, (nom, col) in enumerate(zip(nombres, cols_g)):
        vals = [ae["forward"][nom][h]["media"] * 100 for h in H]
        ax.bar(np.arange(len(H)) + (k - 1.5) * w, vals, width=w, color=col, label=nom)
        for x, v in zip(np.arange(len(H)) + (k - 1.5) * w, vals):
            ax.text(x, v + (0.05 if v >= 0 else -0.12), f"{v:.1f}", ha="center", fontsize=7.5, color="#3a4b44")
    ax.axhline(0, color=TINTA, lw=1); ax.set_xticks(range(len(H))); ax.set_xticklabels([f"{h} día{'s' if h > 1 else ''} después" for h in H])
    ax.set_ylabel("Retorno medio (%)"); ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("¿Qué pasa después de una sobreventa extrema? Retorno medio a 1, 2, 3, 5 y 10 días")
    guardar(fig, "13_aed_forward.png")

    # 14. AED: autocorrelación y rachas
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.bar(range(1, 11), [v * 100 for v in ae["autocorr"]], color=[ROJO if v < 0 else VERDE for v in ae["autocorr"]], width=0.7)
    a1.axhline(0, color=TINTA, lw=1); a1.set_xlabel("Retraso (días)"); a1.set_ylabel("Autocorrelación (%)")
    a1.set_title("Autocorrelación de los retornos diarios")
    ks = list(ae["rachas"].keys()); a2.bar(ks, [ae["rachas"][k]["media"] * 100 for k in ks], color=VERDE, width=0.6)
    for k in ks: a2.text(k, ae["rachas"][k]["media"] * 100 + 0.03, f"{ae['rachas'][k]['pct_pos']*100:.0f} % pos.\nn={ae['rachas'][k]['n']}", ha="center", fontsize=8, color="#3a4b44")
    a2.axhline(0, color=TINTA, lw=1); a2.set_xlabel("Días seguidos de caída (sobre la SMA 200)"); a2.set_ylabel("Retorno medio 3 días después (%)")
    a2.set_title("Cuanto más cae seguido, más rebota"); a2.set_xticks(ks)
    guardar(fig, "14_aed_rachas.png")

    # 15. AED: régimen de tendencia y volatilidad
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), height_ratios=[2.2, 1], sharex=True)
    a1.plot(df.index, df["Close"], color=TINTA, lw=0.9); a1.plot(df.index, df["sma"], color=AZUL, lw=1.2)
    a1.fill_between(df.index, df["Close"].min(), df["Close"].max(), where=~ae["_sobre"].values, color=ROJO, alpha=0.08, lw=0)
    a1.set_yscale("log"); a1.set_ylabel("QQQ (escala log)")
    a1.set_title(f"Régimen de tendencia — el {ae['pct_sobre_sma']*100:.0f} % del tiempo sobre la SMA 200 (sombreado rojo: por debajo, la estrategia no opera)")
    a1.legend(["Cierre QQQ", "SMA 200"], frameon=False, loc="upper left")
    a2.plot(df.index, ae["_atr_pct"].values * 100, color="#c97d1e", lw=0.9); a2.set_ylabel("ATR(14) / precio (%)")
    a2.set_title("Volatilidad diaria: por eso el tamaño de posición se calcula con el ATR", fontsize=11)
    a2.xaxis.set_major_locator(mdates.YearLocator(2))
    guardar(fig, "15_aed_regimen.png")

    # 11. robustez 4D: seis mapas con la misma escala
    r4 = res["robustez_4d"]
    fig, axs = plt.subplots(2, 3, figsize=(13, 8), sharex=True, sharey=True)
    vmax = max(2.5, max(np.nanmax(np.array(v)) for v in r4["cubos"].values()))
    for j, sn in enumerate(r4["salidas"]):
        for i, cn in enumerate(r4["costes"]):
            ax = axs[i, j]; pf = np.array(r4["cubos"][f"{sn} · {cn}"])
            im = ax.imshow(pf, cmap="Greens", vmin=1.0, vmax=vmax, aspect="auto"); ax.grid(False)
            for a in range(pf.shape[0]):
                for b in range(pf.shape[1]):
                    ax.text(b, a, f"{pf[a,b]:.2f}", ha="center", va="center", fontsize=8, color="white" if pf[a, b] > 0.55 * vmax + 0.45 else TINTA)
            ax.set_title(f"Salida: {sn}\ncoste {cn} por lado", fontsize=10, loc="center")
            ax.set_xticks(range(len(r4["sma"]))); ax.set_xticklabels([str(s) for s in r4["sma"]], fontsize=8.5)
            ax.set_yticks(range(len(r4["rsi"]))); ax.set_yticklabels([f"RSI<{r}" for r in r4["rsi"]], fontsize=8.5)
            if i == 1: ax.set_xlabel("periodo de la SMA", fontsize=9)
            if sn == "Dos velas verdes" and cn == "5 bps":
                a, b = r4["rsi"].index(RSI_THR), r4["sma"].index(SMA_LEN)
                ax.add_patch(plt.Rectangle((b - 0.5, a - 0.5), 1, 1, fill=False, ec=TINTA, lw=2.5))
    fig.suptitle(f"Robustez en cuatro dimensiones — Profit Factor en construcción para {r4['n_combos']} combinaciones", fontweight="bold", x=0.01, ha="left")
    fig.colorbar(im, ax=axs, label="Profit Factor (IS)", shrink=0.7, pad=0.02)
    guardar(fig, "11_robustez_4d.png")

    # 12. distribución de las combinaciones
    pfs = np.array([x["pf"] for x in r4["_todos"]])
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.hist(pfs, bins=36, color=VERDE2, ec="white")
    ax.axvline(1.3, color=ROJO, ls="--"); ax.text(1.3, ax.get_ylim()[1] * 0.9, " criterio 1,3", color=ROJO)
    ax.axvline(r4["pf_vigente"], color=TINTA, lw=2.5); ax.text(r4["pf_vigente"], ax.get_ylim()[1] * 0.7, f"  configuración que opera · {r4['pf_vigente']:.2f}", color=TINTA, fontweight="bold")
    ax.set_title(f"¿Cuántas combinaciones ganan? {r4['pct_pf13']*100:.0f} % superan PF 1,3 · {r4['pct_pf1']*100:.0f} % son rentables"); ax.set_xlabel("Profit Factor (IS)"); ax.set_ylabel("Combinaciones")
    guardar(fig, "12_robustez_dist.png")

    # 9. walk-forward
    wf = res["fase2"]["ventanas"]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    b = ax.bar([v["ano"] for v in wf], [v["ret_oos"] * 100 for v in wf], color=[VERDE if v["ret_oos"] > 0 else ROJO for v in wf], width=0.7)
    l, = ax.plot([v["ano"] for v in wf], [v["ret_is_anual"] * 100 for v in wf], color=TINTA, lw=1.5, marker="o", ms=4)
    ax.axhline(0, color=TINTA, lw=1); ax.set_ylabel("Retorno del año (%)")
    ax.legend([b, l], ["Año validado (OOS, reglas fijas)", "Media anual de los 3 años previos (IS)"], frameon=False)
    ax.set_title("Walk-forward con reglas fijas — cada año validado contra los 3 anteriores")
    guardar(fig, "09_walkforward.png")


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(RAIZ / "data" / "QQQ_D1.csv"))
    ap.add_argument("--etiqueta", default="QQQ")
    ap.add_argument("--solo-metricas", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    raw = cargar(args.csv); df = preparar(raw)
    sp = int(len(df) * IS_FRAC); dfi, dfo = df.iloc[:sp], df.iloc[sp:]; sp_date = dfo.index[0]
    ti, to, ta = backtest(dfi), backtest(dfo), backtest(df)
    eq_cap, eq_atr, eq_atr2 = equity_diaria(df, ta), equity_diaria(df, ta, "atr"), equity_diaria(df, ta, "atr2")
    eq_x2, eq_fijo = equity_diaria(df, ta, "x2"), equity_fija(df, ta)
    eqi_cap, eqo_cap = equity_diaria(dfi, ti), equity_diaria(dfo, to)
    eqo_atr, eqo_atr2, eqo_x2 = equity_diaria(dfo, to, "atr"), equity_diaria(dfo, to, "atr2"), equity_diaria(dfo, to, "x2")

    res = dict(meta=dict(activo=args.etiqueta, fuente=Path(args.csv).name, desde=str(df.index[0].date()),
                         hasta=str(df.index[-1].date()), velas=int(len(df)), rsi=RSI_THR, sma=SMA_LEN,
                         slippage_bps_lado=SLIP * 1e4, is_desde=str(dfi.index[0].date()), is_hasta=str(dfi.index[-1].date()),
                         oos_desde=str(dfo.index[0].date()), oos_hasta=str(dfo.index[-1].date()),
                         generado=str(pd.Timestamp.today().date())))
    res["fase1"] = dict(IS=metricas(ti, eqi_cap), OOS=metricas(to, eqo_cap), TODO=metricas(ta, eq_cap),
                        OOS_atr=metricas(to, eqo_atr, "atr"), TODO_atr=metricas(ta, eq_atr, "atr"),
                        OOS_atr2=metricas(to, eqo_atr2, "atr2"), TODO_atr2=metricas(ta, eq_atr2, "atr2"),
                        OOS_x2=metricas(to, eqo_x2, "x2"), TODO_x2=metricas(ta, eq_x2, "x2"))
    res["_eq_atr2"], res["_eq_x2"], res["_eq_fijo"] = eq_atr2, eq_x2, eq_fijo
    res["fijo"] = dict(final=float(eq_fijo.iloc[-1]), ganancia_total_por_10k=float((eq_fijo.iloc[-1] - 1) * 10000),
                       mdd=float(((eq_fijo - eq_fijo.cummax()) / eq_fijo.cummax()).min()))
    res["drawdowns_x2"] = episodios_dd(eq_x2, top=3)
    # curvas semanales para el gráfico interactivo de la ficha
    sem = pd.DataFrame({"capital": eq_cap, "fijo": eq_fijo, "atr1": eq_atr, "atr2": eq_atr2, "x2": eq_x2}).resample("W-FRI").last().dropna()
    (OUT / "equity_semanal.json").write_text(json.dumps(dict(fechas=[d.strftime("%Y-%m-%d") for d in sem.index], oos=str(dfo.index[0].date()),
                                                             **{k: [round(float(v), 4) for v in sem[k]] for k in sem.columns})), encoding="utf-8")
    res["sizing"] = dict(riesgo_pct=RISK_PCT, atr_len=ATR_LEN, atr_mult=ATR_MULT,
                         exposicion_media_1pct=float(np.mean([min(1, t["expo"]) for t in ta])),
                         exposicion_media_2pct=float(np.mean([min(1, 2 * t["expo"]) for t in ta])),
                         ejemplo=dict(precio=float(ta[-1]["px_ent"]), atr=float(df["atr"].iloc[ta[-1]["i_ent"] - 1])))
    res["fase1"]["pasa"] = fase1_ok(res["fase1"]["OOS"])
    res["fase1"]["criterios"] = dict(pf=res["fase1"]["OOS"]["pf"] >= 1.3, n=res["fase1"]["OOS"]["n"] >= 30,
                                     mdd=res["fase1"]["OOS"]["mdd"] > -0.20, pfnb=(res["fase1"]["OOS"]["pfnb"] or 0) > 1.0)
    # control: salida cierre>cierre anterior (definición de investigación) y libro
    df_cc = df.copy(); df_cc["verde"] = (df_cc["Close"] > df_cc["Close"].shift(1)).astype(int)
    res["control_salida_cierre_a_cierre"] = metricas(backtest(df_cc.iloc[sp:]))
    tl = backtest(df, rsi_thr=5, salida="ma5", estricto=False)
    res["libro"] = dict(TODO=metricas(tl, equity_diaria(df, tl)), OOS=metricas(backtest(dfo, rsi_thr=5, salida="ma5", estricto=False)))
    res["_eq_libro"] = equity_diaria(df, tl)

    res["aed"] = aed(df)
    res["fase2"] = fase2_walkforward(df)
    res["fase3"] = fase3_grid(raw, dfi.index[-1])
    res["robustez_4d"] = robustez_4d(raw, dfi.index[-1])
    res["fase4"] = fase4_montecarlo(ta)
    res["fase4_atr"] = {k: v for k, v in fase4_montecarlo(ta, sizing="atr").items() if not k.startswith("_")}
    res["fase5"] = fase5_stress(df, dfo, to)
    res["monkey"] = monkey_test(df, ta)
    res["edge_decay"] = edge_decay(ta, dfi.index[-1])
    res["drawdowns"] = episodios_dd(eq_cap)
    res["drawdowns_atr"] = episodios_dd(eq_atr, top=3)
    res["veredicto"] = dict(fase1=res["fase1"]["pasa"], fase2=res["fase2"]["pasa"], fase3=res["fase3"]["pasa"],
                            fase4=res["fase4"]["pasa"], fase5=res["fase5"]["pasa"])

    if not args.solo_metricas:
        graficos(df, ta, eq_cap, eq_atr, sp_date, res, raw)
        pd.DataFrame([{k: (str(v.date()) if isinstance(v, pd.Timestamp) else v) for k, v in t.items() if not k.startswith("i_")}
                      for t in ta]).round(5).to_csv(OUT / "trades.csv", index=False)
        pd.DataFrame({"capital_100": eq_cap, "fijo_10k": eq_fijo, "riesgo_1pct_atr": eq_atr, "riesgo_2pct_atr": eq_atr2, "apalancado_x2": eq_x2}).round(5).to_csv(OUT / "equity_diaria.csv")

    limpio = {k: v for k, v in res.items() if not k.startswith("_")}
    for f in ("fase4", "monkey", "robustez_4d", "aed"): limpio[f] = {k: v for k, v in limpio[f].items() if not k.startswith("_")}
    nombre = "metricas.json" if args.etiqueta == "QQQ" else f"metricas_{args.etiqueta}.json"
    (OUT / nombre).write_text(json.dumps(limpio, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

    f1 = res["fase1"]; o = f1["OOS"]
    print(f"{args.etiqueta}: {res['meta']['desde']} → {res['meta']['hasta']} · IS {f1['IS']['n']} trades / OOS {o['n']} trades")
    print(f"  OOS  PF {o['pf']:.2f}  PFnb {o['pfnb']:.2f}  MaxDD {o['mdd']*100:.1f}% (diario {o['mdd_diario']*100:.1f}%)  CAGR {o['cagr']*100:.2f}%  WR {o['wr']*100:.0f}%")
    print(f"  TODO PF {f1['TODO']['pf']:.2f}  CAGR {f1['TODO']['cagr']*100:.2f}%  MaxDD {f1['TODO']['mdd']*100:.1f}%  |  ATR: CAGR {f1['TODO_atr']['cagr']*100:.2f}% MaxDD {f1['TODO_atr']['mdd_diario']*100:.1f}%")
    print(f"  Fases: {res['veredicto']}")
    print(f"  WF ef {res['fase2'].get('eficiencia')}, {res['fase2'].get('pct_positivas')} positivas · grid meseta {res['fase3']['meseta_3x3']} caída {res['fase3']['peor_caida_vecino_pct']:.0f}% · MC p5ret {res['fase4']['p5_ret']:.2f} mddp5 {res['fase4']['mdd_p5']:.3f} ruina {res['fase4']['prob_ruina']}")
    print(f"  Monkey {res['monkey']['pct_pf']:.3f} · stress {[(k, round(v['pf'],2), v['pasa']) for k, v in res['fase5'].items() if isinstance(v, dict) and 'pf' in v]}")


if __name__ == "__main__":
    main()
