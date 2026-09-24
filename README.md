# RSI 2 — Trade It Simple

Estrategia **#1** del material de trading sistemático de Trade It Simple:
reversión a la media de corto plazo sobre el Nasdaq 100, a partir del trabajo de RSI(2) de Connors y Alvarez.

Este repositorio contiene los **datos, reglas, motor de backtest, resultados y código de ejecución** necesarios para inspeccionar y reproducir el research.

> La estrategia no es el premio. El premio es aprender a **construir, validar y confiar** en la tuya.

---

## 📘 Empieza por aquí

Si es tu primera vez en el repositorio:

1. Revisa las reglas de la estrategia.
2. Abre `resultados/trades.csv` para ver las operaciones una a una.
3. Revisa `resultados/metricas.json`.
4. Explora los gráficos dentro de `resultados/graficos/`.
5. Ejecuta el motor para reproducir los resultados.
6. Después revisa la implementación para MetaTrader 5.

---

## 🚀 Reprodúcelo tú

Instala las dependencias:

```bash
pip install -r requirements.txt
```

El dataset utilizado ya está incluido en:

```text
data/QQQ_D1.csv
```

Si quieres volver a descargarlo:

```bash
python descargar_datos.py
```

Ejecuta el motor:

```bash
python motor/rsi2_motor.py
```

Los resultados se generan en `resultados/`.

El motor también acepta otros CSV diarios con columnas:

```text
Date, Open, High, Low, Close
```

Ejemplo:

```bash
python motor/rsi2_motor.py --csv mis_datos.csv --etiqueta TEST --solo-metricas
```

---

## 📐 Las reglas

| | |
|---|---|
| **Filtro** | Cierre diario > SMA(200) |
| **Entrada** | RSI(2) < 15 al cierre → compra en la apertura siguiente |
| **Salida** | Dos velas verdes consecutivas → venta en la apertura siguiente |
| **Dirección** | Solo largos |
| **Temporalidad** | Diario |
| **Costes del research** | 5 puntos básicos por lado |

Una vela verde se define como:

```text
Close > Open
```

---

## 🗂️ Estructura

```text
├── codigo/
│   └── TIS_RSI2_MeanReversion.mq5
│
├── data/
│   └── QQQ_D1.csv
│
├── motor/
│   └── rsi2_motor.py
│
├── resultados/
│   ├── metricas.json
│   ├── trades.csv
│   ├── equity_diaria.csv
│   ├── equity_semanal.json
│   └── graficos/
│
├── descargar_datos.py
├── requirements.txt
└── README.md
```

### `motor/rsi2_motor.py`

Motor de backtest y validación de la estrategia.

### `resultados/trades.csv`

Operaciones generadas por el sistema, una a una.

### `resultados/metricas.json`

Métricas y resultados de las pruebas de validación.

### `resultados/graficos/`

Visualizaciones del backtest, robustez, Monte Carlo, walk-forward, drawdowns y otras pruebas del research.

### `codigo/TIS_RSI2_MeanReversion.mq5`

Implementación de la estrategia para MetaTrader 5, incluyendo la capa de gestión de riesgo y ejecución.

---

## 📌 Alcance

El backtest de referencia utiliza datos diarios de QQQ.

El motor modela **5 bps de coste por lado**. La ejecución puede variar por instrumento, spread, comisiones, swaps, horarios, liquidez y condiciones del bróker.

Este repositorio tiene fines educativos y de investigación.

Los resultados pasados no garantizan resultados futuros y este material no constituye asesoría financiera.

---

**Trade It Simple · Systematic Trading Research**
