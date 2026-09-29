"""La ficha de la estrategia (guia/rsi2-ficha.html). Importa las piezas comunes de comun.py."""
from comun import *

CSS_FICHA = """
.badge.c1{background:#e6faef;color:#0d3d24;border-color:#b9efd1}.badge.c2{background:#e8f0fa;color:#1d3f6b;border-color:#c5d8f2}
.badge.c3{background:#fff5e9;color:#9a5a15;border-color:#f0d3ab}.badge.c4{background:#f3e8fa;color:#4c2a73;border-color:#dcc6ee}
.badge.c5{background:#e6f7f7;color:#0f4c4c;border-color:#b8e3e3}.badge.c6{background:#132620;color:#fff;border-color:#132620}
.strip{display:grid;grid-template-columns:1fr 1fr 1.3fr 1.4fr;gap:10px;margin:22px 0 0}
.chart{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px;margin:26px 0 8px}
.chart .tog{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.chart .tog button{font:inherit;font-size:13px;font-weight:700;padding:6px 12px;border-radius:999px;border:2px solid var(--c);background:var(--c);color:#fff;cursor:pointer}
.chart .tog button.off{background:#fff;color:var(--c);opacity:.7}
.chart canvas{width:100%;height:auto;display:block}.chart .tip{font-size:13px;color:var(--sub);min-height:20px;margin-top:6px;font-variant-numeric:tabular-nums}
.chart .print{display:none}@media print{.chart canvas,.chart .tog,.chart .tip{display:none}.chart .print{display:block}}
.libro{display:grid;grid-template-columns:78px 1fr;gap:14px;align-items:start}
.portada{width:78px;height:112px;border-radius:4px 8px 8px 4px;box-shadow:3px 3px 0 #0003,inset 6px 0 0 #0002;padding:10px 8px;color:#fff;font-weight:800;font-size:10.5px;line-height:1.2;display:flex;flex-direction:column;justify-content:space-between}
.portada small{font-weight:600;opacity:.85;font-size:9px}.portada.p1{background:linear-gradient(160deg,#1d3f6b,#0f2440)}.portada.p2{background:linear-gradient(160deg,#0e9c58,#0b3d24)}.portada.p3{background:linear-gradient(160deg,#63756b,#3a4b44)}
.portada img{width:78px;height:112px;object-fit:cover;border-radius:4px 8px 8px 4px}
.niveles{grid-template-columns:repeat(4,1fr)}
.strip div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;font-size:14px}
.strip b{display:block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:2px}
.strip span{font-weight:800;color:var(--brand-ink);font-size:16px}.strip a{font-weight:800}
.oos-head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:38px 0 12px}
.oos-head h3{margin:0;font-size:22px}.oos-head span{color:var(--muted);font-size:14.5px}
.kpis6{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
.kpis6 .kpi .v{font-size:28px}
.regla-big{background:#fff;border:1px solid var(--line);border-radius:18px;padding:0;overflow:hidden;display:grid;grid-template-columns:150px 1fr}
.regla-big .lab{padding:22px 18px;color:#fff;display:flex;flex-direction:column;justify-content:center}
.regla-big .lab .k{font-size:11px;letter-spacing:.16em;opacity:.85;font-weight:800}.regla-big .lab .t{font-size:26px;font-weight:900;line-height:1;margin-top:6px;letter-spacing:-.01em}
.regla-big .cont{padding:18px 22px}.regla-big .cont h4{margin:0 0 6px;font-size:20px}.regla-big .cont p{margin:0 0 12px;color:var(--sub);font-size:15px}
.regla-big pre{border-radius:10px;font-size:13.5px;padding:12px 14px;max-height:none}
.rb-f .lab{background:var(--azul)}.rb-e .lab{background:var(--brand)}.rb-s .lab{background:var(--neg)}.rb-n .lab{background:#63756b}
.reglas-big{display:grid;gap:14px;margin-top:22px}
.specs{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px}
.spec{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 16px 12px;border-top:5px solid var(--line);min-width:0}
.spec pre,.regla-big pre{white-space:pre-wrap;word-break:break-word}
.spec .k{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:800}.spec .t{font-size:22px;font-weight:900;margin:4px 0 6px}
.spec p{margin:0 0 10px;font-size:13.5px;color:var(--sub)}.spec pre{border-radius:8px;font-size:12.5px;padding:9px 12px}
.spec.s1{border-top-color:#9a5a15}.spec.s2{border-top-color:#1d3f6b}.spec.s3{border-top-color:#4c2a73}.spec.s4{border-top-color:#0f4c4c}
.niveles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}
.nivel{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px 22px;border-top:7px solid var(--line)}
.nivel.n1{border-top-color:var(--azul)}.nivel.n2{border-top-color:#f0a860}.nivel.n3{border-top-color:var(--brand)}
.nivel .ico{font-size:28px}.nivel h4{margin:6px 0 0;font-size:20px}.nivel .sub{color:var(--muted);font-size:13.5px;margin:2px 0 12px;min-height:2.7em}
.nivel .big{font-size:34px;font-weight:900;letter-spacing:-.02em;line-height:1}.nivel .bl{font-size:12.5px;color:var(--muted);margin-bottom:12px}
.nivel .fila{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:baseline;font-size:13.5px;padding:7px 0;border-top:1px solid var(--line)}.nivel .fila span{color:var(--sub)}.nivel .fila b{font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right}
.nivel.n1 .big{color:var(--azul)}.nivel.n2 .big{color:#c97d1e}.nivel.n3 .big{color:var(--brand)}.nivel.n4{border-top-color:var(--neg)}.nivel.n4 .big{color:var(--neg)}
.atr{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:16px}
.atr div{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}.atr .n{font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.1em}
.atr .f{font-family:var(--mono);font-size:13.5px;color:var(--brand-ink);margin:6px 0;background:var(--panel2);padding:6px 8px;border-radius:6px}
.atr .r{font-size:22px;font-weight:900}.atr p{margin:6px 0 0;font-size:13px;color:var(--sub)}
.flujo{display:grid;grid-template-columns:repeat(5,1fr);gap:0;margin-top:22px;align-items:stretch}
.flujo > div{background:#fff;border:1px solid var(--line);padding:16px 14px;position:relative;text-align:center}
.flujo > div:first-child{border-radius:14px 0 0 14px}.flujo > div:last-child{border-radius:0 14px 14px 0}
.flujo .ic{font-size:26px}.flujo b{display:block;font-size:14.5px;margin:6px 0 2px}.flujo span{font-size:12.5px;color:var(--muted)}
.flujo > div:not(:last-child)::after{content:"›";position:absolute;right:-9px;top:50%;transform:translateY(-50%);width:18px;height:18px;border-radius:50%;background:var(--brand);color:#fff;font-weight:900;font-size:14px;line-height:18px;z-index:2}
.vias{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}
.via{border-radius:18px;padding:22px;border:1px solid var(--line);background:#fff;border-top:7px solid var(--line)}
.via.v1{border-top-color:var(--brand)}.via.v2{border-top-color:var(--azul)}.via.v3{border-top-color:#9a5a15}
.via .ico{font-size:34px}.via h4{margin:8px 0 4px;font-size:19px}.via .tag{display:inline-block;font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:999px;background:var(--panel2);color:var(--sub);margin-bottom:8px}
.via ul{margin:0;padding-left:18px;font-size:14.5px;color:var(--sub)}.via li{margin:4px 0}
.cfd{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.cfd div{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;font-size:14.5px}.cfd h5{margin:0 0 6px;font-size:16px}.cfd ul{margin:0;padding-left:18px;color:var(--sub)}
.rec-big{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}
.recb{border-radius:18px;overflow:hidden;border:1px solid var(--line);background:#fff}
.recb .head{padding:22px;color:#fff}.recb .head .ico{font-size:34px}.recb .head h4{margin:8px 0 0;font-size:19px}.recb .head span{font-size:13px;opacity:.9}
.recb .cuerpo{padding:16px 22px 20px}.recb .cuerpo p{margin:0 0 12px;font-size:14.5px;color:var(--sub)}
.recb.r1 .head{background:linear-gradient(135deg,#0d3d24,#0e9c58)}.recb.r2 .head{background:linear-gradient(135deg,#1d3f6b,#2b6cb0)}.recb.r3 .head{background:linear-gradient(135deg,#3a2560,#7a4fb8)}
@media(max-width:1000px){.niveles{grid-template-columns:1fr 1fr}}
@media(max-width:860px){.strip,.kpis6,.specs,.niveles,.atr,.vias,.rec-big{grid-template-columns:1fr 1fr}.flujo{grid-template-columns:1fr}.flujo > div{border-radius:0}.flujo > div:not(:last-child)::after{display:none}.regla-big{grid-template-columns:110px 1fr}}
@media(max-width:560px){.strip,.kpis6,.specs,.niveles,.atr,.vias,.rec-big,.cfd{grid-template-columns:1fr}.regla-big{grid-template-columns:1fr}.regla-big .lab{padding:14px 18px}}
"""


