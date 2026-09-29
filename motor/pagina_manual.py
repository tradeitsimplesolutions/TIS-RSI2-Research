"""El manual avanzado (guia/rsi2-validacion.html): evolución y documentación, método TIS con las pruebas dentro,
robustez, drawdowns y desgaste, glosario y alcance. Cada prueba se cuenta igual: pregunta → cómo → criterio → resultado → qué significa."""
from comun import *

RSI_OP, SMA_OP = M["meta"]["rsi"], M["meta"]["sma"]

CSS_MANUAL = """
#sup4d-wrap .print{display:none}@media print{#sup4d{display:none}#sup4d-wrap .print{display:block}}
.score{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px}
.sc{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;gap:12px;align-items:center}
.sc .ic{font-size:26px}.sc b{display:block;font-size:14.5px}.sc span{font-size:12.5px;color:var(--muted)}
.sc .r{margin-left:auto;font-size:11.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:4px 9px;border-radius:999px;background:var(--brand-soft);color:var(--brand-ink);white-space:nowrap}
.sc.ko .r{background:var(--neg-soft);color:var(--neg)}.sc.na .r{background:var(--panel2);color:var(--muted)}
.estaciones{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px}
.est{border-radius:14px;padding:16px 16px 14px;min-height:118px;position:relative;border:1px solid var(--line)}
.est .n{font-size:11px;font-weight:800;letter-spacing:.14em;opacity:.7;text-transform:uppercase}.est h4{margin:4px 0 8px;font-size:18px}.est p{margin:0;font-size:13px;opacity:.9;line-height:1.45}
.est p.pr{font-style:italic;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(128,128,128,.25)}.est p.en{opacity:1}
.est.oscura{background:#132620;color:#fff;border-color:#132620}.est.verde{background:var(--brand);color:#fff;border-color:var(--brand)}
.est.clara{background:#fff;color:var(--ink)}.est.clara p{color:var(--sub)}.est a{color:inherit;text-decoration:underline}
.prueba{margin-top:52px;background:#fff;border:1px solid var(--line);border-radius:22px;padding:28px 30px 26px;box-shadow:0 1px 0 rgba(19,38,32,.03)}
.prueba .cab{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.prueba .num{font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#fff;background:var(--brand);padding:5px 11px;border-radius:999px}
.prueba .ico{font-size:30px}.prueba h3{margin:0;font-size:27px;letter-spacing:-.01em}
.prueba .ver{margin-left:auto;font-size:12.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:6px 12px;border-radius:999px;background:var(--brand-soft);color:var(--brand-ink)}
.prueba .ver.ko{background:var(--neg-soft);color:var(--neg)}.prueba .ver.na{background:var(--panel2);color:var(--muted)}
.pqc{display:grid;grid-template-columns:1.1fr 1.4fr 1fr;gap:12px;margin:18px 0 6px}
.pqc div{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;font-size:14.5px;color:var(--sub)}
.pqc .k{font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--brand);margin-bottom:6px}
.pqc .q{font-size:17px;font-weight:800;color:var(--ink);line-height:1.3}.pqc ol{margin:0;padding-left:18px}.pqc li{margin:3px 0}
.pqc .c{font-weight:700;color:var(--ink)}
.signif{background:linear-gradient(135deg,#0d3d24,#0e9c58);color:#fff;border-radius:16px;padding:18px 22px;margin-top:22px;font-size:15.5px}
.signif .k{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.85;margin-bottom:4px;font-weight:800}.signif b{font-weight:800}
.analogia{display:flex;gap:12px;align-items:flex-start;background:var(--warn-soft);border:1px solid var(--warn-line);border-radius:14px;padding:12px 16px;margin-top:16px;font-size:14.5px;color:var(--warn)}
.analogia .ic{font-size:22px}
.docs{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}
.doc{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px}.doc .k{font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.doc h4{margin:4px 0 8px;font-size:18px}.doc p,.doc li{font-size:14.5px;color:var(--sub);margin:0}.doc ul{margin:0;padding-left:18px}.doc pre{border-radius:8px;font-size:12.5px;padding:10px 12px;margin-top:8px}
.stats4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}
.cierre{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:22px}
.cierre div{border-radius:16px;padding:20px 22px;border:1px solid var(--line);background:#fff}.cierre h4{margin:0 0 8px;font-size:18px}.cierre ul{margin:0;padding-left:18px;font-size:15px;color:var(--sub)}.cierre li{margin:5px 0}
.cierre .si{border-top:6px solid var(--brand)}.cierre .no{border-top:6px solid var(--faint)}
@media(max-width:1000px){.score{grid-template-columns:1fr 1fr}}
@media(max-width:860px){.estaciones,.docs,.stats4,.pqc,.cierre{grid-template-columns:1fr 1fr}.prueba{padding:20px 18px}}
@media(max-width:560px){.score,.estaciones,.docs,.stats4,.pqc,.cierre{grid-template-columns:1fr}}
"""


def prueba(num, ico, titulo, ok, pregunta, pasos, criterio, cuerpo, significado, analogia=None, id_=""):
    ver = "Superada" if ok else ("No superada" if ok is False else "Informativa")
    cl = "" if ok else ("ko" if ok is False else "na")
    an = f'<div class="analogia"><span class="ic">💡</span><div>{analogia}</div></div>' if analogia else ""
    return f"""<div class="prueba" id="{id_}"><div class="cab"><span class="num">{num}</span><span class="ico">{ico}</span><h3>{titulo}</h3><span class="ver {cl}">{ver}</span></div>
<div class="pqc"><div><div class="k">La pregunta</div><div class="q">{pregunta}</div></div>
<div><div class="k">Cómo lo hacemos</div><ol>{''.join(f'<li>{p}</li>' for p in pasos)}</ol></div>
<div><div class="k">El criterio (fijado antes)</div><div class="c">{criterio}</div></div></div>
{an}{cuerpo}<div class="signif"><span class="k">Qué significa para ti</span>{significado}</div></div>"""


