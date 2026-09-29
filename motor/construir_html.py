"""
Construye las dos páginas de la guía a partir de resultados/metricas.json y resultados/graficos/*.png:
  guia/rsi2-ficha.html        → la estrategia explicada de principio a fin (para el alumno)
  guia/rsi2-validacion.html   → manual avanzado: evolución, método TIS con las fases, robustez, drawdowns, glosario
Uso: python motor/construir_html.py
"""
from comun import GUIA
from pagina_ficha import ficha
from pagina_manual import manual

if __name__ == "__main__":
    GUIA.mkdir(exist_ok=True)
    (GUIA / "rsi2-ficha.html").write_text(ficha(), encoding="utf-8")
    (GUIA / "rsi2-validacion.html").write_text(manual(), encoding="utf-8")
    for p in GUIA.glob("rsi2-*.html"):
        print(f"{p.name}: {p.stat().st_size/1024:.0f} KB")