def portada(cl, fichero, titulo, sub):
    """Portada de libro: usa guia/<fichero> si existe; si no, una portada dibujada con CSS."""
    p = GUIA / fichero
    if p.exists():
        return f'<div class="portada" style="padding:0;background:none;box-shadow:3px 3px 0 #0003"><img src="data:image/jpeg;base64,{base64.b64encode(p.read_bytes()).decode()}" alt="{html.escape(titulo)}"></div>'
    return f'<div class="portada {cl}"><span>{titulo}</span><small>{sub}</small></div>'


def grafico_interactivo():
    """Curva de capital con botones para encender/apagar cada tamaño de posición (canvas + JS, sin librerías)."""
    if not SEM:
        return fig("01_equity.png", "Curva de capital con tres tamaños de posición.")
    series = [("capital", "100 % del capital (reinvirtiendo)", "#0e9c58", True), ("fijo", "10.000 $ fijos por operación (sin reinvertir)", "#c97d1e", True),
              ("atr1", "1 % de riesgo · ATR×2 (el robot)", "#2b6cb0", True), ("atr2", "2 % de riesgo · ATR×2", "#f0a860", False), ("x2", "Apalancado 1:2 (200 %)", "#c8512f", False)]
    datos = json.dumps(dict(fechas=SEM["fechas"], oos=SEM["oos"], series=[dict(k=k, n=n, c=c, on=on, v=SEM[k]) for k, n, c, on in series]))
    botones = "".join(f'<button data-k="{k}" style="--c:{c}" class="{"" if on else "off"}">{n}</button>' for k, n, c, on in series)
    js = """
(function(){const D=%s;const el=document.getElementById('eqchart');const cv=el.querySelector('canvas');const tip=el.querySelector('.tip');const on={};D.series.forEach(s=>on[s.k]=s.on);
const W=1100,H=440,L=62,R=16,T=18,B=34;cv.width=W;cv.height=H;const ctx=cv.getContext('2d');
const xs=D.fechas.map(f=>new Date(f).getTime());const x0=xs[0],x1=xs[xs.length-1];const X=t=>L+(t-x0)/(x1-x0)*(W-L-R);
function lims(){let lo=1e9,hi=-1e9;D.series.forEach(s=>{if(!on[s.k])return;s.v.forEach(v=>{if(v<lo)lo=v;if(v>hi)hi=v;});});if(hi<0)hi=1;lo=Math.min(lo,0.9);return[lo,hi*1.08];}
function draw(hover){const[lo,hi]=lims();const Y=v=>T+(Math.log(hi)-Math.log(Math.max(v,0.05)))/(Math.log(hi)-Math.log(lo))*(H-T-B);ctx.clearRect(0,0,W,H);
ctx.fillStyle='#eef6f1';const xo=X(new Date(D.oos).getTime());ctx.fillRect(xo,T,W-R-xo,H-T-B);ctx.fillStyle='#3a4b44';ctx.font='12px system-ui';ctx.fillText('fuera de muestra →',xo+6,T+14);
ctx.strokeStyle='#e2ede8';ctx.lineWidth=1;ctx.fillStyle='#3a4b44';[0.5,1,1.5,2,3,4,5,6,8,10,15,20].filter(v=>v>=lo&&v<=hi).forEach(v=>{ctx.beginPath();ctx.moveTo(L,Y(v));ctx.lineTo(W-R,Y(v));ctx.stroke();ctx.fillText(v+'×',8,Y(v)+4);});
for(let y=new Date(x0).getFullYear()+1;y<=new Date(x1).getFullYear();y+=2){const tx=X(new Date(y,0,1).getTime());ctx.beginPath();ctx.moveTo(tx,T);ctx.lineTo(tx,H-B);ctx.stroke();ctx.fillText(y,tx-14,H-10);}
D.series.forEach(s=>{if(!on[s.k])return;ctx.strokeStyle=s.c;ctx.lineWidth=2;ctx.beginPath();s.v.forEach((v,i)=>{const x=X(xs[i]),y=Y(v);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
ctx.fillStyle=s.c;ctx.font='bold 12px system-ui';ctx.fillText(s.v[s.v.length-1].toFixed(2)+'×',W-R-46,Y(s.v[s.v.length-1])-4);});
if(hover!=null){const i=hover;ctx.strokeStyle='#132620';ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(X(xs[i]),T);ctx.lineTo(X(xs[i]),H-B);ctx.stroke();ctx.setLineDash([]);
let s=D.fechas[i]+' · ';D.series.forEach(q=>{if(on[q.k])s+=q.n.split(' (')[0].split(' ·')[0]+': '+q.v[i].toFixed(2)+'× · ';});tip.textContent=s.slice(0,-3);
D.series.forEach(q=>{if(!on[q.k])return;ctx.fillStyle=q.c;ctx.beginPath();ctx.arc(X(xs[i]),Y(q.v[i]),4,0,7);ctx.fill();});}}
el.querySelectorAll('.tog button').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.k;on[k]=!on[k];b.classList.toggle('off',!on[k]);draw(null);}));
cv.addEventListener('mousemove',e=>{const r=cv.getBoundingClientRect();const x=(e.clientX-r.left)*W/r.width;const t=x0+(x-L)/(W-L-R)*(x1-x0);let i=0;while(i<xs.length-1&&xs[i]<t)i++;draw(i);});
cv.addEventListener('mouseleave',()=>{draw(null);tip.textContent='';});draw(null);})();""" % datos
    return f"""<div class="chart" id="eqchart"><div class="tog">{botones}</div><canvas></canvas><div class="tip"></div>
<img class="print" src="{img('01_equity.png')}" alt="Curva de capital">
<figcaption style="padding:8px 4px 0">Curva de capital desde {SEM['fechas'][0][:4]}, escala logarítmica. Pulsa cada botón para encender o apagar una forma de dimensionar; pasa el ratón para ver los valores. La zona sombreada es el periodo fuera de muestra: la estrategia se diseñó sin ver esos datos.</figcaption>
<script>{js}</script></div>"""


