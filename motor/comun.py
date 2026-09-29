"""
Piezas comunes de las páginas (configuración, utilidades, CSS, plantilla). Importado por construir_html.py y pagina_ficha.py.

Construye las dos páginas de la guía a partir de resultados/metricas.json y resultados/graficos/*.png:
  guia/rsi2-ficha.html        → la estrategia explicada de principio a fin (para el alumno)
  guia/rsi2-validacion.html   → la validación completa, fase a fase

Todo autocontenido (imágenes incrustadas), sin dependencias externas. Uso: python motor/construir_html.py
"""
import base64, html, io, json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RES, G, GUIA = RAIZ / "resultados", RAIZ / "resultados" / "graficos", RAIZ / "guia"

# ------------------------------------------------------------------ configuración editable
REPO_URL = "https://github.com/tradeitsimplesolutions/tis-rsi2-research"
PINE_URL = "https://es.tradingview.com/script/u8LQInYf/"
MT4_PATH = None          # ruta a un .mq4 si algún día existe
INSTAGRAM = "https://instagram.com/mariellangsaez"
LIBRO_1 = "https://www.amazon.com/Short-Term-Trading-Strategies-That/dp/0981923909"
LIBRO_2 = "https://www.amazon.com/High-Probability-ETF-Trading-Professional/dp/0615297412"
ART_STOCKCHARTS = "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2"
ART_QS = "https://www.quantifiedstrategies.com/rsi-2-strategy/"

# Costes reales leídos del terminal MT5 de Darwinex (symbol_info). Se actualizan a mano cuando cambien.
DARWINEX = dict(
    fecha="2026-09-22",
    qqq=dict(spread_pts=3, point=0.01, precio=747.2, swap_long_pct=-5.5, comision="0 (incluida en el spread)"),
    ndx=dict(spread_pts=None, precio=None, swap_long_pct=-5.5, comision="0 (incluida en el spread)"),
)

M = json.loads((RES / "metricas.json").read_text(encoding="utf-8"))
SEM = json.loads((RES / "equity_semanal.json").read_text(encoding="utf-8")) if (RES / "equity_semanal.json").exists() else None
NDX = json.loads((RES / "metricas_NDX.json").read_text(encoding="utf-8")) if (RES / "metricas_NDX.json").exists() else None
REC = json.loads((RES / "reconciliacion_mt5.json").read_text(encoding="utf-8")) if (RES / "reconciliacion_mt5.json").exists() else None
EA = (RAIZ / "codigo" / "TIS_RSI2_MeanReversion.mq5").read_text(encoding="utf-8", errors="ignore")


# ------------------------------------------------------------------ utilidades
def pct(x, d=1, signo=False):
    if x is None: return "—"
    s = f"{x*100:+.{d}f}" if signo else f"{x*100:.{d}f}"
    return s.replace(".", ",").replace("-", "−") + " %"


def num(x, d=2):
    if x is None: return "—"
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def fecha(s):
    if not s: return "—"
    y, m, d = s.split("-"); meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{int(d)} {meses[int(m)-1]} {y}"


