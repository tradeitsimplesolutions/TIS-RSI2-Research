# Datos

`QQQ_D1.csv` no se versiona. Las cifras de la guía se generaron con **Norgate Data** (retorno total),
que no se puede redistribuir. Para reproducirlas:

```
python descargar_datos.py --norgate   # si tienes Norgate
python descargar_datos.py             # Yahoo Finance, gratuito: cifras muy parecidas, no idénticas
```

El contraste con los datos del bróker (CFD NDX de Darwinex) tampoco se redistribuye; el motor acepta
cualquier CSV diario con columnas `Date,Open,High,Low,Close`.