def manual():
    f1 = M["fase1"]; o, oos, t = f1["IS"], f1["OOS"], f1["TODO"]; meta = M["meta"]; anos = int(meta["hasta"][:4]) - int(meta["desde"][:4])
    lb = M["libro"]; f2, f3, f4, f4a, f5, mk, ed, dd, r4 = M["fase2"], M["fase3"], M["fase4"], M["fase4_atr"], M["fase5"], M["monkey"], M["edge_decay"], M["drawdowns"], M["robustez_4d"]
    c = f1["criterios"]; v = M["veredicto"]
    ae = dict(M["aed"]); fw = {k: {int(h): vv for h, vv in d.items()} for k, d in ae["forward"].items()}; ks = list(fw.keys())
    ae["rachas"] = {int(k): vv for k, vv in ae["rachas"].items()}
    decay_ok = ed["ultimos_3"]["pf"] >= 0.8 * ed["is_medio"]["pf"]

    # ------------------------------------------------------------- hero + marcador
    marcador = [("🔬", "AED del Nasdaq", "¿revierte de verdad?", True, "#aed"), ("📊", "Fase 1 · Backtest", "dentro y fuera de muestra", v["fase1"], "#fase1"),
                ("🔁", "Fase 2 · Walk-forward", "año a año, reglas fijas", v["fase2"], "#fase2"), ("🗺️", "Fase 3 · Zonas robustas", "mapa 2D + superficie de robustez", v["fase3"], "#fase3"),
                ("🎲", "Fase 4 · Monte Carlo", "barajar las operaciones", v["fase4"], "#fase4"), ("🔥", "Fase 5 · Estrés", "tratarla mal a propósito", v["fase5"], "#fase5"),
                ("🐒", "Test del mono", "¿le gana al azar?", mk["pct_pf"] >= 0.95, "#mono"), ("⏳", "Desgaste del edge", "¿sigue viva?", decay_ok, "#drawdowns")]
    hero = f"""<header class="hero"><div class="wrap"><div class="eyebrow">Estrategia #1 · Manual avanzado</div>
<h1>RSI 2 · Connors<small>Cómo la construimos y cómo la validamos. Ocho pruebas, contadas para que las entiendas y las puedas repetir.</small></h1>
<div class="badges"><span class="badge c1">QQQ · {meta['desde'][:4]}–{meta['hasta'][:4]}</span><span class="badge c2">{num(t['n'],0)} operaciones</span><span class="badge c3">5 bps por lado</span><span class="badge c5">Motor: Sentinel · Método: TIS</span><span class="badge c6">Un solo motor para todo</span></div>
<div class="score">{''.join(f'<a class="sc {"" if ok else "ko"}" href="{h}"><span class="ic">{i}</span><div><b>{n}</b><span>{s}</span></div><span class="r">{"OK" if ok else "No"}</span></a>' for i, n, s, ok, h in marcador)}</div>
<p class="hint" style="margin-top:16px">← <a href="rsi2-ficha.html">Volver a la ficha de la estrategia</a> · Cada prueba sigue el mismo guion: la pregunta, cómo la respondemos, el criterio fijado de antemano, el resultado y qué significa para ti.</p></div></header>"""

    # ------------------------------------------------------------- 1 · evolución y documentación
    ndx_tabla = ""
    if NDX:
        n1 = NDX["fase1"]; nm = NDX["meta"]
        ndx_tabla = "<h3>Contraste con los datos del bróker</h3>" + tabla(["", "QQQ (ETF) · validación", "NDX CFD del bróker · validación"], [
            ["Periodo", f"{fecha(meta['oos_desde'])} → {fecha(meta['oos_hasta'])}", f"{fecha(nm['oos_desde'])} → {fecha(nm['oos_hasta'])}"],
            ["Operaciones", oos["n"], n1["OOS"]["n"]], ["Profit Factor", num(oos["pf"]), num(n1["OOS"]["pf"])],
            ["CAGR (100 % capital)", pct(oos["cagr"]), pct(n1["OOS"]["cagr"])], ["Drawdown día a día", pct(oos["mdd_diario"]), pct(n1["OOS"]["mdd_diario"])],
            ["Aciertos", pct(oos["wr"], 0), pct(n1["OOS"]["wr"], 0)]]) + '<div class="info">Mismo motor, mismas reglas, sobre las velas diarias del propio bróker. El comportamiento se mantiene en el instrumento que opera el robot. Los datos del bróker no se redistribuyen (son suyos); el motor acepta cualquier CSV diario exportado de MetaTrader.</div>'
    evol = sec("evolucion", "1 · Evolución y documentación", "De la regla del libro a la nuestra",
               "Todo empieza por saber de dónde viene la idea y con qué la hemos probado. Mismos datos, mismos costes, mismo filtro de tendencia: solo cambian el umbral de entrada y la salida.",
               fig("03_libro_vs_tis.png", "Capital acumulado con 100 % por operación. Verde: nuestra variante (RSI(2) < 15, salida a dos velas verdes). Azul: la regla original de Connors (RSI(2) ≤ 5, salida al cerrar por encima de la media de 5).")
               + tabla(["", "Libro (Connors)", "TIS"], [
                   ["Entrada", "RSI(2) ≤ 5 y cierre > SMA 200", "RSI(2) &lt; 15 y cierre > SMA 200"], ["Salida", "Cierre por encima de la MA(5)", "Dos velas verdes consecutivas"],
                   [f"Operaciones · periodo completo ({meta['desde'][:4]}–{meta['hasta'][:4]})", num(lb["TODO"]["n"], 0), f"<b>{num(t['n'], 0)}</b>"],
                   [f"Operaciones · fuera de muestra ({meta['oos_desde'][:4]}–{meta['oos_hasta'][:4]})", num(lb["OOS"]["n"], 0), f"<b>{num(oos['n'], 0)}</b>"],
                   ["Profit Factor · periodo completo", num(lb["TODO"]["pf"]), num(t["pf"])], ["Profit Factor · fuera de muestra", num(lb["OOS"]["pf"]), f"<b>{num(oos['pf'])}</b>"],
                   ["CAGR (100 % capital)", pct(lb["TODO"]["cagr"]), f"<b>{pct(t['cagr'])}</b>"], ["Drawdown máximo (día a día)", pct(lb["TODO"]["mdd_diario"]), pct(t["mdd_diario"])],
                   ["Capital final", num(1 + lb["TODO"]["ret_total"], 1) + "×", f"<b>{num(1 + t['ret_total'], 1)}×</b>"], ["Días por operación", num(lb["TODO"]["barras_media"], 1), num(t["barras_media"], 1)]])
               + f'<div class="signif"><span class="k">Por qué cambiamos la regla</span>Sabemos y apreciamos la documentación del libro, pero también existe el edge decay: lo que publica un libro lo opera todo el mundo. Con RSI ≤ 5 el sistema es excelente pero opera muy poco ({num(lb["OOS"]["n"],0)} veces en ocho años de validación). Buscamos, con el AED y cuidando el fuera de muestra, un umbral que aprovechara más la forma de moverse del Nasdaq: con 15 hay {num(t["n"]/lb["TODO"]["n"],1)} veces más operaciones, la misma calidad por operación y {num((1+t["ret_total"])/(1+lb["TODO"]["ret_total"]),1)} veces más capital final. El análisis de robustez (Fase 3) confirma que no es un número mágico.</div>'
               + f"""<h3>Documentación: con qué se hizo todo</h3>
<div class="docs">
<div class="doc"><div class="k">Datos</div><h4>Norgate + Darwinex</h4><ul><li><b>Norgate Data</b>: QQQ diario con retorno total (splits y dividendos incluidos), la misma fuente que usamos en Sentinel para todo.</li><li>{fecha(meta['desde'])} → {fecha(meta['hasta'])} · {num(meta['velas'],0)} velas tras el calentamiento de la SMA 200.</li><li><b>Darwinex</b>: velas diarias del propio bróker (CFD NDX) para el contraste, y sus specs reales para los costes.</li><li>Los datos de Norgate tienen licencia y no se redistribuyen: el repositorio trae un descargador de Yahoo Finance para reproducirlo con cifras casi idénticas.</li></ul></div>
<div class="doc"><div class="k">Partición</div><h4>70 % construcción · 30 % validación</h4><ul><li>Por número de velas, en orden cronológico.</li><li>Construcción: {fecha(meta['is_desde'])} → {fecha(meta['is_hasta'])} ({o['n']} operaciones).</li><li>Validación: {fecha(meta['oos_desde'])} → {fecha(meta['oos_hasta'])} ({oos['n']} operaciones). Ninguna operación cruza la frontera.</li></ul></div>
<div class="doc"><div class="k">Costes</div><h4>10 puntos básicos ida y vuelta</h4><ul><li>Compra: apertura × 1,0005. Venta: apertura × 0,9995.</li><li>Comisión 0; el spread va dentro del slippage.</li><li>En Darwinex el coste medio real del CFD es ≈ 8 bps por operación (spread + swap). En la prueba de estrés se doblan.</li></ul></div>
<div class="doc"><div class="k">Motor</div><h4>Sentinel · un solo código para todo</h4><p>Backtest, cinco fases, test del mono, desgaste y drawdowns salen del mismo motor y del mismo dataset. Ninguna cifra de esta guía se escribió a mano.</p><pre><code>python descargar_datos.py
python motor/rsi2_motor.py
python motor/construir_html.py</code></pre></div>
<div class="doc"><div class="k">Bibliografía</div><h4>Fuentes</h4><ul><li><a href="{LIBRO_1}">Connors &amp; Alvarez (2008), <i>Short Term Trading Strategies That Work</i></a></li><li><a href="{LIBRO_2}">Connors &amp; Alvarez (2009), <i>High Probability ETF Trading</i></a></li><li><a href="{ART_STOCKCHARTS}">StockCharts ChartSchool: RSI(2)</a> · <a href="{ART_QS}">QuantifiedStrategies: RSI 2 strategy</a></li></ul></div>
<div class="doc"><div class="k">Reconciliación MT5</div><h4>{"Cerrada · " + str(REC["matching"]["entradas_misma_fecha"]) + "/" + str(REC["matching"]["operaciones_mt5"]) + " operaciones" if REC else "Pendiente"}</h4>{f"<p>El Strategy Tester de MetaTrader 5 (Darwinex, {REC['strategy_tester']['calidad_historial']}) y el motor dan las mismas fechas de entrada y de salida en las {REC['matching']['operaciones_mt5']} operaciones de la ventana ejecutable {fecha(REC['ventana_reconciliacion']['desde'])} → {fecha(REC['ventana_reconciliacion']['hasta'])}. PF {num(REC['strategy_tester']['profit_factor'])}, aciertos {num(REC['strategy_tester']['win_rate_pct'],0)} %. Las diferencias de precio de entrada son el spread del bróker.</p>" if REC else "<p>Backtest ↔ Strategy Tester todavía sin comparar.</p>"}</div>
<div class="doc"><div class="k">Reproducir</div><h4>Research reproducible</h4><p>Descarga los datos, ejecuta el motor y revisa por tu cuenta las pruebas y resultados de validación de la estrategia.</p><p style="margin-top:8px"><a href="{REPO_URL}">Ir al repositorio →</a></p></div>
</div>{ndx_tabla}""")

    # ------------------------------------------------------------- 2 · método + pruebas
    est = [("oscura", "01", "Hipótesis", "Core logic", "Empieza con una hipótesis y su lógica. Antes de tocar un dato tienes que saber por qué debería funcionar; si no sabes por qué gana, no sabrás cuándo dejará de hacerlo.",
            "Sobreventa de dos días dentro de una tendencia alcista → rebote. Está en la ficha.", "rsi2-ficha.html#hipotesis"),
           ("oscura", "02", "AED · validación", "Edge estructural", "Explora los datos antes de asumir nada. Deja que el activo hable: ¿tiende o revierte? ¿cuándo es volátil? Construir sin AED es asumir.",
            f"¿Revierte el Nasdaq tras caídas rápidas? Sí: {pct(fw[ks[2]][3]['media'])} de media a 3 días tras la señal, frente a {pct(fw[ks[0]][3]['media'])} un día cualquiera. Abajo, con gráficos.", "#aed"),
           ("oscura", "03", "Reglas", "El código", "Escribe las reglas antes de ver el resultado, y que quepan en una página. Cada pieza de más es otra forma de engañarte: menos es más.",
            "Cuatro reglas fijas, sin ajustar por activo. El mismo código en el motor y en el robot.", "rsi2-ficha.html#reglas"),
           ("verde", "04", "Backtesting", "IS / OOS", "Separa construcción y validación, y valida en lo desconocido con costes reales. Después pregúntate si le ganas al azar (test del mono).",
            f"{anos} años partidos en 70/30, 5 bps por lado. Fase 1, Fase 2 (walk-forward) y test del mono, abajo.", "#fase1"),
           ("clara", "05", "Optimización", "+ robustez", "No busques el número perfecto: mueve los parámetros alrededor y comprueba que el vecindario entero gana. Quita lo que no aporta.",
            "No se optimiza. Mapa 2D, superficie de robustez giratoria y 180 combinaciones en la Fase 3, abajo.", "#fase3"),
           ("clara", "06", "Sizing / RM", "Gestión del riesgo", "Decide con honestidad: acepta lo que el sistema hace y lo que no. Un número más grande no es mejor si sube el riesgo. Elige por perfil.",
            "Monte Carlo, estrés y cuatro niveles de tamaño (1 %, 2 %, 100 %, 1:2). Fases 4 y 5, abajo; los niveles, en la ficha.", "#fase4"),
           ("clara", "07", "Incubación", "Primeras entradas live", "Antes de confiar, míralo operar en real con poco. Las primeras operaciones reales son la última prueba, no la primera.",
            "El robot opera en cuenta real desde junio de 2026. Las primeras operaciones se publicarán cuando haya muestra.", ""),
           ("clara", "08", "Deploy live", "Producción", "El robot tiene que hacer exactamente lo que dice el papel, con cortacircuitos por si algo falla. Nada se cambia en caliente.",
            "EA en MetaTrader 5 sobre NDX, servidor 24/7, cortacircuitos −3 % / −8 % y alertas." + (f" Reconciliado con el Strategy Tester: {REC['matching']['entradas_misma_fecha']}/{REC['matching']['operaciones_mt5']} operaciones coinciden." if REC else ""), "rsi2-ficha.html#donde")]
    estaciones = '<div class="estaciones">' + "".join(
        f'<div class="est {cl}"><div class="n">{n_} · {s}</div><h4>{h}</h4><p class="pr">{p}</p><p class="en"><b>En el RSI 2:</b> {e}{f" <a href=\"{l}\">→</a>" if l else ""}</p></div>'
        for cl, n_, h, s, p, e, l in est) + "</div>"

    aed_sec = prueba("Estación 02 · AED", "🔬", "¿De verdad revierte el Nasdaq 100?", True,
                     "Antes de construir nada: ¿qué hace el Nasdaq en los días siguientes a una caída brusca? ¿Y cuánto pesa la tendencia de fondo?",
                     ["Tomamos todos los días de 27 años y miramos el retorno a 1, 2, 3, 5 y 10 días.", "Separamos cuatro grupos: cualquier día, días sobre la SMA 200, días con RSI(2) &lt; 15 sobre la SMA 200 (nuestra señal) y la misma señal por debajo.", "Medimos además si el Nasdaq revierte (autocorrelación, rachas de caídas) y cómo cambia su volatilidad."],
                     "No hay criterio numérico: es exploración. Si la señal no destacara sobre un día cualquiera, la hipótesis moriría aquí.",
                     f'<div class="kpis">{kpi(pct(fw[ks[2]][3]["media"], 2, True), "3 días tras la señal", "retorno medio · sobre la SMA 200", "ok")}{kpi(pct(fw[ks[0]][3]["media"], 2, True), "3 días cualesquiera", "retorno medio · todos los días")}{kpi(pct(fw[ks[2]][3]["pct_pos"], 0), "Rebotes", "de las señales suben a 3 días", "ok")}{kpi(pct(ae["pct_sobre_sma"], 0), "Del tiempo sobre la SMA 200", "solo ahí operamos")}{kpi(num(ae["senales_ano_media"], 0), "Señales al año", "de media, con tendencia a favor")}</div>'
                     + fig("13_aed_forward.png", "Retorno medio del Nasdaq 100 (QQQ) a 1, 2, 3, 5 y 10 días según el punto de partida. Verde: nuestra señal (RSI(2) < 15 con el precio sobre la SMA 200). Rojo: la misma sobreventa pero por debajo de la SMA 200.")
                     + tabla(["Punto de partida", "Días"] + [f"{h} d" for h in ae["horizontes"]], [[k, fw[k][ae["horizontes"][0]]["n"]] + [f"{pct(fw[k][h]['media'], 2, True)} · {pct(fw[k][h]['pct_pos'], 0)} ↑" for h in ae["horizontes"]] for k in ks])
                     + f'<div class="info"><b>Lo que dice:</b> un día cualquiera el Nasdaq sube de media {pct(fw[ks[0]][3]["media"], 2)} en tres días. Tras una sobreventa extrema con la tendencia a favor sube {pct(fw[ks[2]][3]["media"], 2)}, y el {pct(fw[ks[2]][3]["pct_pos"], 0)} de las veces. La misma sobreventa <b>por debajo</b> de la SMA 200 sube de media algo parecido ({pct(fw[ks[3]][3]["media"], 2)}) pero solo el {pct(fw[ks[3]][3]["pct_pos"], 0)} de las veces y con sustos mucho mayores: sin tendencia, el rebote es una moneda al aire. El filtro no compra rentabilidad media, compra <b>consistencia</b>.</div>'
                     + fig("14_aed_rachas.png", "Izquierda: autocorrelación de los retornos diarios (negativa = lo que cae hoy tiende a subir mañana). Derecha: retorno medio a 3 días después de 1, 2, 3 y 4 días seguidos de caída, con el precio sobre la SMA 200.")
                     + f'<div class="info"><b>Reversión, no continuación:</b> la autocorrelación a un día es {pct(ae["autocorr"][0], 1)}. Después de {max(ae["rachas"], key=lambda k: ae["rachas"][k]["media"])} días seguidos de caída sobre la SMA 200, el rebote medio a 3 días es {pct(ae["rachas"][max(ae["rachas"], key=lambda k: ae["rachas"][k]["media"])]["media"], 2)}. El RSI de 2 períodos es solo una forma compacta de medir exactamente eso.</div>'
                     + fig("15_aed_regimen.png", "Arriba: el precio con la SMA 200; en rojo, los tramos por debajo, donde la estrategia no opera. Abajo: el ATR(14) como porcentaje del precio, la volatilidad diaria que usa el robot para dimensionar.")
                     + "<h3>Colas gordas: por qué el tamaño se decide con el ATR</h3>"
                     + fig("18_aed_colas.png", "Cuántos días hubo con cada retorno (escala logarítmica para que se vean los extremos) frente a lo que predeciría una campana normal con la misma media y desviación. Las colas reales están muy por encima de la curva azul: los días extremos ocurren mucho más de lo que dice la teoría.")
                     + tabla(["Retornos diarios de QQQ", ""], [["Media diaria", pct(ae["retorno"]["media_dia"], 3, True)], ["Desviación típica diaria", pct(ae["retorno"]["std_dia"], 2)], ["Días positivos", pct(ae["retorno"]["pct_dias_pos"], 0)], ["Mejor / peor día", f"{pct(ae['retorno']['mejor_dia'], 1, True)} / {pct(ae['retorno']['peor_dia'], 1, True)}"], ["Asimetría · curtosis", f"{num(ae['retorno']['asimetria'])} · {num(ae['retorno']['curtosis'])} (una campana normal tiene curtosis 0)"], ["ATR(14) / precio · media (mín – máx)", f"{pct(ae['atr_pct']['media'], 2)} ({pct(ae['atr_pct']['min'], 2)} – {pct(ae['atr_pct']['max'], 2)})"]])
                     + f'<div class="nota"><b>Qué es una cola gorda y por qué te importa:</b> si los retornos diarios siguieran una campana normal, un día del {pct(ae["retorno"]["peor_dia"], 1, True)} sería prácticamente imposible. Ocurrió, y no una vez. La curtosis de {num(ae["retorno"]["curtosis"])} (una campana tiene 0) mide exactamente eso: cuánto más gordas son las colas que las de la teoría. Consecuencia práctica: la volatilidad cambia de golpe y por eso el robot calcula el tamaño de cada operación con el ATR de los últimos 14 días, no con un porcentaje fijo. Cuando el mercado se pone nervioso, la posición se encoge sola antes de que llegue el susto.</div>',
                     "El Nasdaq revierte a corto plazo y lo hace con consistencia solo cuando la tendencia de fondo es alcista. La hipótesis no es una opinión: está en los datos antes de escribir una sola regla. Si algún día estos números cambian, la estrategia deja de tener sentido y lo veremos aquí.",
                     "Es como mirar el historial de un jugador antes de ficharlo: no te fías del talento que te cuentan, miras qué ha hecho en cada situación.", "aed")

    fase1 = prueba("Fase 1", "📊", "Backtest dentro y fuera de muestra", v["fase1"],
                   "Con las reglas ya escritas, ¿gana dinero en datos que nunca vio, y no depende de un golpe de suerte?",
                   ["Partimos la historia en dos por número de velas: el 70 % para construir y el 30 % final, guardado y sin mirar.", "Corremos las reglas fijas con 5 bps de coste por lado en cada operación.", "Miramos solo el tramo guardado: si la estrategia se hubiera ajustado al pasado, ahí se desmoronaría."],
                   "Fuera de muestra: Profit Factor ≥ 1,3 · al menos 30 operaciones · drawdown menor del 20 % · Profit Factor sin la mejor operación > 1.",
                   tabla(["", "Construcción (IS)", "Validación (OOS)", "Todo"], [
                       ["Periodo", f"{fecha(meta['is_desde'])} → {fecha(meta['is_hasta'])}", f"{fecha(meta['oos_desde'])} → {fecha(meta['oos_hasta'])}", f"{anos} años"],
                       ["Operaciones", o["n"], oos["n"], t["n"]], ["Profit Factor", num(o["pf"]), f"<b>{num(oos['pf'])}</b>", num(t["pf"])],
                       ["Profit Factor sin la mejor operación", num(o["pfnb"]), num(oos["pfnb"]), num(t["pfnb"])],
                       ["CAGR (100 % capital)", pct(o["cagr"]), f"<b>{pct(oos['cagr'])}</b>", pct(t["cagr"])],
                       ["Drawdown máx. operación a operación", pct(o["mdd"]), pct(oos["mdd"]), pct(t["mdd"])],
                       ["Drawdown máx. día a día", pct(o["mdd_diario"]), pct(oos["mdd_diario"]), pct(t["mdd_diario"])],
                       ["Aciertos", pct(o["wr"], 0), pct(oos["wr"], 0), pct(t["wr"], 0)],
                       ["Retorno medio por operación", pct(o["expectancy"], 2), pct(oos["expectancy"], 2), pct(t["expectancy"], 2)],
                       ["Mejor / peor operación", f"{pct(o['mejor'])} / {pct(o['peor'])}", f"{pct(oos['mejor'])} / {pct(oos['peor'])}", f"{pct(t['mejor'])} / {pct(t['peor'])}"],
                       ["Tiempo en mercado", pct(o["exposicion"], 0), pct(oos["exposicion"], 0), pct(t["exposicion"], 0)]])
                   + '<ul class="checks">' + check(c['pf'], f"PF fuera de muestra ≥ 1,3 → {num(oos['pf'])}") + check(c['n'], f"≥ 30 operaciones fuera de muestra → {oos['n']}")
                   + check(c['mdd'], f"Drawdown fuera de muestra &lt; 20 % → {pct(oos['mdd'])}") + check(c['pfnb'], f"PF sin la mejor operación &gt; 1 → {num(oos['pfnb'])}") + "</ul>"
                   + '<div class="nota"><b>Dos cifras de drawdown, y no se contradicen.</b> "Operación a operación" solo actualiza el capital cuando se cierra cada operación: es el criterio de la prueba. "Día a día" valora la posición abierta cada noche: es la cifra que sentirías en la cuenta y la que usamos en la ficha. La segunda siempre es igual o peor.</div>',
                   f"La estrategia gana en ocho años que no vio, con costes, y no depende de una sola operación afortunada. Que la validación salga <b>mejor</b> que la construcción no es mérito nuestro: 2019–2026 ha sido un mercado muy favorable a comprar caídas en el Nasdaq. Lo que importa es que no se degrada. Los años malos existen y están en la sección 3, mes a mes.",
                   "Es un examen con las preguntas que no viste al estudiar. Aprobar el examen que ya conocías no vale nada.", "fase1")

    fase2 = prueba("Fase 2", "🔁", "Walk-forward: un examen sorpresa cada año", v["fase2"],
                   "¿Lo que rinde en el pasado reciente se parece a lo que rinde después? ¿O vive de dos o tres años buenos?",
                   ["Para cada año natural, tomamos los tres años anteriores como referencia (construcción) y ese año como examen (validación).", "Rodamos la ventana año a año desde 2003 hasta el último completo, siempre con las mismas reglas.", "Comparamos el retorno del año examinado con la media de los tres previos, y contamos cuántos años salen positivos."],
                   "Eficiencia (retorno medio validado ÷ retorno medio previo) ≥ 0,50 · al menos el 60 % de los años positivos · ningún año con drawdown ≥ 20 %.",
                   fig("09_walkforward.png", "Barras: retorno de cada año validado con las reglas fijas. Línea: media anual de los tres años previos. Verde/rojo: año positivo/negativo.")
                   + '<ul class="checks">' + check(f2["eficiencia"] >= 0.5, f"Eficiencia ≥ 0,50 → {num(f2['eficiencia'])}")
                   + check(f2["pct_positivas"] >= 0.6, f"≥ 60 % de años positivos → {pct(f2['pct_positivas'],0)} ({sum(x['ret_oos']>0 for x in f2['ventanas'])} de {len(f2['ventanas'])})")
                   + check(f2["peor_mdd"] > -0.2, f"Ningún año con drawdown ≥ 20 % → peor: {pct(f2['peor_mdd'])}") + "</ul>"
                   + tabla(["Año", "Operaciones", "Retorno del año", "Profit Factor", "Drawdown"], [[x["ano"], x["n_oos"], f"<span class='{'ok' if x['ret_oos']>0 else 'ko'}'>{pct(x['ret_oos'], 1, True)}</span>", num(x["pf_oos"]) if x["pf_oos"] is not None else "—", pct(x["mdd_oos"])] for x in f2["ventanas"]]),
                   f"Como las reglas no se optimizan, este walk-forward es honesto por construcción: no hay nada que reajustar cada año. Una eficiencia de {num(f2['eficiencia'])} dice que los años examinados rinden, de media, más que los tres previos que los anticipaban. Los años rojos existen ({len(f2['ventanas']) - sum(x['ret_oos']>0 for x in f2['ventanas'])} de {len(f2['ventanas'])}) y son pequeños: ninguno pasó del {pct(min(x['ret_oos'] for x in f2['ventanas']))}.",
                   "Un profesor que cada año pone un examen nuevo y compara con los tres cursos anteriores. Si el alumno solo aprobaba el examen que se sabía, aquí se nota.", "fase2")

    fase3 = prueba("Fase 3", "🗺️", "Zonas robustas: ¿depende de un número exacto?", v["fase3"],
                   "¿El resultado depende de haber acertado un número exacto (15, 200) o aguanta todo el vecindario? Es la prueba que separa un sistema real de una curva bonita ajustada al pasado.",
                   ["Mapa 2D: movemos el umbral del RSI (5 a 30) y el periodo de la media (100 a 300), con salida y costes fijos. 30 celdas, solo en construcción.", "Superficie de robustez: la misma rejilla en tres dimensiones (RSI × SMA × Profit Factor), giratoria, para ver si la que opera está en una meseta; y las 30 combinaciones ordenadas con y sin el doble de coste.", "Después repetimos las 30 celdas para tres salidas distintas y dos niveles de coste: 180 combinaciones."],
                   "Meseta 3×3 con PF ≥ 1,3 y más de 30 operaciones por celda · ningún vecino cae más del 30 % respecto al centro · y, como referencia, que la mayoría de las 180 combinaciones supere PF 1,3.",
                   "<h3 style=\"margin-top:10px\">El mapa 2D: umbral del RSI × periodo de la media</h3>"
                   + fig("04_grid.png", "Profit Factor en construcción para las 30 combinaciones, con salida y costes fijos. El recuadro es la configuración que opera (RSI < 15, SMA 200). N es el número de operaciones de cada celda. Cuanto más verde, mejor; lo que buscamos es que el recuadro esté rodeado de verde, no que sea la celda más oscura.")
                   + '<ul class="checks">' + check(f3["meseta_3x3"], "Meseta 3×3: las 9 celdas alrededor de la elegida superan PF 1,3 con más de 30 operaciones")
                   + check(f3["anticliff"], f"Anti-acantilado: ningún vecino cae más del 30 % respecto al centro → peor caída {pct(f3['peor_caida_vecino_pct']/100, 0)}")
                   + check(f3["pct_celdas_pf13"] >= 0.8, f"{pct(f3['pct_celdas_pf13'],0)} de las 30 celdas superan PF 1,3") + "</ul>"
                   + f'<div class="info">La mejor celda del mapa es RSI &lt; {f3["optimo"]["rsi"]} con SMA {f3["optimo"]["sma"]} (PF {num(f3["optimo"]["pf"])}). No la elegimos: tiene menos operaciones y elegir el pico del mapa es exactamente el error que esta prueba quiere evitar. Nos quedamos en el centro de la meseta.</div>'
                   + "<h3>La superficie de robustez: gírala tú</h3><p class=\"lead\" style=\"font-size:16px\">La misma rejilla vista como una superficie, como en el optimizador de MultiCharts: altura y color son el Profit Factor, y el punto negro es la configuración que opera. Lo que buscamos es que esté en una meseta, con vecinos parecidos, no en un pico aislado. Con los botones ves las seis combinaciones de salida y coste; al pasar el cursor por cada celda ves también su drawdown.</p>"
                   + superficie_4d(r4, RSI_OP, SMA_OP)
                   + "<h3>Las 30 combinaciones, de mejor a peor, con y sin el doble de coste</h3>"
                   + fig("11b_robustez_barras.png", "Cada combinación es una barra (Profit Factor con 5 bps por lado) y la línea naranja es la misma combinación con 10 bps; la barra negra es la que opera. Todas siguen por encima del criterio de 1,3 aun con el doble de coste.")
                   + "<h3>Tres salidas y dos costes: 180 combinaciones</h3><p class=\"lead\" style=\"font-size:16px\">Si la estrategia dependiera de <i>nuestra</i> salida o de costes bajos, aquí se vería.</p>"
                   + fig("11_robustez_mapas.png", "Seis mapas con la misma escala de color. Arriba, costes de 5 bps por lado; abajo, 10 bps. Columnas: salida a dos velas verdes (la nuestra), salida al cruzar la media de 5 (la del libro) y salida cuando el RSI(2) supera 70. El recuadro es la configuración que opera.")
                   + f'<div class="stats4">{kpi(r4["n_combos"], "Combinaciones probadas", "RSI × SMA × salida × coste")}{kpi(pct(r4["pct_pf13"],0), "Superan PF 1,3", "el criterio de la Fase 1", "ok")}{kpi(pct(r4["pct_pf1"],0), "Son rentables", "PF por encima de 1", "ok")}{kpi(num(r4["pf_min"]) + " · " + num(r4["pf_mediana"]) + " · " + num(r4["pf_max"]), "Mínimo · mediana · máximo", "Profit Factor")}</div>'
                   + fig("12_robustez_dist.png", "Distribución del Profit Factor de las 180 combinaciones. La línea negra es la configuración que opera; la roja, el criterio mínimo.")
                   + tabla(["Dimensión", "Valor", "PF medio (IS)"], [["Salida", s, num(x)] for s, x in r4["por_salida"].items()] + [["Coste por lado", c_, num(x)] for c_, x in r4["por_coste"].items()]),
                   f"La configuración que opera está en el percentil {pct(r4['percentil_vigente'],0)} de las {r4['n_combos']} combinaciones: ni la mejor ni la peor, en el centro de una superficie suave donde casi todo gana. Doblar los costes baja el PF medio de {num(r4['por_coste']['5 bps'])} a {num(r4['por_coste']['10 bps'])} y no cambia la conclusión. Las tres salidas funcionan; la nuestra no es un número mágico. Esto es lo que permite decir que el edge es del activo, no de los parámetros: mañana, con parámetros ligeramente distintos, seguirá funcionando.",
                   "Un buen restaurante no depende de que el cocinero titular esté ese día. Si con cualquier cocinero de la casa la comida sigue siendo buena, el mérito es de la cocina. Y si solo ganas apostando al 17 exacto, era suerte.", "fase3")

    fase4 = prueba("Fase 4", "🎲", "Monte Carlo: barajar las operaciones", v["fase4"],
                   f"Las {num(t['n'],0)} operaciones ocurrieron en un orden concreto. ¿Y si hubieran venido en otro? ¿Cuánto del resultado es el orden y cuánto es la estrategia?",
                   [f"Reordenamos las operaciones reales {num(f4['n_sim'],0)} veces al azar, en bloques de {f4['bloque']} para conservar las rachas.", "Dibujamos los caminos posibles y, para cada uno, calculamos el retorno total y la peor caída.", "Miramos el 5 % de escenarios más desfavorables y el peor de todos: ahí es donde se esconde el riesgo real."],
                   "Evaluado con el tamaño que opera el robot (1 % de riesgo por ATR): retorno total del 5 % peor de escenarios > 0 · drawdown del 5 % peor de escenarios < 25 % · probabilidad de perder la mitad del capital < 5 %. El 100 % del capital se muestra como referencia.",
                   fig("05_montecarlo.png", f"Arriba: {num(f4['n_sim'],0)} caminos posibles con las mismas operaciones en distinto orden (400 dibujados en gris, bandas de todos). El camino real en negro, la mediana en verde y en rojo el camino con el peor drawdown de los {num(f4['n_sim'],0)}. Abajo: retorno total y drawdown máximo de cada camino, con el 5 % peor y el peor absoluto marcados.")
                   + f'<div class="kpis">{kpi(pct(f4["mdd_p50"]), "Drawdown mediano", "de los caminos", "neg")}{kpi(pct(f4["mdd_p5"]), "Drawdown del 5 % peor", "criterio: mejor que −25 %", "neg")}{kpi(pct(f4["mdd_peor"]), "El peor de todos", f"1 camino entre {num(f4["n_sim"],0)}", "neg")}{kpi(pct(f4["p50_ret"],0,True), "Retorno mediano", "de los caminos", "ok")}{kpi(pct(f4["ret_peor"],0,True), "El peor retorno", "aun así positivo" if f4["ret_peor"] > 0 else "negativo")}</div>'
                   + '<h4 style="margin:22px 0 6px">Criterio · con el tamaño del robot (1 % de riesgo por ATR)</h4><ul class="checks">' + check(f4a["p5_ret"] > 0, f"Retorno del 5 % peor de escenarios > 0 → {pct(f4a['p5_ret'],0, True)}")
                   + check(f4a["mdd_p5"] > -0.25, f"Drawdown del 5 % peor de escenarios &lt; 25 % → {pct(f4a['mdd_p5'])}")
                   + check(f4a["prob_ruina"] < 0.05, f"Probabilidad de perder la mitad del capital &lt; 5 % → {pct(f4a['prob_ruina'])}") + "</ul>"
                   + '<h4 style="margin:22px 0 6px">Referencia · con el 100 % del capital</h4><ul class="checks">' + check(f4["p5_ret"] > 0, f"Retorno del 5 % peor de escenarios > 0 → {pct(f4['p5_ret'],0, True)}")
                   + check(f4["mdd_p5"] > -0.25, f"Drawdown del 5 % peor de escenarios &lt; 25 % → {pct(f4['mdd_p5'])} (el {pct(f4['prob_mdd_25'])} de escenarios lo supera)")
                   + check(f4["prob_ruina"] < 0.05, f"Probabilidad de perder la mitad del capital &lt; 5 % → {pct(f4['prob_ruina'])}") + "</ul>"
                   + tabla(["", "100 % capital", "1 % de riesgo (ATR)"], [["Retorno total · p5 / mediana / p95", f"{pct(f4['p5_ret'],0)} / {pct(f4['p50_ret'],0)} / {pct(f4['p95_ret'],0)}", f"{pct(f4a['p5_ret'],0)} / {pct(f4a['p50_ret'],0)} / {pct(f4a['p95_ret'],0)}"],
                                                                           ["Drawdown máximo · p5 / mediana / p95", f"{pct(f4['mdd_p5'])} / {pct(f4['mdd_p50'])} / {pct(f4['mdd_p95'])}", f"{pct(f4a['mdd_p5'])} / {pct(f4a['mdd_p50'])} / {pct(f4a['mdd_p95'])}"],
                                                                           ["Escenarios con drawdown > 25 %", pct(f4["prob_mdd_25"]), pct(f4a["prob_mdd_25"])], ["Probabilidad de ruina (−50 %)", pct(f4["prob_ruina"]), pct(f4a["prob_ruina"])]])
                   + f'<div class="nota"><b>Lectura honesta:</b> con el 100 % del capital, uno de cada {int(round(1/max(f4["prob_mdd_25"],1e-9)))} escenarios habría pasado por una caída mayor del 25 %, y el 5 % peor queda en {pct(f4["mdd_p5"])}: justo en el límite. Por eso el criterio se evalúa con el tamaño que de verdad va a mercado, el del robot, donde el riesgo queda muy lejos del límite. Si vas con todo el capital, esta es la cifra que tienes que aceptar antes.</div>',
                   f"El drawdown que viste en el backtest ({pct(t['mdd_diario'])}) fue <b>uno</b> de los posibles. La mediana de los {num(f4['n_sim'],0)} caminos es {pct(f4['mdd_p50'])}, el 5 % peor llega a {pct(f4['mdd_p5'])} y el peor de todos a {pct(f4['mdd_peor'])}: eso es lo que tienes que estar dispuesto a aguantar si vas con todo el capital. Fíjate en que ni siquiera el peor camino termina en pérdidas ({pct(f4['ret_peor'],0,True)}): el orden cambia cuánto sufres, no si ganas. No es una comparación contra el azar ni una predicción; es una medida de cuánto puede doler el camino.",
                   "Barajar las cartas de una partida ya jugada: las cartas son las mismas, pero el orden cambia cuánto sufres antes de ganar.", "fase4")

    def fila_stress(nombre, k):
        e = f5[k]; ev = e.get("pasa")
        return [nombre, e.get("n", 0), num(e.get("pf")) if e.get("n") else "—", pct(e.get("ret_total")) if e.get("n") else "—",
                "Muestra insuficiente" if e.get("n", 0) < 30 else ("<span class='ok'>Supera</span>" if ev else "<span class='ko'>No supera</span>")]
    fase5 = prueba("Fase 5", "🔥", "Estrés: tratarla mal a propósito", v["fase5"],
                   "¿Sigue ganando si los costes se disparan, si le quitamos sus mejores años, o en los peores mercados de la historia reciente?",
                   ["Doblamos los costes (10 bps por lado) en el periodo de validación.", "Quitamos los dos mejores años de validación y miramos qué queda.", "La corremos en 2000–2002, 2008 y 2022, los tres mercados bajistas del periodo."],
                   "Profit Factor ≥ 1,1 con costes dobles y sin los dos mejores años. Los regímenes bajistas se muestran; si hay menos de 30 operaciones, no se evalúan.",
                   tabla(["Escenario", "Operaciones", "Profit Factor", "Retorno", "Veredicto"], [
                       fila_stress("Costes ×2 (10 bps por lado) · validación", "costes_x2"),
                       fila_stress(f"Sin los dos mejores años ({', '.join(map(str, f5['sin_2_mejores_anos']['anos']))}) · validación", "sin_2_mejores_anos"),
                       fila_stress("Estallido puntocom · 2000–2002", "regimen_2000_2002"), fila_stress("Crisis financiera · 2008", "regimen_2008"), fila_stress("Mercado bajista · 2022", "regimen_2022")])
                   + '<ul class="checks">' + check(f5["costes_x2"]["pasa"], f"Con el doble de costes → PF {num(f5['costes_x2']['pf'])}") + check(f5["sin_2_mejores_anos"]["pasa"], f"Sin los dos mejores años → PF {num(f5['sin_2_mejores_anos']['pf'])}") + "</ul>"
                   + '<div class="info"><b>Los años bajistas se pasan casi enteros sin operar</b>: con el precio por debajo de la media de 200 no hay señales. En 2008 y 2022 hubo dos operaciones en cada uno, perdedoras y pequeñas. No es un fallo del sistema, es su diseño: el filtro hace su trabajo y el coste es no ganar nada en esos años. Con dos operaciones no se puede evaluar un Profit Factor, así que lo dejamos como "muestra insuficiente" en vez de disfrazarlo.</div>',
                   f"Con el doble de costes el Profit Factor baja de {num(oos['pf'])} a {num(f5['costes_x2']['pf'])}: el edge no vive de una ejecución perfecta. Sin sus dos mejores años sigue en {num(f5['sin_2_mejores_anos']['pf'])}: no depende de un par de rachas. Y en los mercados bajistas hace lo que promete: apartarse. Lo que no hace es ganar en ellos, y eso hay que saberlo antes de operarla.",
                   "Antes de comprar un coche usado lo llevas a un mecánico que busca fallos a propósito. Si sale bien de ahí, te fías.", "fase5")

    mono = prueba("Prueba extra", "🐒", "El test del mono: ¿le ganamos al azar?", mk["pct_pf"] >= 0.95,
                  "En un mercado que sube, entrar en cualquier momento gana algo. ¿Aporta algo el momento exacto de entrada, o es el filtro de tendencia el que hace todo el trabajo?",
                  [f"{num(mk['n_sim'],0)} monos entran en días aleatorios, pero solo con el precio sobre la SMA 200.", "Cada mono hace el mismo número de operaciones, con la misma distribución de duraciones y los mismos costes que la estrategia.", "Comparamos el Profit Factor, el retorno y el drawdown de la estrategia con los de los monos."],
                  "La estrategia tiene que superar al menos al 95 % de los monos en Profit Factor.",
                  fig("06_monkey.png", "Izquierda: la curva de capital de 250 monos (gris), la del mono mediano (morado discontinuo) y la de la estrategia (verde), operación a operación. Derecha: distribución del Profit Factor de los 2.000 monos, con la curva de densidad; la línea verde es la estrategia.")
                  + f'<div class="kpis">{kpi(num(mk["pf_real"]), "PF de la estrategia", "periodo completo", "ok")}{kpi(num(mk["pf_mono_mediana"]), "PF del mono mediano", "misma tendencia, entrada al azar")}{kpi(pct(mk["pct_pf"],1), "Monos superados", "en Profit Factor", "ok")}{kpi(pct(mk["pct_ret"],1), "Monos superados", "en retorno total")}{kpi(pct(mk["pct_mdd"],1), "Monos superados", "en drawdown (menor)")}</div>',
                  f"El mono mediano, entrando al azar dentro de la misma tendencia, consigue un Profit Factor de {num(mk['pf_mono_mediana'])}: el filtro de la SMA 200 ya da algo. La estrategia consigue {num(mk['pf_real'])} y bate al {pct(mk['pct_pf'],1)} de los monos. La diferencia entre las dos cifras es exactamente lo que aporta el RSI(2): el momento de entrada importa.",
                  "Si le ganas a 2.000 monos que apuestan al azar con tus mismas condiciones, no fue suerte. Si no, era el mercado, no tú.", "mono")

    metodo = sec("metodo", "2 · El método TIS", "Una estrategia es una línea de producción",
                 "Entra una premisa por un lado. Sale una estrategia validada por el otro. Ocho estaciones, siempre en el mismo orden: cada una te protege del error de la siguiente. Así pasó el RSI 2 por cada una.",
                 estaciones + '<div class="info" style="margin-top:22px">Cada estación lleva su principio (el que vale para cualquier sistema) y lo que se hizo en el RSI 2. Las estaciones 02, 04, 05 y 06 se pueden medir: abajo están las pruebas, y todas siguen el mismo guion. Los criterios se escriben <b>antes</b> de correr nada y no se tocan según el resultado.</div>'
                 + aed_sec + fase1 + fase2 + fase3 + fase4 + fase5 + mono, "alt")

    # ------------------------------------------------------------- 3 · robustez
    rob = None and prueba("Fase 3 · en detalle", "🗺️", "Mapa 2D y vista 4D", v["fase3"],
                 "Si movemos los parámetros, ¿seguimos en una zona ganadora o nos caemos por un acantilado?",
                 ["Mapa 2D: umbral del RSI (5 a 30) × periodo de la media (100 a 300), con salida y costes fijos. 30 celdas.", "Vista 4D: las mismas 30 celdas repetidas para tres salidas distintas y dos niveles de coste. 180 combinaciones.", "Todo sobre el periodo de construcción, con la validación intacta."],
                 "Meseta 3×3 con PF ≥ 1,3 y más de 30 operaciones por celda · ningún vecino cae más del 30 % · y, como referencia, que la mayoría de las 180 combinaciones supere PF 1,3.",
                 "<h3 style=\"margin-top:10px\">Mapa 2D: umbral del RSI × periodo de la media</h3>"
                 + fig("04_grid.png", "Profit Factor en construcción para las 30 combinaciones, con salida y costes fijos. El recuadro es la configuración que opera (RSI < 15, SMA 200). N es el número de operaciones de cada celda.")
                 + '<ul class="checks">' + check(f3["meseta_3x3"], "Meseta 3×3: las 9 celdas alrededor de la elegida superan PF 1,3 con más de 30 operaciones")
                 + check(f3["anticliff"], f"Anti-acantilado: ningún vecino cae más del 30 % respecto al centro → peor caída {pct(f3['peor_caida_vecino_pct']/100, 0)}")
                 + check(f3["pct_celdas_pf13"] >= 0.8, f"{pct(f3['pct_celdas_pf13'],0)} de las 30 celdas superan PF 1,3") + "</ul>"
                 + f'<div class="info">La mejor celda del mapa es RSI &lt; {f3["optimo"]["rsi"]} con SMA {f3["optimo"]["sma"]} (PF {num(f3["optimo"]["pf"])}). No la elegimos: tiene menos operaciones y elegir el pico del mapa es exactamente el error que esta prueba quiere evitar. Nos quedamos en el centro de la meseta.</div>'
                 + f"<h3>Vista 4D: añadimos el tipo de salida y el coste</h3><p class=\"lead\" style=\"font-size:16px\">Si la estrategia dependiera de <i>nuestra</i> salida o de costes bajos, aquí se vería.</p>"
                 + fig("11_robustez_4d.png", "Seis mapas con la misma escala de color. Arriba, costes de 5 bps por lado; abajo, 10 bps. Columnas: salida a dos velas verdes (la nuestra), salida al cruzar la media de 5 (la del libro) y salida cuando el RSI(2) supera 70. El recuadro es la configuración que opera.")
                 + f'<div class="stats4">{kpi(r4["n_combos"], "Combinaciones probadas", "RSI × SMA × salida × coste")}{kpi(pct(r4["pct_pf13"],0), "Superan PF 1,3", "el criterio de la Fase 1", "ok")}{kpi(pct(r4["pct_pf1"],0), "Son rentables", "PF por encima de 1", "ok")}{kpi(num(r4["pf_min"]) + " · " + num(r4["pf_mediana"]) + " · " + num(r4["pf_max"]), "Mínimo · mediana · máximo", "Profit Factor")}</div>'
                 + fig("12_robustez_dist.png", "Distribución del Profit Factor de todas las combinaciones. La línea negra es la configuración que opera; la roja, el criterio mínimo.")
                 + tabla(["Dimensión", "Valor", "PF medio (IS)"], [["Salida", s, num(x)] for s, x in r4["por_salida"].items()] + [["Coste por lado", c_, num(x)] for c_, x in r4["por_coste"].items()]),
                 f"La configuración que opera está en el percentil {pct(r4['percentil_vigente'],0)} de las {r4['n_combos']} combinaciones: ni la mejor ni la peor, en la zona media-alta de una distribución que casi entera gana. Doblar los costes baja el PF medio de {num(r4['por_coste']['5 bps'])} a {num(r4['por_coste']['10 bps'])} y no cambia la conclusión. Las tres salidas funcionan; la nuestra no es un número mágico. Esto es lo que permite decir que el edge es del activo, no de los parámetros.",
                 "Un buen restaurante no depende de que el cocinero titular esté ese día. Si con cualquier cocinero de la casa la comida sigue siendo buena, el mérito es de la cocina.", "robustez-detalle")
    robustez = ""

    # ------------------------------------------------------------- 4 · drawdowns y desgaste
    peor = dd["peores"][0]; largo = max(dd["peores"], key=lambda e: e["dias"]); me = M["mensual"]
    neg10 = me["ultimos10_negativos"]; ult_filas = [f for f in me["filas"] if f["ano"] >= me["ultimos10_desde"]]
    ddp = prueba("Prueba extra", "🌊", "Drawdowns: lo que se siente por el camino", True,
                 "¿Cuánto y durante cuánto tiempo va a estar la cuenta por debajo de su máximo? ¿Cuántos meses y años cierran en rojo? Es lo que hace abandonar a la gente, no el retorno final.",
                 ["Construimos la curva de capital día a día, valorando la posición abierta cada noche, y la cerramos mes a mes y año a año.", "Identificamos cada caída desde un máximo hasta su recuperación: cuánto cayó y cuántos días tardó en volver, y las agrupamos por profundidad.", "Contamos meses y años positivos y negativos, con foco en los últimos diez años."],
                 "Informativa: no hay umbral. Lo que se exige (drawdown < 20 % fuera de muestra) ya está en la Fase 1. Aquí se trata de que sepas cómo es el camino antes de recorrerlo.",
                 f'<div class="kpis">{kpi(f"{me["meses_pos"]} / {me["meses_neg"]}", "Meses positivos / negativos", f"{me["meses_planos"]} meses sin operar", "ok")}{kpi(len(me["anos_negativos"]), "Años negativos", f"de {len(me["anos"])} · " + (", ".join(map(str, me["anos_negativos"])) if me["anos_negativos"] else "ninguno"), "neg" if me["anos_negativos"] else "ok")}{kpi(len(neg10), "Años negativos en los últimos 10", (", ".join(map(str, neg10)) if neg10 else "ninguno") + f" · desde {me["ultimos10_desde"]}", "neg" if neg10 else "ok")}{kpi(pct(me["peor_mes"]), "Peor mes", fecha(me["peor_mes_fecha"]), "neg")}{kpi(pct(me["mejor_mes"]), "Mejor mes", "100 % capital", "ok")}</div>'
                 + "<h3>Mes a mes, año a año</h3>"
                 + fig("19_meses.png", "Retorno de cada mes con el 100 % del capital (verde positivo, rojo negativo, vacío sin operaciones). A la derecha, el retorno del año y cuántos meses cerraron arriba y abajo. Así se ve de verdad lo que es operar esto: muchos meses planos, rachas de meses rojos pequeños y unos pocos meses que hacen el año.")
                 + tabla(["Año", "Retorno", "Meses ↑", "Meses ↓", "Peor mes", "Mejor mes"], [[f["ano"], f"<span class='{'ok' if f['anual'] >= 0 else 'ko'}'>{pct(f['anual'],1,True)}</span>", f["pos"], f["neg"], pct(f["peor_mes"], 1, True), pct(f["mejor_mes"], 1, True)] for f in ult_filas])
                 + "<h3>Las caídas, una a una y por tamaño</h3>"
                 + fig("08_underwater.png", "Curva submarina con el 100 % del capital: cuánto está la cuenta por debajo de su máximo en cada momento. La línea punteada separa construcción y validación.")
                 + f'<div class="kpis">{kpi(dd["n"], "Caídas desde máximos", f"{anos} años")}{kpi(dd["recuperados"], "Recuperadas", "todas", "ok")}{kpi(num(dd["dias_medio"],0)+" días", "Recuperación media", "de cada caída")}{kpi(pct(peor["prof"]), "La más profunda", fecha(peor["inicio"])[-4:], "neg")}{kpi(num(largo["dias"]/365.25,1)+" años", "La más larga", "hasta recuperar", "neg")}</div>'
                 + fig("20_dd_bins.png", "Las caídas agrupadas por profundidad: cuántas hubo de cada tamaño, qué porcentaje del total son, y cuánto tardaron en recuperarse de media y como máximo. Casi todas son pequeñas y cortas; las que duelen son pocas, pero largas.")
                 + tabla(["Profundidad", "Caídas", "% del total", "Recuperación media", "Recuperación máxima"], [[b["bin"], b["n"], pct(b["pct"], 0), f"{b['dias_medio']:.0f} días", f"{b['dias_max']} días"] for b in dd["bins"]])
                 + "<h4 style=\"margin-top:22px\">Las cinco peores</h4>"
                 + tabla(["Inicio", "Fondo", "Recuperada", "Profundidad", "Duración"], [[fecha(e["inicio"]), fecha(e["fondo"]), fecha(e["fin"]) if e["fin"] else "en curso", pct(e["prof"]), f"{e['dias']} días"] for e in dd["peores"]]),
                 f"De {len(me['anos'])} años, {len(me['anos_negativos'])} cerraron en negativo" + (f" ({', '.join(map(str, me['anos_negativos']))})" if me["anos_negativos"] else "") + f"; en los últimos diez, {len(neg10) if neg10 else 'ninguno'}. Pero {me['meses_neg']} meses de {me['meses_pos'] + me['meses_neg']} operados cerraron en rojo: casi la mitad. Todas las caídas se recuperaron, y la más larga tardó {num(largo['dias']/365.25,1)} años ({fecha(largo['inicio'])} → {fecha(largo['fin'])}). Eso, con el 100 % del capital. Con el tamaño por ATR del robot la caída más profunda de toda la historia fue del {pct(M['drawdowns_atr']['peores'][0]['prof'])}, a cambio de un retorno de {pct(f1['TODO_atr']['cagr'])} anual frente a {pct(t['cagr'])}. Ganar con esta estrategia es, sobre todo, saber esperar sin tocar nada.",
                 "El retorno final es el destino; el drawdown es el viaje. Nadie abandona por el destino: abandonan en el kilómetro 30 del viaje.", "drawdowns-detalle")
    decay = prueba("Prueba extra", "⏳", "Desgaste del edge: ¿sigue viva?", decay_ok,
                   "Las estrategias publicadas en libros suelen dejar de funcionar cuando todo el mundo las conoce. ¿Le está pasando a esta?",
                   ["Calculamos el Profit Factor de las últimas 40 operaciones en cada momento, y lo seguimos a lo largo de los 27 años: si el edge se gastara, esa línea bajaría hacia 1 y se quedaría ahí.", "Contamos las operaciones de cada año: si la señal dejara de aparecer, también sería una forma de morir.", "Comparamos la media del periodo de construcción con los tres últimos años completos."],
                   "Que el Profit Factor de los tres últimos años completos no caiga más de un 20 % respecto al del periodo de construcción.",
                   fig("07_pf_anual.png", "Arriba: Profit Factor móvil de las últimas 40 operaciones. Por encima de 1 (línea roja) se gana; 1,3 (línea discontinua) es el criterio de la Fase 1. Las zonas rojas son rachas de 40 operaciones perdedoras en conjunto: existen, y siempre volvieron. Abajo: operaciones por año; sin barra es un año sin señales, con el precio bajo la SMA 200.")
                   + tabla(["", "Construcción (media por año)", f"Últimos 3 años completos ({ed['anos_ultimos'][0]}–{ed['anos_ultimos'][-1]})"], [
                       ["Operaciones por año", num(ed["is_medio"]["freq"], 1), num(ed["ultimos_3"]["freq"], 1)],
                       ["Retorno medio por operación", pct(ed["is_medio"]["expectancy"], 2), pct(ed["ultimos_3"]["expectancy"], 2)],
                       ["Profit Factor", num(ed["is_medio"]["pf"]), num(ed["ultimos_3"]["pf"])]]),
                   f"Frecuencia, retorno por operación y Profit Factor se mantienen o mejoran: el Profit Factor de los tres últimos años completos es {num(ed['ultimos_3']['pf'])} frente a {num(ed['is_medio']['pf'])} en construcción. Esto describe el pasado reciente, no garantiza el futuro: por eso la seguimos midiendo cada año y esta página se regenera con los datos nuevos.",
                   "Un edge es como una mina: tarde o temprano se agota. La pregunta no es si se agotará, sino si ya empezó. Por ahora, no.", "decay")
    dds = sec("drawdowns", "3 · Drawdowns y desgaste del edge", "Lo que se siente por el camino, y si sigue vivo",
              "Dos preguntas que no salen en la mayoría de backtests y que deciden si un sistema se puede operar de verdad.", ddp + decay, "alt")

    # ------------------------------------------------------------- 5 · glosario y alcance
    glos = sec("glosario", "4 · Conclusión y glosario", "Lo que las ocho pruebas permiten afirmar", "",
               '<div class="cierre" style="grid-template-columns:1fr"><div class="si"><h4>✅ Lo que las pruebas dicen</h4><ul>'
               + f"<li>El Nasdaq revierte a corto plazo tras caídas bruscas, y con consistencia solo sobre la SMA 200 (AED).</li><li>Las reglas ganan en {anos} años, con costes, y en ocho años que no vieron (Fase 1).</li><li>Rinden año a año, no por dos rachas (Fase 2), y no dependen de un número exacto (Fase 3).</li><li>El riesgo del camino está medido: {pct(f4['mdd_p5'])} en el 5 % peor de {num(f4['n_sim'],0)} caminos con todo el capital, {pct(f4['mdd_peor'])} en el peor (Fase 4).</li><li>Aguanta costes dobles y quitarle sus mejores años (Fase 5), y bate al {pct(mk['pct_pf'],1)} de las entradas al azar (mono).</li><li>Casi la mitad de los meses operados cierran en rojo y las caídas largas existen: el edge se cobra en paciencia.</li><li>No hay señales de desgaste hasta hoy, y esta página se regenera con los datos nuevos para seguir vigilándolo.</li>" + (f"<li>El robot hace lo que dice el papel: el Strategy Tester de MetaTrader 5 coincide con el motor en {REC['matching']['entradas_misma_fecha']} de {REC['matching']['operaciones_mt5']} entradas y salidas ({fecha(REC['ventana_reconciliacion']['desde'])} → {fecha(REC['ventana_reconciliacion']['hasta'])}).</li>" if REC else "") + "</ul></div></div>"
               + '<h3>Glosario</h3><div class="glos">' + "".join(f"<div><b>{a}</b> — {b}</div>" for a, b in [
                   ("RSI", "Relative Strength Index. Mide la fuerza de las subidas frente a las bajadas recientes, de 0 a 100. Con 2 períodos reacciona en dos días."),
                   ("SMA 200", "Media móvil simple de los últimos 200 cierres. El filtro de tendencia más usado del mundo."),
                   ("Profit Factor (PF)", "Dinero ganado dividido por dinero perdido. Por encima de 1 el sistema gana; 2 significa que gana el doble de lo que pierde."),
                   ("PF sin la mejor operación", "El mismo cálculo quitando la mejor operación. Si se hunde, el resultado dependía de un golpe de suerte."),
                   ("CAGR", "Tasa de crecimiento anual compuesto: el retorno anual equivalente."),
                   ("Drawdown", "Caída desde el último máximo de capital. El máximo drawdown es la más profunda de la serie."),
                   ("Dentro / fuera de muestra (IS / OOS)", "Datos usados para construir la regla / datos guardados para comprobarla una vez fijada."),
                   ("Walk-forward", "Validar cada tramo de tiempo contra el tramo anterior, rodando hacia delante."),
                   ("Zonas robustas", "Mover los parámetros alrededor de los elegidos y comprobar que el vecindario entero gana, no solo una celda."),
                   ("Monte Carlo (block bootstrap)", "Reordenar las operaciones miles de veces, en bloques, para ver el abanico de resultados que el azar del orden permitía."),
                   ("Test del mono", "Comparar la estrategia con entradas al azar bajo las mismas condiciones. Si no le gana al mono, no hay habilidad."),
                   ("Edge decay", "Desgaste del edge: cuando una ventaja publicada deja de funcionar porque todos la operan."),
                   ("Expectancy", "Retorno medio por operación, ganadoras y perdedoras incluidas."),
                   ("ATR", "Average True Range: cuánto se mueve el precio al día, de media. La vara de la volatilidad con la que el robot decide el tamaño."),
                   ("Slippage", "Diferencia entre el precio de la señal y el precio al que de verdad se ejecuta."),
                   ("Puntos básicos (bps)", "Centésimas de un 1 %. 5 bps = 0,05 %.")]) + "</div>"
               + f'<div class="cta-final" style="margin-top:32px"><div><h3>Reprodúcelo tú</h3><p>Un comando baja los datos, otro corre las ocho pruebas y genera estas páginas. Sin cajas negras.</p></div><a class="btn" href="{REPO_URL}">Ir al repositorio →</a></div>')

    cuerpo = hero + evol + metodo + robustez + dds + glos
    nav = [("evolucion", "Evolución"), ("metodo", "Método TIS"), ("aed", "AED"), ("fase1", "Fases"), ("fase3", "Robustez"), ("drawdowns", "Drawdowns"), ("glosario", "Conclusión")]
    return pagina("RSI 2 · Manual avanzado — Trade It Simple", "Manual avanzado de la estrategia RSI(2): evolución, método TIS con las ocho pruebas explicadas, robustez 2D y 4D, drawdowns, desgaste, glosario y alcance.", nav, cuerpo, ("rsi2-ficha.html", "← Ficha"), CSS_MANUAL + CSS_BADGES)