def img(nombre):
    from PIL import Image
    im = Image.open(G / nombre).convert("RGB"); buf = io.BytesIO(); im.save(buf, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def logo():
    p = RAIZ / "guia" / "logo_tis.png"
    if not p.exists(): return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def fig(nombre, caption):
    return f'<figure><img src="{img(nombre)}" alt="{html.escape(caption)}"><figcaption>{caption}</figcaption></figure>'


def superficie_4d(r4, rsi_op=15, sma_op=200):
    """Superficie 3D interactiva (Plotly), al estilo del optimizador de MultiCharts: altura y color = Profit Factor,
    para ver si la combinación que opera está en una meseta o en un pico. Botones para las seis combinaciones de salida y coste.
    Se gira con el ratón. Necesita internet para cargar plotly.js (CDN)."""
    import plotly.graph_objects as go
    RS, SM = r4["rsi"], r4["sma"]; claves = list(r4["cubos"].keys()); ia, ib = RS.index(rsi_op), SM.index(sma_op)
    zmax = max(v for k in claves for fila in r4["cubos"][k] for v in fila if v is not None); zmin = min(v for k in claves for fila in r4["cubos"][k] for v in fila if v is not None)
    escala = [[0, "#c8512f"], [0.12, "#f4805e"], [0.25, "#f0a860"], [0.45, "#e6f2a0"], [0.7, "#5eeba4"], [1, "#0b6e3e"]]
    fig = go.Figure()
    for i, k in enumerate(claves):
        Z = r4["cubos"][k]; C = [[abs(v) * 100 for v in fila] for fila in r4["cubos_mdd"][k]]; N = r4["cubos_n"][k]
        txt = [[f"RSI(2) &lt; {RS[a]} · SMA {SM[b]}<br><b>Profit Factor {Z[a][b]:.2f}</b><br>Drawdown máx. {C[a][b]:.1f} %<br>{N[a][b]} operaciones" for b in range(len(SM))] for a in range(len(RS))]
        fig.add_trace(go.Surface(x=SM, y=RS, z=Z, cmin=1.0, cmax=min(3.0, zmax), colorscale=escala,
                                 colorbar=dict(title="Profit<br>Factor", thickness=14, len=0.6, tickvals=[1, 1.3, 1.5, 2, 2.5, 3], ticktext=["1", "1,3", "1,5", "2", "2,5", "≥ 3"]), text=txt, hoverinfo="text", name=k, visible=(i == 0), opacity=0.97,
                                 contours=dict(z=dict(show=True, usecolormap=True, highlightcolor="#132620", project_z=True, width=2)), lighting=dict(ambient=0.75, diffuse=0.7, specular=0.15, roughness=0.6)))
        fig.add_trace(go.Scatter3d(x=[SM[ib]], y=[RS[ia]], z=[Z[ia][ib] + 0.06], mode="markers+text", text=["la que opera"], textposition="top center",
                                   textfont=dict(color="#132620", size=13, family="system-ui"), marker=dict(size=8, color="#132620", line=dict(color="white", width=2)), hoverinfo="text",
                                   hovertext=f"La que opera · PF {Z[ia][ib]:.2f} · DD {C[ia][ib]:.1f} %", name="la que opera", visible=(i == 0), showlegend=False))
    botones = [dict(label=k, method="update", args=[{"visible": [j // 2 == i for j in range(2 * len(claves))]}]) for i, k in enumerate(claves)]
    fig.update_layout(height=720, margin=dict(l=0, r=0, t=56, b=0), paper_bgcolor="white", font=dict(family="system-ui, Segoe UI, Roboto, sans-serif", color="#132620"),
                      scene=dict(xaxis=dict(title="periodo de la SMA", tickvals=SM, backgroundcolor="#f5fbf8", gridcolor="#e2ede8"),
                                 yaxis=dict(title="umbral del RSI(2)", tickvals=RS, ticktext=[f"< {r}" for r in RS], backgroundcolor="#f5fbf8", gridcolor="#e2ede8"),
                                 zaxis=dict(title="Profit Factor (IS)", range=[zmin * 0.9, zmax * 1.04], backgroundcolor="#ffffff", gridcolor="#e2ede8"),
                                 camera=dict(eye=dict(x=1.45, y=1.55, z=1.15), center=dict(x=0, y=0, z=-0.15)), aspectratio=dict(x=1.2, y=1, z=0.85), domain=dict(y=[0, 1])),
                      updatemenus=[dict(type="buttons", direction="right", x=0, y=1.0, xanchor="left", yanchor="bottom", showactive=True, buttons=botones,
                                        bgcolor="#eef6f1", bordercolor="#e2ede8", font=dict(size=11), pad=dict(r=4, t=0, b=0))],
                      modebar=dict(orientation="v"))
    div = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="sup4d", config=dict(displayModeBar=True, responsive=True, displaylogo=False, locale="es"))
    return f'<div class="chart" id="sup4d-wrap">{div}<img class="print" src="{img("11_robustez_4d.png")}" alt="Superficie de robustez"><figcaption style="padding:8px 4px 0">Gírala con el ratón, haz zoom con la rueda y pasa el cursor por cada celda. Altura y color son el Profit Factor en construcción: verde alto, rojo cerca de 1. Lo que buscamos es que el punto negro (la configuración que opera) esté en una zona verde y llana, rodeado de vecinos parecidos, no en un pico aislado. Los botones cambian la salida y el coste: la forma de la superficie apenas cambia, y eso es lo que buscamos.</figcaption></div>'


def kpi(valor, label, sub="", tono=""):
    return f'<div class="kpi {tono}"><div class="v">{valor}</div><div class="l">{label}</div>{f"<div class=s>{sub}</div>" if sub else ""}</div>'


def check(ok, texto, detalle=""):
    ic = "✓" if ok else ("✕" if ok is False else "·")
    cl = "ok" if ok else ("ko" if ok is False else "na")
    return f'<li class="chk {cl}"><span class="ic">{ic}</span><div><b>{texto}</b>{f"<br><span class=d>{detalle}</span>" if detalle else ""}</div></li>'


def tabla(cab, filas, clase=""):
    th = "".join(f"<th>{c}</th>" for c in cab)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas)
    return f'<div class="tw"><table class="{clase}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def sec(id_, kicker, titulo, lead, cuerpo, clase=""):
    return f'<section id="{id_}" class="{clase}"><div class="wrap"><div class="kicker">{kicker}</div><h2>{titulo}</h2>' \
           f'{f"<p class=lead>{lead}</p>" if lead else ""}{cuerpo}</div></section>'


# ------------------------------------------------------------------ CSS común
CSS = """
:root{--bg:#fff;--panel:#f5fbf8;--panel2:#eef6f1;--line:#e2ede8;--ink:#132620;--sub:#3a4b44;--muted:#6b7a72;--faint:#95a29b;
--brand:#0e9c58;--brand2:#26d97e;--brand-soft:#e6faef;--brand-ink:#0d3d24;--neg:#c8512f;--neg-soft:#fdeee9;--warn:#9a5a15;--warn-soft:#fff5e9;--warn-line:#f0d3ab;
--azul:#2b6cb0;--azul-soft:#e8f0fa;--sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;--mono:"SF Mono",ui-monospace,Consolas,"Roboto Mono",monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:70px}
body{margin:0;font-family:var(--sans);color:var(--ink);background:var(--bg);line-height:1.55;font-size:17px}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
nav.top{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav.top .wrap{display:flex;align-items:center;gap:18px;height:56px}
nav.top img{height:32px;background:var(--brand-ink);padding:5px 9px;border-radius:7px}nav.top .brand{font-weight:800;letter-spacing:.2px;font-size:15px;color:var(--brand-ink);white-space:nowrap}
nav.top .links{display:flex;gap:4px;margin-left:auto;overflow-x:auto;scrollbar-width:none}
nav.top .links a{font-size:13.5px;font-weight:600;color:var(--sub);padding:6px 10px;border-radius:8px;white-space:nowrap}
nav.top .links a:hover{background:var(--panel2);text-decoration:none;color:var(--brand-ink)}
nav.top .links a.cta{background:var(--brand);color:#fff}
header.hero{background:radial-gradient(1200px 500px at 15% -10%,#dcf6e4 0,transparent 60%),radial-gradient(900px 400px at 95% 10%,#e8f0fa 0,transparent 55%),var(--bg);padding:54px 0 34px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--brand)}
h1{font-size:clamp(40px,7vw,68px);line-height:1;margin:8px 0 10px;letter-spacing:-.02em}
h1 small{display:block;font-size:clamp(18px,2.6vw,26px);font-weight:600;color:var(--sub);letter-spacing:0;margin-top:8px}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0}
.badge{font-size:13px;font-weight:700;padding:6px 12px;border-radius:999px;background:var(--panel2);color:var(--brand-ink);border:1px solid var(--line)}
.badge.b{background:var(--brand);color:#fff;border-color:var(--brand)}
.hero-grid{display:grid;grid-template-columns:1.3fr 1fr;gap:28px;align-items:end}
.hero .hint{font-size:15px;color:var(--muted);margin-top:14px}
.hero-kpis{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 1px 0 rgba(19,38,32,.03)}
.kpi .v{font-size:30px;font-weight:800;letter-spacing:-.02em;color:var(--brand-ink);line-height:1.05}
.kpi.ok .v{color:var(--brand)}.kpi.neg .v{color:var(--neg)}.kpi.azul .v{color:var(--azul)}
.kpi .l{font-size:13px;font-weight:700;color:var(--sub);margin-top:6px}.kpi .s{font-size:12.5px;color:var(--muted);margin-top:2px}
section{padding:54px 0;border-bottom:1px solid var(--line)}section.alt{background:var(--panel)}
.kicker{font-size:12.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--brand)}
h2{font-size:clamp(28px,4vw,38px);line-height:1.1;margin:6px 0 10px;letter-spacing:-.015em}
h3{font-size:20px;margin:26px 0 8px}
p.lead{font-size:19px;color:var(--sub);max-width:820px;margin:0 0 22px}
.hipo{background:linear-gradient(135deg,#0d3d24,#0e9c58);color:#fff;border-radius:20px;padding:34px 36px;margin:10px 0 0;box-shadow:0 12px 40px rgba(14,156,88,.25)}
.hipo .k{font-size:12.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;opacity:.85}
.hipo .t{font-size:clamp(24px,3.4vw,34px);font-weight:800;line-height:1.2;margin:8px 0 12px;letter-spacing:-.01em}
.hipo .w{font-size:17px;opacity:.95;max-width:760px}
.tres{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 22px}
.card h4{margin:0 0 6px;font-size:16px}.card p{margin:0;font-size:15px;color:var(--sub)}
.card .n{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--brand);color:#fff;font-weight:800;font-size:14px;margin-bottom:10px}
.reglas{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}
.regla{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;border-top:5px solid var(--brand)}
.regla.sal{border-top-color:var(--neg)}.regla.fil{border-top-color:var(--azul)}.regla.no{border-top-color:var(--faint)}
.regla .k{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.regla .t{font-size:22px;font-weight:800;margin:6px 0 6px;letter-spacing:-.01em}.regla p{margin:0;font-size:14.5px;color:var(--sub)}
.params{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}
.param{background:var(--panel2);border-radius:12px;padding:12px 14px}.param .v{font-weight:800;font-size:20px}.param .l{font-size:12.5px;color:var(--muted)}
figure{margin:26px 0 8px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px;overflow:hidden}
figure img{width:100%;height:auto;display:block;border-radius:8px}figcaption{font-size:13.5px;color:var(--muted);padding:10px 4px 2px}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:20px}
ul.checks{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:8px}
li.chk{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:15px}
li.chk .ic{flex:0 0 26px;height:26px;border-radius:50%;display:grid;place-items:center;font-weight:900;color:#fff;background:var(--brand)}
li.chk.ko .ic{background:var(--neg)}li.chk.na .ic{background:var(--faint)}li.chk .d{color:var(--muted);font-size:14px}
.nota{background:var(--warn-soft);border:1px solid var(--warn-line);color:var(--warn);border-radius:12px;padding:14px 16px;font-size:15px;margin:18px 0 0}
.nota b{color:inherit}.info{background:var(--azul-soft);border:1px solid #cfdff3;color:#1d3f6b;border-radius:12px;padding:14px 16px;font-size:15px;margin:18px 0 0}
.dos{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
.riesgo{border-radius:18px;padding:22px 24px;border:1px solid var(--line);background:#fff}
.riesgo.bajo{border-top:6px solid var(--azul)}.riesgo.medio{border-top:6px solid var(--brand)}
.riesgo h4{margin:0;font-size:20px}.riesgo .sub{color:var(--muted);font-size:14px;margin:2px 0 14px}
.riesgo ul{margin:0 0 14px;padding-left:18px;font-size:15px;color:var(--sub)}.riesgo .mini{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.mini .kpi .v{font-size:22px}
.tw{overflow-x:auto;margin-top:16px}table{border-collapse:collapse;width:100%;font-size:14.5px;background:#fff;border-radius:12px;overflow:hidden}
th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--panel2);font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--sub)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}tr:last-child td{border-bottom:0}
.ok{color:var(--brand);font-weight:700}.ko{color:var(--neg);font-weight:700}
.pasos{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}
.paso{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;position:relative}
.paso .n{font-size:12px;font-weight:800;color:var(--brand);letter-spacing:.1em}.paso h4{margin:4px 0 6px;font-size:15.5px}.paso p{margin:0;font-size:13.5px;color:var(--sub)}
.paso .aqui{position:absolute;top:12px;right:12px;font-size:11px;font-weight:800;background:var(--brand);color:#fff;border-radius:999px;padding:3px 8px}
.fases{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:18px}
.fase{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px;text-align:center}
.fase .n{font-size:12px;font-weight:800;color:var(--muted)}.fase .t{font-weight:800;font-size:15px;margin:2px 0 6px}
.fase .r{display:inline-block;font-size:12.5px;font-weight:800;border-radius:999px;padding:3px 10px;background:var(--brand-soft);color:var(--brand-ink)}
.fase.ko .r{background:var(--neg-soft);color:var(--neg)}
.camino{position:relative;margin:24px 0 0;padding-left:34px;border-left:3px solid var(--line)}
.hito{position:relative;margin-bottom:18px}.hito::before{content:"";position:absolute;left:-43px;top:6px;width:16px;height:16px;border-radius:50%;background:var(--brand);border:3px solid #fff;box-shadow:0 0 0 2px var(--brand)}
.hito .f{font-size:12.5px;font-weight:800;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}.hito h4{margin:2px 0 4px;font-size:17px}.hito p{margin:0;font-size:15px;color:var(--sub)}
details.code{background:#fff;border:1px solid var(--line);border-radius:14px;margin-top:14px;overflow:hidden}
details.code summary{cursor:pointer;padding:16px 18px;font-weight:800;list-style:none;display:flex;align-items:center;gap:12px}
details.code summary::-webkit-details-marker{display:none}details.code summary .tag{font-size:12px;font-weight:800;padding:3px 9px;border-radius:999px;background:var(--panel2);color:var(--sub)}
details.code summary .arrow{margin-left:auto;transition:.2s;color:var(--muted)}details[open].code summary .arrow{transform:rotate(180deg)}
details.code .body{border-top:1px solid var(--line)}details.code .meta{padding:12px 18px;font-size:14px;color:var(--sub);background:var(--panel)}
pre{margin:0;padding:18px;background:#0f1a15;color:#dbe8df;font-family:var(--mono);font-size:12.5px;line-height:1.5;overflow:auto;max-height:520px}
.copiar{float:right;font-size:12px;font-weight:700;padding:5px 10px;border-radius:8px;border:1px solid var(--line);background:#fff;cursor:pointer;color:var(--sub)}
.recursos{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:20px}
.rec{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px}.rec h4{margin:0 0 4px;font-size:16px}.rec p{margin:0 0 10px;font-size:14px;color:var(--sub)}
.btn{display:inline-block;font-weight:800;font-size:14px;padding:9px 14px;border-radius:10px;background:var(--brand);color:#fff}.btn.sec{background:var(--panel2);color:var(--brand-ink)}.btn.off{background:var(--panel2);color:var(--faint);pointer-events:none}
.glos{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}.glos div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:14.5px}.glos b{color:var(--brand-ink)}
footer{padding:36px 0 60px;color:var(--muted);font-size:13.5px}footer .wrap{display:grid;gap:8px}
.cta-final{background:linear-gradient(135deg,#0d3d24,#0e9c58);color:#fff;border-radius:20px;padding:30px 34px;display:flex;align-items:center;gap:24px;justify-content:space-between;flex-wrap:wrap}
.cta-final h3{margin:0 0 4px;font-size:24px}.cta-final p{margin:0;opacity:.9}.cta-final .btn{background:#fff;color:var(--brand-ink)}
.origen{display:grid;grid-template-columns:1.2fr 1fr;gap:20px;margin-top:20px}
.libro{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:10px}.libro b{display:block;font-size:15.5px}.libro span{font-size:14px;color:var(--muted)}
@media(max-width:860px){.hero-grid,.tres,.reglas,.params,.kpis,.dos,.pasos,.fases,.recursos,.glos,.origen,.riesgo .mini{grid-template-columns:1fr 1fr}.hero-grid{grid-template-columns:1fr}}
@media(max-width:560px){.tres,.reglas,.params,.kpis,.dos,.pasos,.fases,.recursos,.glos,.origen,.riesgo .mini,.hero-kpis{grid-template-columns:1fr}body{font-size:16px}section{padding:40px 0}.hipo{padding:26px 22px}}
@media print{nav.top{position:static}details.code{display:none}section{page-break-inside:avoid}}
"""

CSS_BADGES = """
.badge.c1{background:#e6faef;color:#0d3d24;border-color:#b9efd1}.badge.c2{background:#e8f0fa;color:#1d3f6b;border-color:#c5d8f2}
.badge.c3{background:#fff5e9;color:#9a5a15;border-color:#f0d3ab}.badge.c4{background:#f3e8fa;color:#4c2a73;border-color:#dcc6ee}
.badge.c5{background:#e6f7f7;color:#0f4c4c;border-color:#b8e3e3}.badge.c6{background:#132620;color:#fff;border-color:#132620}
"""

JS = """
document.querySelectorAll('.copiar').forEach(b=>b.addEventListener('click',()=>{const t=b.closest('.body').querySelector('pre').innerText;navigator.clipboard.writeText(t).then(()=>{b.textContent='Copiado ✓';setTimeout(()=>b.textContent='Copiar',1500)})}));
"""


def pagina(titulo, desc, nav_links, cuerpo, otra, css_extra=""):
    lg = logo()
    links = "".join(f'<a href="#{i}">{t}</a>' for i, t in nav_links) + f'<a class="cta" href="{otra[0]}">{otra[1]}</a>'
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title><meta name="description" content="{html.escape(desc)}"><style>{CSS}{css_extra}</style></head><body>
<nav class="top"><div class="wrap">{f'<img src="{lg}" alt="Trade It Simple">' if lg else ''}<span class="brand">Trade It Simple</span><div class="links">{links}</div></div></nav>
{cuerpo}
<footer><div class="wrap"><div>Material educativo de <a href="{INSTAGRAM}">Trade It Simple</a>. No es asesoría financiera. Los resultados pasados no garantizan resultados futuros. Operar con apalancamiento puede hacerte perder más de lo invertido.</div>
<div>Cifras generadas el {fecha(M['meta']['generado'])} con el motor abierto del repositorio <a href="{REPO_URL}">TIS-RSI2-Research</a> · datos diarios de QQQ: {M['meta']['fuente']} · contraste con datos de Darwinex · {M['meta']['desde'][:4]}–{M['meta']['hasta'][:4]}.</div></div></footer>
<script>{JS}</script></body></html>"""


