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
    bordes = [(0, 0.02, "0 – 2 %"), (0.02, 0.05, "2 – 5 %"), (0.05, 0.10, "5 – 10 %"), (0.10, 0.15, "10 – 15 %"), (0.15, 1.0, "> 15 %")]
    bins = []
    for lo, hi, nom in bordes:
        sel = [e for e in eps if lo <= -e["prof"] < hi]
        bins.append(dict(bin=nom, n=len(sel), dias_medio=float(np.mean([e["dias"] for e in sel])) if sel else 0.0,
                         dias_max=int(max([e["dias"] for e in sel])) if sel else 0, pct=float(len(sel) / len(eps)) if eps else 0.0))
    return dict(n=len(eps), recuperados=sum(e["fin"] is not None for e in eps),
                dias_medio=float(np.mean([e["dias"] for e in eps])) if eps else None, peores=eps[:top], bins=bins)


def mensual(eq):
    """Retornos mensuales y anuales de la curva de capital, con meses positivos/negativos por año."""
    m = eq.resample("ME").last().pct_change().dropna()
    m.iloc[0] = eq.resample("ME").last().iloc[1] / eq.iloc[0] - 1 if len(m) else 0
    anos = sorted(set(m.index.year)); filas = []; matriz = []
    for y in anos:
        s = m[m.index.year == y]; fila = [None] * 12
        for d, v in s.items(): fila[d.month - 1] = float(v)
        anual = float((1 + s).prod() - 1)
        op = s[s != 0]
        filas.append(dict(ano=y, anual=anual, pos=int((s > 0).sum()), neg=int((s < 0).sum()), planos=int((s == 0).sum()),
                          peor_mes=float(op.min()) if len(op) else 0.0, mejor_mes=float(op.max()) if len(op) else 0.0))
        matriz.append(fila)
    ult = [f for f in filas if f["ano"] >= anos[-1] - 9]
    return dict(anos=anos, filas=filas, matriz=matriz, meses_pos=int((m > 0).sum()), meses_neg=int((m < 0).sum()), meses_planos=int((m == 0).sum()),
                anos_negativos=[f["ano"] for f in filas if f["anual"] < 0], ultimos10_negativos=[f["ano"] for f in ult if f["anual"] < 0],
                ultimos10_desde=ult[0]["ano"] if ult else None, peor_mes=float(m.min()), peor_mes_fecha=str(m.idxmin().date()), mejor_mes=float(m.max()))


def pf_movil(trades, w=40):
    r = np.array([t["ret"] for t in trades]); out = []
    for i in range(w, len(r) + 1):
        s = r[i - w:i]; g = s[s > 0].sum(); l = np.abs(s[s <= 0]).sum() or 1e-12
        out.append(dict(fecha=str(trades[i - 1]["salida"].date()), pf=float(min(g / l, 8)), exp=float(s.mean())))
    return out


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
    cubos, cubos_mdd, cubos_n, todos = {}, {}, {}, []
    for sk, sn in SAL:
        for sp, spn in SLIP:
            pf = np.full((len(RS), len(SM)), np.nan); md = np.full_like(pf, np.nan); nn = np.zeros_like(pf)
            for a, rt in enumerate(RS):
                for b, sl in enumerate(SM):
                    d2 = preps[sl]; d2 = d2[d2.index <= n_is]
                    m = metricas(backtest(d2, rsi_thr=rt, slip=sp, salida=sk))
                    if m:
                        pf[a, b], md[a, b], nn[a, b] = m["pf"], m["mdd"], m["n"]
                        todos.append(dict(rsi=rt, sma=sl, salida=sn, coste=spn, pf=m["pf"], n=m["n"], mdd=m["mdd"]))
            cubos[f"{sn} · {spn}"] = np.round(pf, 3).tolist(); cubos_mdd[f"{sn} · {spn}"] = np.round(md, 4).tolist(); cubos_n[f"{sn} · {spn}"] = nn.astype(int).tolist()
    pfs = np.array([x["pf"] for x in todos])
    viva = [x for x in todos if x["rsi"] == RSI_THR and x["sma"] == SMA_LEN and x["salida"] == "Dos velas verdes" and x["coste"] == "5 bps"][0]["pf"]
    return dict(rsi=RS, sma=SM, salidas=[s for _, s in SAL], costes=[s for _, s in SLIP], cubos=cubos, cubos_mdd=cubos_mdd, cubos_n=cubos_n,
                n_combos=int(len(todos)), pct_pf13=float((pfs >= 1.3).mean()), pct_pf1=float((pfs >= 1.0).mean()),
                pf_min=float(pfs.min()), pf_mediana=float(np.median(pfs)), pf_max=float(pfs.max()),
                pf_vigente=float(viva), percentil_vigente=float((pfs < viva).mean()),
                por_salida={s: float(np.mean([x["pf"] for x in todos if x["salida"] == s])) for _, s in SAL},
                por_coste={c: float(np.mean([x["pf"] for x in todos if x["coste"] == c])) for _, c in SLIP},
                _todos=todos)


