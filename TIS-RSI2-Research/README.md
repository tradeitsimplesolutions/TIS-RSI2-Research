# RSI(2) Mean Reversion — Trade It Simple

Research reproducible de una estrategia de reversión a la media de corto plazo sobre el Nasdaq 100, desarrollada a partir del trabajo de Larry Connors y Cesar Alvarez sobre RSI de 2 períodos.

Este repositorio contiene los datos utilizados, las reglas de la estrategia, el motor de backtest en Python, los resultados del research y el código de ejecución para MetaTrader 5.

> La estrategia no es el premio. El premio es aprender a construir, validar y entender un sistema.

---

## 🧠 Hipótesis

La estrategia busca capturar reversiones de corto plazo después de episodios de sobreventa dentro de una tendencia alcista de largo plazo.

El RSI(2) detecta estrés de muy corto plazo y la SMA(200) funciona como filtro de tendencia.

---

## 📐 Reglas

| | |
|---|---|
| **Activo de referencia** | QQQ / Nasdaq 100 |
| **Timeframe** | Diario |
| **Dirección** | Solo largos |
| **Filtro** | Cierre > SMA(200) |
| **Entrada** | RSI(2) < 15 al cierre → entrada en la apertura siguiente |
| **Salida** | Dos velas verdes consecutivas → salida en la apertura siguiente |
| **Costes del research** | 5 puntos básicos por lado |

Una vela verde se define como `Close > Open`.

---

## 🚀 Reproducir el research

Instala las dependencias:

```bash
pip install -r requirements.txt