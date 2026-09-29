# RSI 2 — Trade It Simple

Estrategia **#1** del material de trading sistemático de [Trade It Simple](https://instagram.com/mariellangsaez):
reversión a la media de corto plazo sobre el Nasdaq 100, con el RSI de 2 períodos de Connors y Alvarez.

Aquí está **todo**: la hipótesis, el origen, las reglas, el robot que la opera y el motor que generó
cada cifra y cada gráfico de la guía. Sin cajas negras: un comando baja los datos, otro corre las
cinco fases de validación y construye las páginas.

> La estrategia no es el premio. El premio es aprender a **construir, validar y confiar** en la tuya.

---

## 📘 Empieza por aquí

Abre en el navegador (son autocontenidas, no necesitan internet):

- **[`guia/rsi2-ficha.html`](guia/rsi2-ficha.html)** — la estrategia de principio a fin: hipótesis, origen,
  método TIS, reglas, resultado, riesgo, dónde operarla y el código.
- **[`guia/rsi2-validacion.html`](guia/rsi2-validacion.html)** — la validación completa, fase a fase:
  backtest dentro/fuera de muestra, walk-forward, zonas robustas, Monte Carlo, estrés, test del mono,
  desgaste del edge y drawdowns.

## 🚀 Reprodúcelo tú

```bash
pip install -r requirements.txt
python descargar_datos.py            # baja QQQ diario de Yahoo Finance a data/QQQ_D1.csv
python descargar_datos.py --norgate  # o de Norgate (retorno total), la fuente de las cifras de la guía
python motor/rsi2_motor.py         # corre las 5 fases + extras → resultados/ (JSON, trades, gráficos)
python motor/construir_html.py     # construye las dos páginas de guia/
```

El motor acepta cualquier CSV diario con columnas `Date,Open,High,Low,Close`:

```bash
python motor/rsi2_motor.py --csv mis_datos.csv --etiqueta NDX --solo-metricas
```

## 📐 Las reglas (las mismas en el motor y en el robot)

| | |
|---|---|
| **Filtro** | Cierre diario > SMA(200) |
| **Entrada** | RSI(2) < 15 al cierre → compra en la apertura del día siguiente |
| **Salida** | Dos velas verdes consecutivas (cierre > apertura) → venta en la apertura del día siguiente |
| **Stop** | Ninguno de precio. El robot dimensiona con 1 % de riesgo y stop virtual ATR(14)×2 |
| **Costes** | 5 puntos básicos por lado, comisión 0 |

## 🗂️ Estructura

```
├── guia/                        Las dos páginas HTML (empieza aquí) + logo
├── motor/
│   ├── rsi2_motor.py            Backtest, 5 fases, monkey test, edge decay, drawdowns, gráficos
│   └── construir_html.py        Genera guia/*.html a partir de resultados/
├── codigo/
│   └── TIS_RSI2_MeanReversion.mq5   Robot para MetaTrader 5 (v2.01, el que opera en real)
├── resultados/
│   ├── metricas.json            Todas las cifras (QQQ)
│   ├── metricas_NDX.json        Mismas reglas sobre los datos del bróker (solo métricas)
│   ├── trades.csv               Las operaciones, una a una
│   ├── equity_diaria.csv        Curva de capital diaria con los cinco sizings
│   ├── equity_semanal.json      Curvas semanales para el gráfico interactivo de la ficha
│   ├── graficos/                Los 20 gráficos de la guía
│   └── reconciliacion_mt5.json     Evidencia de reconciliación backtest ↔ Strategy Tester (40/40)
├── data/                        QQQ_D1.csv (se regenera con descargar_datos.py)
├── descargar_datos.py
└── requirements.txt
```

## ⚠️ Lo que no afirmamos

- No hay resultados de cuenta real en esta guía (el robot opera en real desde junio de 2026).
- El backtest es sobre QQQ (Norgate, retorno total); sobre el CFD del bróker el comportamiento es coherente,
  pero swaps y horarios no están modelados. Los datos de Norgate no se redistribuyen (ver `data/LEEME.md`).
- La reconciliación formal backtest ↔ Strategy Tester de MetaTrader está cerrada sobre la ventana 2024–2026: 40/40 entradas y 40/40 salidas coinciden en fecha. Las diferencias de precio de entrada corresponden al spread/ask de ejecución del bróker.

Material educativo. No es asesoría financiera. Los resultados pasados no garantizan resultados futuros.