def fase4_montecarlo(trades, n_sim=10000, bloque=5, sizing="capital", guardar_caminos=False):
    r = np.array([t["ret"] * expo_de(t, sizing) for t in trades]); n = len(r)
    rets, mdds, ruina = [], [], 0; caminos = np.zeros((n_sim, n)) if guardar_caminos else None
    peor_eq, peor_mdd = None, 0
    for k in range(n_sim):
        starts = rng.integers(0, n, size=int(np.ceil(n / bloque)))
        idx = np.concatenate([np.arange(s, s + bloque) % n for s in starts])[:n]
        eq = np.cumprod(1 + r[idx]); pk = np.maximum.accumulate(eq); m = ((eq - pk) / pk).min()
        rets.append(eq[-1] - 1); mdds.append(m); ruina += eq.min() < 0.5
        if guardar_caminos:
            caminos[k] = eq
            if m < peor_mdd: peor_mdd, peor_eq = m, eq
    rets, mdds = np.array(rets), np.array(mdds)
    out = dict(n_sim=n_sim, bloque=bloque, p5_ret=float(np.percentile(rets, 5)), p50_ret=float(np.median(rets)),
               p95_ret=float(np.percentile(rets, 95)), mdd_p5=float(np.percentile(mdds, 5)),
               mdd_p50=float(np.median(mdds)), mdd_p95=float(np.percentile(mdds, 95)),
               mdd_peor=float(mdds.min()), mdd_mejor=float(mdds.max()), ret_peor=float(rets.min()), ret_mejor=float(rets.max()),
               prob_mdd_25=float((mdds < -0.25).mean()), prob_ruina=float(ruina / n_sim),
               prob_ret_pos=float((rets > 0).mean()))
    out["pasa"] = bool(out["p5_ret"] > 0 and out["mdd_p5"] > -0.25 and out["prob_ruina"] < 0.05)
    out["_rets"], out["_mdds"] = rets, mdds
    if guardar_caminos:
        out["_caminos"] = caminos[:400]; out["_bandas"] = np.percentile(caminos, [5, 25, 50, 75, 95], axis=0)
        out["_peor"] = peor_eq; out["_real"] = np.cumprod(1 + r)
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
    real = metricas(trades); pfs, rets, mdds, curvas = [], [], [], []
    for k in range(n_sim):
        ent = np.sort(rng.choice(elig, size=n, replace=False)); d = rng.choice(dur, size=n)
        sal = np.minimum(ent + d, len(df) - 1)
        r = (o[sal] * (1 - SLIP)) / (o[ent] * (1 + SLIP)) - 1
        g, l = r[r > 0].sum(), np.abs(r[r <= 0]).sum() or 1e-12
        eq = np.cumprod(1 + r); pk = np.maximum.accumulate(eq)
        pfs.append(g / l); rets.append(eq[-1] - 1); mdds.append(((eq - pk) / pk).min())
        if k < 250: curvas.append(eq)
    pfs, rets, mdds = np.array(pfs), np.array(rets), np.array(mdds)
    return dict(n_sim=n_sim, pf_real=real["pf"], pct_pf=float((pfs < real["pf"]).mean()),
                pct_ret=float((rets < real["ret_total"]).mean()), pct_mdd=float((mdds < real["mdd"]).mean()),
                pf_mono_mediana=float(np.median(pfs)), ret_mono_mediana=float(np.median(rets)), mdd_mono_mediana=float(np.median(mdds)),
                _pfs=pfs, _curvas=np.array(curvas), _real=np.cumprod(1 + np.array([t["ret"] for t in trades])))


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

    # 5. Monte Carlo: abanico de caminos + distribuciones
    mc = res["fase4"]; n_tr = mc["_caminos"].shape[1]; xi = np.arange(1, n_tr + 1)
    fig = plt.figure(figsize=(13, 9)); gs = fig.add_gridspec(2, 2, height_ratios=[1.6, 1])
    a0 = fig.add_subplot(gs[0, :]); a1 = fig.add_subplot(gs[1, 0]); a2 = fig.add_subplot(gs[1, 1])
    for cam in mc["_caminos"]: a0.plot(xi, cam, color=GRIS, lw=0.4, alpha=0.25)
    b = mc["_bandas"]; a0.fill_between(xi, b[0], b[4], color=VERDE, alpha=0.12, lw=0); a0.fill_between(xi, b[1], b[3], color=VERDE, alpha=0.18, lw=0)
    a0.plot(xi, b[2], color=VERDE, lw=1.6, ls="--"); a0.plot(xi, mc["_real"], color=TINTA, lw=2.2); a0.plot(xi, mc["_peor"], color=ROJO, lw=1.6)
    a0.set_yscale("log"); ticks = [0.5, 1, 2, 3, 5, 8, 12]; a0.set_yticks(ticks); a0.set_yticklabels([f"{t:g}×" for t in ticks]); a0.minorticks_off()
    arriba = mc["_real"][-1] >= b[2][-1]
    a0.text(n_tr, mc["_real"][-1], f"  real · {mc['_real'][-1]:.1f}×", color=TINTA, fontweight="bold", va="bottom" if arriba else "top")
    a0.text(n_tr, b[2][-1], f"  mediana · {b[2][-1]:.1f}×", color=VERDE, fontweight="bold", va="top" if arriba else "bottom")
    a0.text(n_tr, mc["_peor"][-1], f"  peor drawdown · {mc['mdd_peor']*100:.0f} %", color=ROJO, fontweight="bold", va="center")
    a0.set_xlim(1, n_tr * 1.14); a0.set_xlabel("Número de operación"); a0.set_ylabel("Capital (1 = inicial, escala log)")
    a0.set_title(f"{mc['n_sim']:,} reordenaciones de las {n_tr} operaciones reales · 400 dibujadas · bandas: 5–95 % y 25–75 % de todas".replace(",", "."))
    a0.legend([plt.Line2D([], [], color=GRIS, lw=1), plt.Line2D([], [], color=VERDE, lw=1.6, ls="--"), plt.Line2D([], [], color=TINTA, lw=2.2), plt.Line2D([], [], color=ROJO, lw=1.6)],
              ["Un camino posible", "Mediana de todos", "El camino real", "El camino con el peor drawdown"], loc="upper left", frameon=False, fontsize=9.5)
    a1.hist(mc["_rets"] * 100, bins=60, color=VERDE2, alpha=0.8, ec="white")
    a1.axvline(mc["p5_ret"] * 100, color=TINTA, ls="--"); a1.text(mc["p5_ret"] * 100, a1.get_ylim()[1] * 0.9, f" 5 % peor: {mc['p5_ret']*100:+.0f} %", color=TINTA, fontsize=9)
    a1.set_title("Retorno total de cada camino", fontsize=11); a1.set_xlabel("Retorno total (%)")
    a2.hist(mc["_mdds"] * 100, bins=60, color="#f0a860", alpha=0.85, ec="white")
    a2.axvline(-25, color=ROJO, ls="--"); a2.text(-25, a2.get_ylim()[1] * 0.9, " límite −25 % ", color=ROJO, ha="right", fontsize=9)
    a2.axvline(mc["mdd_p5"] * 100, color=TINTA, ls="--"); a2.text(mc["mdd_p5"] * 100, a2.get_ylim()[1] * 0.72, f" 5 % peor: {mc['mdd_p5']*100:.1f} %", color=TINTA, fontsize=9)
    a2.axvline(mc["mdd_peor"] * 100, color=ROJO, lw=2); a2.text(mc["mdd_peor"] * 100, a2.get_ylim()[1] * 0.5, f" el peor de todos: {mc['mdd_peor']*100:.1f} %", color=ROJO, fontsize=9)
    a2.set_title("Drawdown máximo de cada camino", fontsize=11); a2.set_xlabel("Drawdown máximo (%)")
    fig.tight_layout(); guardar(fig, "05_montecarlo.png")

    # 6. monkey: curvas de los monos + distribución con línea
    from scipy.stats import gaussian_kde
    mk = res["monkey"]; nm = mk["_curvas"].shape[1]; xm = np.arange(1, nm + 1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw=dict(width_ratios=[1.35, 1]))
    for cv in mk["_curvas"]: a1.plot(xm, cv, color=GRIS, lw=0.5, alpha=0.35)
    a1.plot(xm, np.median(mk["_curvas"], axis=0), color="#7a4fb8", lw=1.8, ls="--"); a1.plot(xm, mk["_real"], color=VERDE, lw=2.4)
    a1.set_yscale("log"); ticks = [0.5, 1, 2, 3, 5, 8]; a1.set_yticks(ticks); a1.set_yticklabels([f"{t:g}×" for t in ticks]); a1.minorticks_off()
    a1.text(nm, mk["_real"][-1], f"  estrategia · {mk['_real'][-1]:.1f}×", color=VERDE, fontweight="bold", va="center")
    a1.text(nm, np.median(mk["_curvas"], axis=0)[-1], f"  mono mediano · {np.median(mk['_curvas'], axis=0)[-1]:.1f}×", color="#7a4fb8", fontweight="bold", va="center")
    a1.set_xlim(1, nm * 1.2); a1.set_xlabel("Número de operación"); a1.set_ylabel("Capital (escala log)")
    a1.set_title("250 monos entrando al azar (gris) frente a la estrategia (verde)", fontsize=11)
    cnt, edges, _ = a2.hist(mk["_pfs"], bins=45, color="#c2d0c8", ec="white")
    xs = np.linspace(mk["_pfs"].min(), max(mk["_pfs"].max(), mk["pf_real"] * 1.05), 300); kde = gaussian_kde(mk["_pfs"])(xs) * len(mk["_pfs"]) * (edges[1] - edges[0])
    a2.plot(xs, kde, color="#7a4fb8", lw=2)
    a2.axvline(mk["pf_mono_mediana"], color="#7a4fb8", ls="--"); a2.axvline(mk["pf_real"], color=VERDE, lw=3)
    a2.text(mk["pf_real"], a2.get_ylim()[1] * 0.9, f" estrategia · PF {mk['pf_real']:.2f}\n supera al {mk['pct_pf']*100:.1f} %", color=VERDE, fontweight="bold", fontsize=9.5, ha="right")
    a2.text(mk["pf_mono_mediana"], a2.get_ylim()[1] * 0.55, f" mono mediano · {mk['pf_mono_mediana']:.2f}", color="#7a4fb8", fontsize=9.5)
    a2.set_title(f"Profit Factor de los {mk['n_sim']:,} monos".replace(",", "."), fontsize=11); a2.set_xlabel("Profit Factor"); a2.set_ylabel("Monos")
    fig.tight_layout(); guardar(fig, "06_monkey.png")

    # 7. desgaste del edge: PF móvil de las últimas 40 operaciones + operaciones por año
    ed = res["edge_decay"]["anual"]; mv = res["edge_decay"]["movil"]
    fx = pd.to_datetime([m["fecha"] for m in mv]); fy = [m["pf"] for m in mv]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7), height_ratios=[2.2, 1], sharex=True)
    a1.axvspan(sp_date, fx[-1], color="#eef6f1", zorder=0)
    a1.fill_between(fx, 1, fy, where=np.array(fy) >= 1, color=VERDE, alpha=0.15, lw=0); a1.fill_between(fx, 1, fy, where=np.array(fy) < 1, color=ROJO, alpha=0.25, lw=0)
    a1.plot(fx, fy, color=VERDE, lw=2)
    a1.axhline(1, color=ROJO, lw=1.2); a1.axhline(1.3, color=TINTA, lw=1, ls="--")
    bb = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)
    a1.text(fx[0], 1.36, " criterio: 1,3", color=TINTA, fontsize=9, bbox=bb); a1.text(fx[0], 0.82, " por debajo de 1 se pierde dinero", color=ROJO, fontsize=9, bbox=bb)
    a1.text(sp_date, a1.get_ylim()[1] * 0.97, "  fuera de muestra →", va="top", color="#3a4b44", fontsize=10)
    a1.set_ylabel("Profit Factor de las últimas 40 operaciones"); a1.set_ylim(0, min(8, max(fy) * 1.1))
    a1.set_title("¿Se desgasta el edge? Profit Factor móvil: si la línea bajara hacia 1 y se quedara, el edge estaría muriendo")
    a2.bar([pd.Timestamp(f"{f['ano']}-07-01") for f in ed], [f["n"] for f in ed], width=250, color=[VERDE if f["pf"] >= 1 else ROJO for f in ed])
    for f in ed: a2.text(pd.Timestamp(f"{f['ano']}-07-01"), f["n"] + 0.4, str(f["n"]), ha="center", fontsize=8, color="#3a4b44")
    a2.set_ylabel("Operaciones por año"); a2.set_title("Frecuencia: verde = año con PF > 1, rojo = año perdedor. Sin barra = año sin operaciones (precio bajo la SMA 200)", fontsize=10)
    a2.xaxis.set_major_locator(mdates.YearLocator(2)); a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout(); guardar(fig, "07_pf_anual.png")

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
    fig, ax = plt.subplots(figsize=(13, 6.2)); w = 0.2
    for k, (nom, col) in enumerate(zip(nombres, cols_g)):
        vals = [ae["forward"][nom][h]["media"] * 100 for h in H]
        ax.bar(np.arange(len(H)) + (k - 1.5) * w, vals, width=w, color=col, label=nom)
        for x, v in zip(np.arange(len(H)) + (k - 1.5) * w, vals):
            ax.text(x, v + (0.02 if v >= 0 else -0.06), f"{v:+.2f}", ha="center", fontsize=8.5, color="#3a4b44")
    ax.axhline(0, color=TINTA, lw=1); ax.set_xticks(range(len(H))); ax.set_xticklabels([f"{h} día{'s' if h > 1 else ''} después" for h in H], fontsize=11)
    ax.set_ylabel("Retorno medio (%)", fontsize=11); ax.legend(frameon=False, fontsize=10.5, loc="upper left")
    ax.set_title("Qué hace el Nasdaq después de una sobreventa extrema\nBarra verde > gris: el momento de entrada aporta · roja alta pero menos fiable: la tendencia compra consistencia", fontsize=12, loc="left")
    fig.tight_layout(); guardar(fig, "13_aed_forward.png")

    # 14. AED: autocorrelación y rachas
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.4))
    a1.bar(range(1, 11), [v * 100 for v in ae["autocorr"]], color=[ROJO if v < 0 else VERDE for v in ae["autocorr"]], width=0.7)
    a1.axhline(0, color=TINTA, lw=1); a1.set_xlabel("Retraso (días)"); a1.set_ylabel("Autocorrelación (%)"); a1.set_xticks(range(1, 11))
    a1.set_title("¿Tiende o revierte? Autocorrelación de los retornos diarios\nBarra roja a 1 día = lo que cae hoy tiende a subir mañana (reversión)", fontsize=11, loc="left")
    ks = list(ae["rachas"].keys()); vals = [ae["rachas"][k]["media"] * 100 for k in ks]
    a2.bar(ks, vals, color=VERDE, width=0.6)
    for k, vv in zip(ks, vals): a2.text(k, vv / 2, f"{ae['rachas'][k]['pct_pos']*100:.0f} % suben\nn = {ae['rachas'][k]['n']}", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    a2.axhline(0, color=TINTA, lw=1); a2.set_xlabel("Días seguidos de caída (con el precio sobre la SMA 200)"); a2.set_ylabel("Retorno medio 3 días después (%)")
    a2.set_title("¿Cuánto rebota tras varias caídas seguidas?\nRetorno medio en los 3 días siguientes: cuanto más cae seguido, más rebota", fontsize=11, loc="left"); a2.set_xticks(ks); a2.set_ylim(0, max(vals) * 1.25)
    fig.tight_layout(); guardar(fig, "14_aed_rachas.png")

    # 15. AED: régimen de tendencia y volatilidad
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 8.5), height_ratios=[2.2, 1], sharex=True)
    a1.plot(df.index, df["Close"], color=TINTA, lw=0.9); a1.plot(df.index, df["sma"], color=AZUL, lw=1.4)
    a1.set_yscale("log"); ylo, yhi = df["Close"].min() * 0.9, df["Close"].max() * 1.1; a1.set_ylim(ylo, yhi)
    a1.fill_between(df.index, ylo, yhi, where=~ae["_sobre"].values, color=ROJO, alpha=0.22, lw=0)
    yt = [v for v in [25, 50, 100, 200, 400, 800, 1600] if ylo <= v <= yhi]; a1.set_yticks(yt); a1.set_yticklabels([str(v) for v in yt]); a1.minorticks_off()
    a1.set_ylabel("QQQ (USD, escala log)")
    a1.set_title(f"Régimen de tendencia: el {ae['pct_sobre_sma']*100:.0f} % del tiempo el precio está sobre la SMA 200\nEn rojo, el {100-ae['pct_sobre_sma']*100:.0f} % restante: por debajo de la media la estrategia no opera, y ahí están 2000–2002, 2008 y 2022", fontsize=11.5, loc="left")
    a1.legend([plt.Line2D([], [], color=TINTA), plt.Line2D([], [], color=AZUL, lw=1.4), plt.Rectangle((0, 0), 1, 1, color=ROJO, alpha=0.22)], ["Cierre QQQ", "SMA 200", "Precio bajo la SMA 200: sin operar"], frameon=False, loc="upper left")
    a2.plot(df.index, ae["_atr_pct"].values * 100, color="#c97d1e", lw=0.9); a2.set_ylabel("ATR(14) / precio (%)")
    a2.axhline(ae["atr_pct"]["media"] * 100, color=TINTA, lw=1, ls="--"); a2.text(df.index[0], ae["atr_pct"]["media"] * 100 * 1.1, f" media {ae['atr_pct']['media']*100:.1f} %", fontsize=9, color=TINTA)
    a2.set_title("Volatilidad diaria (ATR como % del precio): se multiplica por 4 en las crisis. Por eso el tamaño de posición se calcula con el ATR y no con un porcentaje fijo", fontsize=11, loc="left")
    a2.xaxis.set_major_locator(mdates.YearLocator(2))
    fig.tight_layout(); guardar(fig, "15_aed_regimen.png")

    # 18. AED: colas gordas
    from scipy.stats import norm as _norm
    r = df["Close"].pct_change().dropna() * 100; mu, sd = r.mean(), r.std()
    fig, ax = plt.subplots(figsize=(13, 5.2))
    cnt, edges, _ = ax.hist(r, bins=120, color="#c2d0c8", ec="white", label="Retornos diarios reales de QQQ")
    xs = np.linspace(r.min(), r.max(), 500); ax.plot(xs, _norm.pdf(xs, mu, sd) * len(r) * (edges[1] - edges[0]), color=AZUL, lw=2, label="Lo que sería una campana normal con la misma media y desviación")
    ax.set_yscale("log"); ax.set_ylim(0.5, cnt.max() * 2)
    for v, lab, col in [(r.min(), f"peor día {r.min():+.1f} %", ROJO), (r.max(), f"mejor día {r.max():+.1f} %", VERDE)]:
        ax.axvline(v, color=col, lw=1.5, ls="--"); ax.text(v, 3, f" {lab} ", color=col, fontsize=9.5, fontweight="bold", ha="left" if v < 0 else "right", rotation=90, va="bottom")
    p_norm = 2 * _norm.cdf(-abs(r.min()), 0, sd); anos_n = 1 / (p_norm * 252)
    anos_txt = f"{anos_n/1e6:,.0f} millones de años".replace(",", ".") if anos_n > 1e6 else f"{anos_n:,.0f} años".replace(",", ".")
    ax.text(0.02, 0.42, f"Días con caída ≥ 5 %: {(r <= -5).sum()} reales\nfrente a {len(r) * 2 * _norm.cdf(-5, mu, sd):.0f} que predeciría la campana.\n\nUn día del {r.min():+.1f} % ocurriría, según la campana,\nuna vez cada {anos_txt}. Ocurrió.",
            transform=ax.transAxes, va="top", fontsize=10, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#e2ede8"))
    ax.set_xlabel("Retorno diario (%)"); ax.set_ylabel("Días (escala log)"); ax.legend(frameon=False, loc="upper right", fontsize=9.5)
    ax.set_title("Colas gordas: los días extremos ocurren mucho más de lo que dice la campana normal\nPor eso el tamaño de posición mira la volatilidad reciente y por eso no hay apalancamiento por defecto", fontsize=11.5, loc="left")
    fig.tight_layout(); guardar(fig, "18_aed_colas.png")

    # 19. retornos mensuales (mapa de calor) con el año a la derecha
    me = res["mensual"]; Mz = np.array([[np.nan if (v is None or abs(v) < 1e-9) else v * 100 for v in fila] for fila in me["matriz"]])
    fig, ax = plt.subplots(figsize=(13, 0.34 * len(me["anos"]) + 1.6))
    vmax = np.nanmax(np.abs(Mz)); im = ax.imshow(Mz, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
    for i in range(Mz.shape[0]):
        for j in range(12):
            if not np.isnan(Mz[i, j]): ax.text(j, i, f"{Mz[i,j]:+.1f}", ha="center", va="center", fontsize=7.5, color=TINTA if abs(Mz[i, j]) < vmax * 0.6 else "white")
        f = me["filas"][i]; ax.text(12.1, i, f"{f['anual']*100:+.1f} %", va="center", fontsize=8.5, fontweight="bold", color=VERDE if f["anual"] >= 0 else ROJO)
        ax.text(13.4, i, f"{f['pos']}↑ {f['neg']}↓", va="center", fontsize=8, color="#3a4b44")
    ax.set_xticks(range(12)); ax.set_xticklabels(["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    ax.set_yticks(range(len(me["anos"]))); ax.set_yticklabels(me["anos"], fontsize=8.5); ax.set_xlim(-0.5, 14.2); ax.grid(False)
    ax.text(12.1, -0.9, "año", fontsize=8.5, fontweight="bold"); ax.text(13.4, -0.9, "meses ↑↓", fontsize=8.5, fontweight="bold")
    ax.set_title(f"Retorno mes a mes con el 100 % del capital · {me['meses_pos']} meses positivos, {me['meses_neg']} negativos, {me['meses_planos']} sin operar (en blanco)", fontsize=11, loc="left", pad=18)
    fig.tight_layout(); guardar(fig, "19_meses.png")

    # 20. drawdowns por profundidad (bins)
    bins = res["drawdowns"]["bins"]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    cols = ["#b9efd1", "#5eeba4", "#f0a860", "#f4805e", ROJO]
    ax.bar(range(len(bins)), [b["n"] for b in bins], color=cols, width=0.65)
    for i, b in enumerate(bins):
        ax.text(i, b["n"] + 1, f"{b['n']} caídas · {b['pct']*100:.0f} %\nmedia {b['dias_medio']:.0f} días · máx {b['dias_max']} días", ha="center", fontsize=9, color="#3a4b44")
    ax.set_xticks(range(len(bins))); ax.set_xticklabels([b["bin"] for b in bins]); ax.set_xlabel("Profundidad de la caída desde el máximo"); ax.set_ylabel("Número de caídas")
    ax.set_ylim(0, max(b["n"] for b in bins) * 1.3)
    ax.set_title(f"Las {res['drawdowns']['n']} caídas desde máximos, agrupadas por profundidad, con cuánto tardaron en recuperarse (100 % capital)", fontsize=11, loc="left")
    fig.tight_layout(); guardar(fig, "20_dd_bins.png")

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
    fig.suptitle(f"Los seis mapas: Profit Factor en construcción para {r4['n_combos']} combinaciones (tres salidas × dos costes)", fontweight="bold", x=0.01, ha="left")
    fig.colorbar(im, ax=axs, label="Profit Factor (IS)", shrink=0.7, pad=0.02)
    guardar(fig, "11_robustez_mapas.png")

    # 11b. superficie 3D con cuarta dimensión en color (estilo MultiCharts) + barras con línea
    todos = r4["_todos"]; base = [x for x in todos if x["salida"] == "Dos velas verdes" and x["coste"] == "5 bps"]
    caro = {(x["rsi"], x["sma"]): x["pf"] for x in todos if x["salida"] == "Dos velas verdes" and x["coste"] == "10 bps"}
    RS, SM = r4["rsi"], r4["sma"]; Z = np.array([[next(x["pf"] for x in base if x["rsi"] == rt and x["sma"] == sl) for sl in SM] for rt in RS])
    C = np.array([[next(-x["mdd"] for x in base if x["rsi"] == rt and x["sma"] == sl) for sl in SM] for rt in RS])
    fig = plt.figure(figsize=(10, 7.5)); ax3 = fig.add_subplot(1, 1, 1, projection="3d")
    Xg, Yg = np.meshgrid(range(len(SM)), range(len(RS))); norm = plt.Normalize(C.min(), C.max()); cmap = plt.get_cmap("YlOrRd")
    surf = ax3.plot_surface(Xg, Yg, Z, facecolors=cmap(norm(C)), rstride=1, cstride=1, linewidth=0.4, edgecolor="#ffffff", alpha=0.95, shade=False)
    ax3.set_xticks(range(len(SM))); ax3.set_xticklabels([str(s) for s in SM], fontsize=8); ax3.set_yticks(range(len(RS))); ax3.set_yticklabels([f"<{r}" for r in RS], fontsize=8)
    ax3.set_xlabel("periodo SMA", fontsize=9, labelpad=6); ax3.set_ylabel("umbral RSI(2)", fontsize=9, labelpad=6); ax3.set_zlabel("Profit Factor (IS)", fontsize=9, labelpad=4)
    ia, ib = RS.index(RSI_THR), SM.index(SMA_LEN); ax3.scatter([ib], [ia], [Z[ia, ib] + 0.05], color=TINTA, s=60, depthshade=False)
    ax3.text(ib, ia, Z[ia, ib] + 0.35, "la que opera", fontsize=9, fontweight="bold", color=TINTA)
    ax3.view_init(elev=30, azim=-125); ax3.set_box_aspect((1.25, 1, 0.75)); ax3.set_zlim(0, Z.max() * 1.05)
    ax3.set_title("Superficie: altura = Profit Factor · color = drawdown máximo (versión fija para imprimir)", fontsize=10.5, loc="left")
    m = plt.cm.ScalarMappable(cmap=cmap, norm=norm); m.set_array([]); cb = fig.colorbar(m, ax=ax3, shrink=0.55, pad=0.08); cb.set_label("drawdown máx. (IS), fracción", fontsize=8.5)
    fig.tight_layout(); guardar(fig, "11_robustez_4d.png")

    fig, ax4 = plt.subplots(figsize=(13, 5.6))
    orden = sorted(base, key=lambda x: -x["pf"]); et = [f"{x['rsi']}/{x['sma']}" for x in orden]
    cols = [TINTA if (x["rsi"] == RSI_THR and x["sma"] == SMA_LEN) else VERDE2 for x in orden]
    ax4.bar(range(len(orden)), [x["pf"] for x in orden], color=cols, width=0.75)
    ax4.plot(range(len(orden)), [caro[(x["rsi"], x["sma"])] for x in orden], color="#c97d1e", lw=2, marker="o", ms=3.5)
    ax4.axhline(1.3, color=ROJO, ls="--", lw=1); ax4.text(len(orden) - 0.5, 1.33, "criterio 1,3", color=ROJO, ha="right", fontsize=9)
    ax4.set_xticks(range(len(orden))); ax4.set_xticklabels(et, rotation=90, fontsize=7.5); ax4.set_xlabel("combinación umbral RSI / periodo SMA (ordenadas de mejor a peor)", fontsize=9)
    ax4.set_ylabel("Profit Factor (IS)"); ax4.set_title("Las 30 combinaciones ordenadas de mejor a peor: barras con 5 bps por lado · línea con el doble de coste", fontsize=11.5, loc="left")
    ax4.legend([plt.Rectangle((0, 0), 1, 1, color=VERDE2), plt.Line2D([], [], color="#c97d1e", lw=2, marker="o"), plt.Rectangle((0, 0), 1, 1, color=TINTA)], ["PF con 5 bps por lado", "PF con 10 bps por lado", "la que opera"], frameon=False, fontsize=9.5)
    fig.tight_layout(); guardar(fig, "11b_robustez_barras.png")

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
    ap.add_argument("--fuente", default="Yahoo Finance (QQQ ajustado)")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    raw = cargar(args.csv); df = preparar(raw)
    sp = int(len(df) * IS_FRAC); dfi, dfo = df.iloc[:sp], df.iloc[sp:]; sp_date = dfo.index[0]
    ti, to, ta = backtest(dfi), backtest(dfo), backtest(df)
    eq_cap, eq_atr, eq_atr2 = equity_diaria(df, ta), equity_diaria(df, ta, "atr"), equity_diaria(df, ta, "atr2")
    eq_x2, eq_fijo = equity_diaria(df, ta, "x2"), equity_fija(df, ta)
    eqi_cap, eqo_cap = equity_diaria(dfi, ti), equity_diaria(dfo, to)
    eqo_atr, eqo_atr2, eqo_x2 = equity_diaria(dfo, to, "atr"), equity_diaria(dfo, to, "atr2"), equity_diaria(dfo, to, "x2")

    res = dict(meta=dict(activo=args.etiqueta, fuente=args.fuente, fichero=Path(args.csv).name, desde=str(df.index[0].date()),
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
    res["fase4"] = fase4_montecarlo(ta, guardar_caminos=True)
    res["fase4_atr"] = {k: v for k, v in fase4_montecarlo(ta, sizing="atr").items() if not k.startswith("_")}
    res["fase5"] = fase5_stress(df, dfo, to)
    res["monkey"] = monkey_test(df, ta)
    res["edge_decay"] = edge_decay(ta, dfi.index[-1]); res["edge_decay"]["movil"] = pf_movil(ta, 40)
    res["drawdowns"] = episodios_dd(eq_cap)
    res["mensual"] = mensual(eq_cap)
    res["drawdowns_atr"] = episodios_dd(eq_atr, top=3)
    # Fase 4 se evalúa sobre el tamaño con el que opera el robot (1 % de riesgo por ATR); el 100 % del capital se muestra como referencia
    res["veredicto"] = dict(fase1=res["fase1"]["pasa"], fase2=res["fase2"]["pasa"], fase3=res["fase3"]["pasa"],
                            fase4=res["fase4_atr"]["pasa"], fase5=res["fase5"]["pasa"])

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
