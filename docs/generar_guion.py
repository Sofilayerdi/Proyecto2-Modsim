"""Exporta docs/presentacion/guion.md a HTML y PDF, sin red."""

from pathlib import Path

from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
CSS = """
body{margin:0;color:#19313b;font:15px/1.6 Georgia,serif;background:white}
main{max-width:820px;margin:32px auto;padding:0 40px}
h1{font:700 30px/1.2 Arial,sans-serif;color:#16313b;border-bottom:4px solid #187a7c;padding-bottom:12px}
h2{font:700 20px/1.3 Arial,sans-serif;color:#187a7c;margin-top:34px;border-top:2px solid #187a7c;padding-top:12px}
h3{font:700 15px/1.3 Arial,sans-serif;color:#16313b;margin:22px 0 6px}
table{border-collapse:collapse;width:100%;font:12px/1.4 Arial,sans-serif;margin:14px 0}
th,td{padding:7px 8px;border-bottom:1px solid #d8e3e6;text-align:left}th{background:#eaf5f4}
p{margin:6px 0 10px}em{color:#526b75}
@media print{@page{size:A4;margin:16mm}main{margin:0;padding:0;max-width:none}
h2{break-before:page;margin-top:0}h2:first-of-type{break-before:auto}h3,h3+p{break-after:avoid}p{orphans:3;widows:3}}
"""


def generar():
    fuente = RAIZ / "docs/presentacion/guion.md"
    texto = fuente.read_text(encoding="utf-8")
    # Las indicaciones entre corchetes se muestran en cursiva para no leerlas en voz alta.
    lineas = [f"*{l}*" if l.startswith("[") and l.endswith("]") else l for l in texto.splitlines()]
    cuerpo = MarkdownIt("commonmark").enable("table").render("\n".join(lineas))
    html = fuente.with_suffix(".html")
    html.write_text('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Guion de presentación</title>'
                    f'<style>{CSS}</style></head><body><main>{cuerpo}</main></body></html>', encoding="utf-8")
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(html.as_uri(), wait_until="networkidle")
        pagina.pdf(path=str(fuente.with_suffix(".pdf")), format="A4", print_background=True,
                   display_header_footer=True, header_template="<span></span>",
                   footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#526b75">'
                                   'UVG · Modelación y Simulación · Guion de presentación · '
                                   '<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                   margin={"top": "16mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
        navegador.close()
    print(fuente.with_suffix(".pdf"))


if __name__ == "__main__":
    generar()