def ficha():
    f1 = M["fase1"]; o, t, oos = f1["IS"], f1["TODO"], f1["OOS"]
    oa, ta, ob, tb, ox, tx = f1["OOS_atr"], f1["TODO_atr"], f1["OOS_atr2"], f1["TODO_atr2"], f1["OOS_x2"], f1["TODO_x2"]
    meta = M["meta"]; mk = M["monkey"]; ed = M["edge_decay"]; sz = M["sizing"]; lb = M["libro"]; fj = M["fijo"]
    anos = int(meta["hasta"][:4]) - int(meta["desde"][:4])
    dq = DARWINEX["qqq"]; spread_bps = dq["spread_pts"] * dq["point"] / dq["precio"] * 1e4
    swap_bps_dia = -dq["swap_long_pct"] / 365 * 100; swap_trade = swap_bps_dia * t["barras_media"]; coste_cfd = spread_bps + swap_trade

    # ------------------------------------------------------------- hero + números + curva
    hero = f"""<header class="hero"><div class="wrap">
<div class="eyebrow">Estrategia #1 · Reversión a la media · Nasdaq 100</div>
<h1>RSI 2 · Connors<small>Compra el miedo de corto plazo dentro de una tendencia alcista. Y sal en cuanto el precio respira.</small></h1>
<div class="badges"><span class="badge c1">Reversión a la media</span><span class="badge c2">Nasdaq 100 · QQQ / NDX</span><span class="badge c3">Velas diarias</span><span class="badge c4">Solo largos</span><span class="badge c5">Automatizada · EA MT5</span><span class="badge c6">{anos} años de datos</span></div>
<div class="strip"><div><b>Motor usado</b><span>Sentinel</span></div><div><b>Método</b><span>TIS</span></div><div><b>Fuente de datos</b><span>Norgate + Darwinex</span></div><div><b>Replícalo tú</b><a href="{REPO_URL}">Repositorio abierto: datos, motor y código →</a></div></div>
<div class="oos-head"><h3>Números fuera de muestra</h3><span>{fecha(meta['oos_desde'])} → {fecha(meta['oos_hasta'])} · datos que la estrategia nunca vio · 100 % del capital por operación · costes incluidos</span></div>
<div class="kpis6">
{kpi(num(oos['pf']), 'Profit Factor', 'ganado ÷ perdido', 'ok')}
{kpi(pct(oos['cagr']), 'Retorno anual', 'CAGR')}
{kpi(pct(oos['mdd_diario']), 'Peor caída', 'drawdown día a día', 'neg')}
{kpi(pct(oos['wr'],0), 'Aciertos', 'operaciones ganadoras')}
{kpi(oos['n'], 'Operaciones', f"{num(oos['n']/8,0)} al año · {t['n']} en {anos} años")}
{kpi(pct(oos['expectancy'],2,True), 'Por operación', 'retorno medio neto')}
</div>
{grafico_interactivo()}
</div></header>"""

    # ------------------------------------------------------------- 1 · ficha técnica
    def regla(cl, k, t_, h, p, code):
        return f'<div class="regla-big {cl}"><div class="lab"><div class="k">{k}</div><div class="t">{t_}</div></div><div class="cont"><h4>{h}</h4><p>{p}</p><pre><code>{html.escape(code)}</code></pre></div></div>'

    def spec(cl, k, t_, p, code):
        return f'<div class="spec {cl}"><div class="k">{k}</div><div class="t">{t_}</div><p>{p}</p><pre><code>{html.escape(code)}</code></pre></div>'

    ficha_tec = sec("reglas", "1 · Ficha técnica", "Las reglas, sin letra pequeña",
                    "Cuatro reglas y cuatro parámetros. Todo se decide al cierre de la vela diaria y se ejecuta en la apertura del día siguiente: es lo que puede hacer de verdad un robot, o tú con una orden a la apertura.",
                    '<div class="reglas-big">'
                    + regla("rb-f", "Regla 1", "FILTRO", "Solo con la tendencia de fondo a favor", "El cierre del día tiene que estar por encima de la media simple de 200 sesiones. Si no, no hay operación posible: en mercados bajistas la estrategia se queda fuera.",
                            "tendencia_ok = cierre[t] > media_simple(cierre, 200)[t]")
                    + regla("rb-e", "Regla 2", "ENTRADA", "Sobreventa extrema de dos días", "Si al cierre el RSI de 2 períodos está por debajo de 15 (y el filtro se cumple), compramos en la apertura del día siguiente.",
                            "senal_compra = tendencia_ok y rsi(cierre, 2)[t] < 15\nsi senal_compra:  comprar en apertura[t+1]")
                    + regla("rb-s", "Regla 3", "SALIDA", "Dos velas verdes seguidas", "Cuando el precio encadena dos días con cierre por encima de su apertura, el rebote ya ha ocurrido. Vendemos en la apertura del día siguiente.",
                            "verde[t] = cierre[t] > apertura[t]\nsenal_venta = verde[t] y verde[t-1]\nsi senal_venta:  vender en apertura[t+1]")
                    + regla("rb-n", "Regla 4", "SIN STOP", "No hay stop de precio", f"La protección es el filtro de tendencia y la duración corta de cada operación ({num(t['barras_media'],1)} días de media). Los stops fijos, en índices, empeoran esta estrategia: Connors lo midió y nosotros también.",
                            "stop_loss = ninguno   # el tamaño de posición es la gestión del riesgo (ver sección 5)")
                    + "</div>"
                    + '<div class="specs">'
                    + spec("s1", "Timeframe", "D1", "Una vela por sesión. Se mira una vez al día, al cierre de Nueva York.", "velas = diarias\nevaluar_al = cierre[t]\nejecutar_en = apertura[t+1]")
                    + spec("s2", "Activo", "Nasdaq 100", "QQQ (ETF) o NDX / US100 (CFD del índice). La señal es la misma.", "activo = 'QQQ' | 'NDX'\ndatos = Norgate (retorno total) + Darwinex")
                    + spec("s3", "Dirección", "Solo largos", "Nunca vendemos en corto. El corto no es el espejo del largo en índices.", "direccion = LONG\nposiciones_simultaneas = 1")
                    + spec("s4", "Costes", "10 bps", f"En el backtest: 5 puntos básicos por lado, comisión 0. En Darwinex (QQQ, leído del terminal el {fecha(DARWINEX['fecha'])}): spread {dq['spread_pts']} puntos ≈ {num(spread_bps,1)} bps, swap {num(dq['swap_long_pct'],1)} % anual, comisión {dq['comision']}.", "precio_compra = apertura × 1,0005\nprecio_venta  = apertura × 0,9995")
                    + "</div>"
                    + fig("02_operaciones_ano.png", "Las operaciones de un año completo sobre el precio de QQQ. Triángulo verde: compra en la apertura tras la señal. Triángulo rojo: venta en la apertura tras dos velas verdes. La línea discontinua es la media de 200 días.")
                    + fig("16_operacion_ejemplo.png", "Dos operaciones reales del periodo fuera de muestra, vela a vela, con el panel del RSI(2) debajo como lo verías en MetaTrader: la zona verde es la banda de compra (por debajo de 15). La vela sombreada es la de la señal. Se compra en la apertura siguiente, se esperan dos velas verdes seguidas y se vende en la apertura posterior. El porcentaje es el movimiento del precio; en el título se traduce a lo que supone para el capital con cada tamaño.")
                    + "<h3>El RSI 2 tradicional frente al nuestro</h3><p class=\"lead\" style=\"font-size:16px\">La regla del libro entra con RSI(2) ≤ 5 y sale al cerrar por encima de la media de 5. La nuestra entra antes (RSI &lt; 15) y sale con dos velas verdes. Mismos datos, mismos costes, mismo filtro, mismo periodo completo (" + f"{meta['desde'][:4]}–{meta['hasta'][:4]}" + ").</p>"
                    + fig("03_libro_vs_tis.png", f"Capital acumulado con el 100 % por operación durante los {anos} años completos. Verde: nuestra variante. Azul: la regla original de Connors y Alvarez.")
                    + tabla(["", "RSI 2 tradicional (Connors)", "RSI 2 · TIS"], [
                        ["Entrada", "RSI(2) ≤ 5 y cierre > SMA 200", "RSI(2) &lt; 15 y cierre > SMA 200"], ["Salida", "Cierre por encima de la MA(5)", "Dos velas verdes seguidas"],
                        [f"Operaciones · periodo completo ({meta['desde'][:4]}–{meta['hasta'][:4]})", num(lb["TODO"]["n"], 0), f"<b>{num(t['n'], 0)}</b>"],
                        [f"Operaciones · fuera de muestra ({meta['oos_desde'][:4]}–{meta['oos_hasta'][:4]})", num(lb["OOS"]["n"], 0), f"<b>{num(oos['n'], 0)}</b>"],
                        ["Profit Factor · periodo completo", num(lb["TODO"]["pf"]), num(t["pf"])], ["Profit Factor · fuera de muestra", num(lb["OOS"]["pf"]), f"<b>{num(oos['pf'])}</b>"],
                        ["Retorno anual (CAGR) · periodo completo", pct(lb["TODO"]["cagr"]), f"<b>{pct(t['cagr'])}</b>"], ["Peor caída (día a día) · periodo completo", pct(lb["TODO"]["mdd_diario"]), pct(t["mdd_diario"])],
                        ["Capital final · periodo completo", num(1 + lb["TODO"]["ret_total"], 1) + "×", f"<b>{num(1 + t['ret_total'], 1)}×</b>"], ["Días por operación", num(lb["TODO"]["barras_media"], 1), num(t["barras_media"], 1)]])
                    + f'<div class="nota"><b>Detalle que importa:</b> "vela verde" es cierre por encima de la apertura de ese mismo día, que es exactamente lo que mira el robot. Probamos también "cierre por encima del cierre anterior" y el resultado es casi idéntico (Profit Factor fuera de muestra {num(oos["pf"])} frente a {num(M["control_salida_cierre_a_cierre"]["pf"])}). Nos quedamos con la del robot para que lo que lees sea lo que opera.</div>', "alt")

    # ------------------------------------------------------------- 2 · hipótesis
    hipo = sec("hipotesis", "2 · La hipótesis", "Por qué debería funcionar",
               "Antes de tocar un dato hay que saber por qué una idea debería ganar. Si no sabes por qué gana, tampoco sabrás cuándo dejará de hacerlo.",
               f"""<div class="hipo"><div class="k">Hipótesis</div>
<div class="t">Cuando un índice en tendencia alcista sufre dos o tres días de ventas bruscas, el miedo de corto plazo exagera la caída. El precio tiende a volver a su sitio en pocos días.</div>
<div class="w">El RSI de 2 períodos mide esa sobreventa de muy corto plazo. La media de 200 días nos dice si la tendencia de fondo sigue intacta. Compramos solo cuando pasan las dos cosas a la vez, y salimos en cuanto el precio muestra dos días seguidos de compras. No adivinamos suelos: aprovechamos un comportamiento repetido del mercado.</div></div>
<div class="tres">
<div class="card"><span class="n">1</span><h4>Qué explota</h4><p>La reversión a la media de corto plazo en índices de acciones: tras caídas rápidas, el rebote es más probable que la continuación.</p></div>
<div class="card"><span class="n">2</span><h4>Por qué existe</h4><p>Stops que saltan en cadena, gestores que reducen riesgo a la vez y un miedo que se agota en dos o tres sesiones. Después, el flujo comprador de fondo vuelve.</p></div>
<div class="card"><span class="n">3</span><h4>Cuándo falla</h4><p>Cuando la tendencia de fondo se rompe de verdad (2008, 2022). Por eso el filtro de la media de 200: por debajo, la estrategia simplemente no opera.</p></div>
</div>""")

    # ------------------------------------------------------------- 3 · origen
    origen = sec("origen", "3 · El origen", "De dónde viene la idea",
                 "No la inventamos nosotros. La publicaron Larry Connors y Cesar Alvarez; nosotros la adaptamos y la validamos con el método TIS.",
                 f"""<div class="origen"><div>
<div class="libro">{portada('p1', 'portada_libro1.jpg', 'Short Term Trading Strategies That Work', 'Connors · Alvarez · 2008')}<div><b>Short Term Trading Strategies That Work (2008)</b><span>Larry Connors y Cesar Alvarez. Aquí aparece por primera vez el RSI de 2 períodos como señal de sobreventa extrema, con el filtro de la media de 200 y la salida por la media de 5. → <a href="{LIBRO_1}">Ver el libro</a></span></div></div>
<div class="libro">{portada('p2', 'portada_libro2.jpg', 'High Probability ETF Trading', 'Connors · Alvarez · 2009')}<div><b>High Probability ETF Trading (2009)</b><span>Los mismos autores aplican la idea a ETFs con varias variantes (R3, RSI 25/75, RSI 10/6). → <a href="{LIBRO_2}">Ver el libro</a></span></div></div>
<div class="libro">{portada('p3', 'portada_web.jpg', 'RSI(2) · ChartSchool', 'StockCharts · QuantifiedStrategies')}<div><b>Lecturas gratuitas</b><span>La regla original explicada en <a href="{ART_STOCKCHARTS}">StockCharts (ChartSchool)</a> y una revisión moderna con backtests en <a href="{ART_QS}">QuantifiedStrategies</a>.</span></div></div>
</div><div>
<div class="card"><h4>Lo que cambiamos nosotros</h4><p>Entrar antes (RSI(2) &lt; 15 en vez de ≤ 5) y salir con dos velas verdes en vez de al cruzar la media de 5. Resultado: <b>{num(t['n'],0)} operaciones</b> frente a {num(lb['TODO']['n'],0)}, capital final <b>{num(1+t['ret_total'],1)}×</b> frente a {num(1+lb['TODO']['ret_total'],1)}×, con un Profit Factor parecido. Más oportunidades, misma calidad por operación.</p></div>
</div></div>""", "alt")

    # ------------------------------------------------------------- 4 · camino
    camino = sec("camino", "4 · El camino", "De un libro a un robot operando",
                 "Cómo llegó esta estrategia hasta aquí. Cada parada tiene su prueba en el manual avanzado.",
                 f"""<div class="camino">
<div class="hito"><div class="f">2008</div><h4>Connors y Alvarez publican el RSI de 2 períodos</h4><p>Sobreventa extrema de muy corto plazo dentro de una tendencia mayor intacta.</p></div>
<div class="hito"><div class="f">Nuestra variante</div><h4>Entrar antes (RSI &lt; 15) y salir con dos velas verdes</h4><p>Sabemos y apreciamos la documentación, pero también existe el edge decay: lo que publica un libro lo opera todo el mundo. Así que buscamos un filtro que favorezca más la evolución del comportamiento del activo, lo hicimos usando AED y cuidando el fuera de muestra. Resultado: más operaciones con la misma calidad. Reglas fijas, sin ajustar nada por activo.</p></div>
<div class="hito"><div class="f">Backtest</div><h4>{anos} años de QQQ, con costes, separados en construcción y validación</h4><p>{o['n']} operaciones para construir · {oos['n']} para validar en datos nunca vistos.</p></div>
<div class="hito"><div class="f">Validación · método TIS</div><h4>Walk-forward, zonas robustas, Monte Carlo, estrés y test del mono</h4><p>Supera al {pct(mk['pct_pf'],0)} de {num(mk['n_sim'],0)} entradas al azar. Sin desgaste: en los últimos tres años completos el Profit Factor es {num(ed['ultimos_3']['pf'])} frente a {num(ed['is_medio']['pf'])} en construcción. Todo en el <a href="rsi2-validacion.html">manual avanzado</a>.</p></div>
<div class="hito"><div class="f">Hoy</div><h4>Un robot en MetaTrader 5 la opera sobre el Nasdaq 100</h4><p>Con un motor de riesgo encima de la señal: tamaño por ATR y cortacircuitos. En cuenta real desde junio de 2026.</p></div>
</div>""")

    # ------------------------------------------------------------- 5 · riesgo
    ej = sz["ejemplo"]; cap = 10000.0; riesgo = cap * sz["riesgo_pct"]; stop = sz["atr_mult"] * ej["atr"]; unidades = riesgo / stop; posicion = unidades * ej["precio"]
    def nivel(cl, ico, nombre, sub, big, bl, filas):
        fs = "".join(f'<div class="fila"><span>{a}</span><b>{b}</b></div>' for a, b in filas)
        return f'<div class="nivel {cl}"><div class="ico">{ico}</div><h4>{nombre}</h4><div class="sub">{sub}</div><div class="big">{big}</div><div class="bl">{bl}</div>{fs}</div>'
    riesgo_sec = sec("riesgo", "5 · Riesgo y tamaño", "La misma señal, cuatro formas de apostar",
                     "La señal es una. Lo que cambia es cuánto capital pones en cada operación. Elige por tu perfil, no por la cifra más grande: las cuatro curvas tienen exactamente las mismas operaciones.",
                     '<div class="niveles">'
                     + nivel("n1", "🛡️", "Conservador", "1 % de riesgo por operación · lo que hace el robot", pct(oa["cagr"]), "retorno anual fuera de muestra",
                             [("Peor caída", pct(oa["mdd_diario"])), (f"Capital final · {anos} años", num(1 + ta["ret_total"], 2) + "×"), ("Capital en juego (media)", pct(sz["exposicion_media_1pct"], 0)), ("Cortacircuitos", "−3 % día · −8 %")])
                     + nivel("n2", "⚖️", "Intermedio", "2 % de riesgo por operación", pct(ob["cagr"]), "retorno anual fuera de muestra",
                             [("Peor caída", pct(ob["mdd_diario"])), (f"Capital final · {anos} años", num(1 + tb["ret_total"], 2) + "×"), ("Capital en juego (media)", pct(sz["exposicion_media_2pct"], 0)), ("Cómo", "doble riesgo")])
                     + nivel("n3", "🔥", "Decidido", "100 % del capital en cada operación", pct(oos["cagr"]), "retorno anual fuera de muestra",
                             [("Peor caída", pct(oos["mdd_diario"])), (f"Capital final · {anos} años", num(1 + t["ret_total"], 2) + "×"), ("Capital en juego", "100 %"), ("Cómo", "sin apalancar")])
                     + nivel("n4", "⚡", "Arriesgado", "apalancamiento 1:2 · 200 % del capital", pct(ox["cagr"]), "retorno anual fuera de muestra",
                             [("Peor caída", pct(ox["mdd_diario"])), (f"Capital final · {anos} años", num(1 + tx["ret_total"], 2) + "×"), ("Capital en juego", "200 % (CFD)"), ("Peor caída histórica", pct(M["drawdowns_x2"]["peores"][0]["prof"]))])
                     + "</div>"
                     + f'<div class="nota"><b>Sobre el nivel arriesgado:</b> solo es posible con CFD (el ETF no se apalanca). Duplica el retorno y duplica las caídas: la peor histórica pasa del {pct(M["drawdowns"]["peores"][0]["prof"])} al {pct(M["drawdowns_x2"]["peores"][0]["prof"])}, y encima pagas swap por el doble de nominal. Si no aguantas ver un tercio del capital desaparecer sin cambiar nada, no es tu nivel.</div>'
                     + fig("10_riesgo.png", "Las cuatro curvas con las mismas operaciones. Abajo, la caída desde máximos de cada una. Escala logarítmica: la misma distancia vertical es el mismo porcentaje.")
                     + f"""<h3>Qué calcula el ATR</h3>
<p class="lead" style="font-size:16px">El rango verdadero de un día es lo más grande de tres cosas: la altura de la vela (máximo − mínimo), la distancia del máximo al cierre anterior, o la del mínimo al cierre anterior. Así cuenta también los huecos de apertura. El ATR(14) es la media de los últimos 14 rangos: cuánto se mueve el activo en un día normal.</p>
{fig('17_atr.png', 'A la izquierda, las 14 velas anteriores a la última señal del backtest; la barra naranja junto a cada vela es su rango verdadero (incluye el hueco respecto al cierre anterior cuando lo hay). A la derecha, esos 14 rangos y su media: el ATR.')}
<h3>Cómo se aplica el ATR (lo que hace el robot antes de cada compra)</h3>
<p class="lead" style="font-size:16px">El robot no pone un stop en el mercado: usa un <b>stop virtual</b> a 2 × ATR solo para calcular cuántas unidades comprar, de forma que si el precio cayera esa distancia perderías el 1 % del capital. Ejemplo con la última operación real del backtest y 10.000 € de capital:</p>
<div class="atr">
<div><div class="n">PASO 1 · RIESGO</div><div class="f">10.000 € × 1 %</div><div class="r">{num(riesgo,0)} €</div><p>Lo máximo que aceptas perder si el precio recorre el stop virtual.</p></div>
<div><div class="n">PASO 2 · STOP VIRTUAL</div><div class="f">2 × ATR(14) = 2 × {num(ej['atr'],2)}</div><div class="r">{num(stop,2)} $</div><p>Distancia de precio que equivale a "la operación ha salido mal".</p></div>
<div><div class="n">PASO 3 · UNIDADES</div><div class="f">{num(riesgo,0)} € ÷ {num(stop,2)} $</div><div class="r">{num(unidades,1)}</div><p>Acciones de QQQ (o contratos equivalentes del CFD).</p></div>
<div><div class="n">PASO 4 · POSICIÓN</div><div class="f">{num(unidades,1)} × {num(ej['precio'],2)} $</div><div class="r">{num(posicion,0)} €</div><p>El {pct(posicion/cap,0)} del capital en esta operación. Con más volatilidad, menos.</p></div>
</div>
<div class="info">Si el precio cae más de 2 × ATR, el robot <b>no cierra</b>: sigue esperando las dos velas verdes. El stop es virtual porque, medido, cerrar por precio empeora la estrategia. En {anos} años, con este tamaño, la peor caída fue del {pct(M['drawdowns_atr']['peores'][0]['prof'])} y los cortacircuitos del −8 % nunca habrían saltado.</div>""", "alt")

    # ------------------------------------------------------------- 6 · dónde
    ndx_txt = ""
    if NDX:
        no = NDX["fase1"]["OOS"]
        ndx_txt = f'<div class="info"><b>Comprobado en el instrumento real:</b> mismo motor, mismas reglas, sobre las velas diarias del propio bróker para el CFD del Nasdaq 100 ({NDX["meta"]["desde"][:4]}–{NDX["meta"]["hasta"][:4]}): {no["n"]} operaciones fuera de muestra, Profit Factor {num(no["pf"])}, peor caída {pct(no["mdd_diario"])}.</div>'
    if REC:
        ndx_txt += f'<div class="info"><b>El robot hace lo que dice esta página:</b> el Strategy Tester de MetaTrader 5 (Darwinex, {REC["strategy_tester"]["calidad_historial"]}) coincide con el motor en {REC["matching"]["entradas_misma_fecha"]} de {REC["matching"]["operaciones_mt5"]} entradas y {REC["matching"]["salidas_misma_fecha"]} de {REC["matching"]["operaciones_mt5"]} salidas entre {fecha(REC["ventana_reconciliacion"]["desde"])} y {fecha(REC["ventana_reconciliacion"]["hasta"])}. Las únicas diferencias son céntimos de spread en el precio de entrada.</div>'
    donde = sec("donde", "6 · Dónde operarla", "Qué necesitas y cómo es un día",
                "Pensada para el Nasdaq 100 en velas diarias. Da igual si lo operas como ETF (QQQ) o como CFD del índice (NDX / US100): la señal es la misma. Tres formas de hacerlo, de más a menos automática.",
                f"""<div class="vias">
<div class="via v1"><div class="ico">🤖</div><span class="tag">Recomendada</span><h4>Con el robot</h4><ul><li>MetaTrader 5 con un bróker que ofrezca el Nasdaq 100 como CFD en gráfico diario.</li><li>Nuestra referencia: Darwinex sobre NDX, en un servidor 24/7.</li><li>Lo hace todo: señal, tamaño por ATR, cortacircuitos y avisos al móvil.</li></ul></div>
<div class="via v2"><div class="ico">🔔</div><span class="tag">Semiautomática</span><h4>Con alertas de TradingView</h4><ul><li>El indicador en Pine Script marca la señal y te avisa al cierre.</li><li>Tú pones la orden de compra a la apertura en tu bróker (ETF o CFD).</li><li>Ideal si no quieres un servidor pero sí disciplina.</li></ul></div>
<div class="via v3"><div class="ico">✍️</div><span class="tag">Manual</span><h4>A mano, cinco minutos al día</h4><ul><li>Al cierre miras dos números: ¿cierre por encima de la SMA 200? ¿RSI(2) por debajo de 15?</li><li>Si sí, orden de compra a la apertura del día siguiente.</li><li>Cada tarde compruebas si hubo dos velas verdes.</li><li><b>Solo recomendable si estás aprendiendo</b> y quieres entender la ejecución. Recuerda que tu objetivo es escalar y despegarte de la pantalla.</li></ul></div>
</div>
<h3>Un día en la vida de la estrategia</h3>
<div class="flujo">
<div><div class="ic">🕓</div><b>Cierre de Nueva York</b><span>22:00 h en España</span></div>
<div><div class="ic">📏</div><b>¿Cierre &gt; SMA 200?</b><span>si no, no hay nada que hacer</span></div>
<div><div class="ic">📉</div><b>¿RSI(2) &lt; 15?</b><span>sobreventa extrema</span></div>
<div><div class="ic">🛒</div><b>Compra a la apertura</b><span>15:30 h del día siguiente</span></div>
<div><div class="ic">🟩🟩</div><b>Dos velas verdes → vendes</b><span>a la apertura siguiente · {num(t['barras_media'],1)} días de media</span></div>
</div>
<h3>ETF o CFD: lo que cambia</h3>
<div class="cfd">
<div><h5>📦 QQQ (ETF)</h5><ul><li>Cobra dividendos (el backtest los incluye).</li><li>Sin swap nocturno; comisión del bróker por operación.</li><li>Sin apalancamiento: el nivel "Decidido" es el máximo.</li></ul></div>
<div><h5>📈 NDX / US100 (CFD)</h5><ul><li>No paga dividendos; el bróker cobra swap por cada noche en posición.</li><li>Con {num(t['barras_media'],1)} días de media por operación el efecto es pequeño, pero existe.</li><li>Permite apalancar: no lo hagas por encima del nivel que elegiste.</li></ul></div>
</div>
<div class="info"><b>Lo que cuesta un CFD, de media, en Darwinex</b> (specs del QQQ leídas del terminal el {fecha(DARWINEX['fecha'])}): spread {dq['spread_pts']} puntos ≈ <b>{num(spread_bps,1)} bps</b> por operación · swap {num(dq['swap_long_pct'],1)} % anual ≈ {num(swap_bps_dia,1)} bps por noche, que con {num(t['barras_media'],1)} noches de media son <b>{num(swap_trade,1)} bps</b> · comisión {dq['comision']}. Total medio: <b>≈ {num(coste_cfd,0)} bps por operación</b>, frente a los 10 bps que asume el backtest. El CFD del índice (NDX) tiene el mismo swap anual; su spread lo ves en tu terminal.</div>{ndx_txt}""")

    # ------------------------------------------------------------- 7 · recursos
    ea_esc = html.escape(EA)
    pine_btn = f'<a class="btn" href="{PINE_URL}">Abrir en TradingView →</a>' if PINE_URL else '<a class="btn off">Enlace pendiente de publicar</a>'
    recursos = sec("recursos", "7 · Recursos", "El código, completo y a la vista",
                   "Incluye los datos, el motor de backtest en Python, los resultados reproducibles y el código del robot para MetaTrader 5.",
                   f"""<div class="rec-big">
<div class="recb r1"><div class="head"><div class="ico">🤖</div><h4>Robot para MetaTrader 5</h4><span>MQL5 · v2.01 · el que opera en real</span></div><div class="cuerpo"><p>EA completo con motor de riesgo: tamaño por ATR, cortacircuitos y alertas push. Despliégalo abajo o descárgalo.</p><a class="btn sec" href="{REPO_URL}/blob/main/codigo/TIS_RSI2_MeanReversion.mq5">Descargar del repositorio</a></div></div>
<div class="recb r2"><div class="head"><div class="ico">🔔</div><h4>Indicador para TradingView</h4><span>Pine Script · señal y alertas</span></div><div class="cuerpo"><p>Marca entradas y salidas sobre el gráfico y te avisa al cierre. Para la vía semiautomática.</p>{pine_btn}</div></div>
<div class="recb r3"><div class="head"><div class="ico">🐍</div><h4>Motor de backtest</h4><span>Python · Sentinel · reproducible</span></div><div class="cuerpo"><p>Descarga los datos, reproduce el backtest y revisa las cinco fases de validación con el mismo motor utilizado en el research.</p><a class="btn sec" href="{REPO_URL}">Ir al repositorio</a></div></div>
</div>
<details class="code"><summary><span class="tag">MQL5</span> TIS_RSI2_MeanReversion.mq5 · robot para MetaTrader 5 <span class="arrow">▼</span></summary><div class="body">
<div class="meta">Parámetros de la estrategia bloqueados (RSI 2 · umbral 15 · SMA 200). Motor de riesgo configurable: 1 % por operación, stop virtual ATR(14)×2, cortacircuitos −3 % diario y −8 % total. Compílalo en MetaEditor y cárgalo en un gráfico D1 del Nasdaq 100. <button class="copiar">Copiar</button></div>
<pre><code>{ea_esc}</code></pre></div></details>
<details class="code"><summary><span class="tag">Python</span> La señal en 12 líneas · lo que hace el motor por dentro <span class="arrow">▼</span></summary><div class="body">
<div class="meta">Extracto del motor. Señal al cierre de T, ejecución en la apertura de T+1, 5 puntos básicos de coste por lado. <button class="copiar">Copiar</button></div>
<pre><code>{html.escape('''sma200 = close.rolling(200).mean()
rsi2   = rsi_wilder(close, 2)
verde  = close > open                      # vela verde: cierra por encima de su apertura

for i in range(2, len(df)):
    if not en_posicion:
        if rsi2[i-1] < 15 and close[i-1] > sma200[i-1]:      # señal al cierre de ayer
            precio_entrada = open[i] * (1 + 0.0005)           # compra en la apertura de hoy
            en_posicion = True
    else:
        if verde[i-1] and verde[i-2]:                         # dos velas verdes seguidas
            precio_salida = open[i] * (1 - 0.0005)            # venta en la apertura de hoy
            en_posicion = False''')}</code></pre></div></details>
<div class="cta-final" style="margin-top:32px"><div><h3>Manual avanzado: cómo la validamos</h3><p>El método TIS paso a paso, las cinco fases con sus números, el test del mono, el desgaste del edge y los drawdowns. Mismos datos, mismo motor.</p></div><a class="btn" href="rsi2-validacion.html">Abrir el manual avanzado →</a></div>""", "alt")

    cuerpo = hero + ficha_tec + hipo + origen + camino + riesgo_sec + donde + recursos
    nav = [("reglas", "Reglas"), ("hipotesis", "Hipótesis"), ("origen", "Origen"), ("camino", "Camino"), ("riesgo", "Riesgo"), ("donde", "Dónde"), ("recursos", "Código")]
    return pagina("RSI 2 · Connors — Trade It Simple", "Estrategia RSI(2) sobre el Nasdaq 100: reglas, resultado, hipótesis, origen, riesgo, dónde operarla y código.", nav, cuerpo, ("rsi2-validacion.html", "Manual avanzado →"), CSS_FICHA)
