"""Exporta el informe maestro y la presentación general a HTML/PDF, sin red."""

import argparse
from html import escape
import hashlib
import json
from pathlib import Path
import re

from latex2mathml.converter import convert
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from playwright.sync_api import sync_playwright

from graficas_presentacion import generar_figuras

RAIZ = Path(__file__).resolve().parents[1]

CSS = """
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#e9eff1;
color:#19313b;font:16px/1.62 Georgia,serif}main{max-width:1000px;margin:36px auto;
padding:68px 76px;background:white;box-shadow:0 12px 60px #18333b14}
.cover{min-height:620px;display:flex;flex-direction:column;justify-content:center;
border-top:9px solid #187a7c;border-bottom:1px solid #c5d8dc;margin-bottom:36px}
.cover h1{font:700 54px/1.12 Arial,sans-serif;letter-spacing:-2px;margin:30px 0}
.cover .eyebrow{color:#187a7c;letter-spacing:2px;font:700 12px Arial,sans-serif}
.cover p{max-width:650px;color:#526b75}.cover .tag{color:#975d16;font-weight:bold}
.cover .institution{font:700 19px/1.5 Arial,sans-serif;color:#183b45;margin-top:22px}
.cover .members{font:15px/1.7 Arial,sans-serif;color:#2d515c;padding-left:0;list-style:none}
.cover .members li{margin:3px 0}.cover .date{font:14px/1.5 Arial,sans-serif;margin-top:22px}
h2,h3{font-family:Arial,sans-serif;line-height:1.25;color:#16313b}
h2{font-size:29px;border-top:3px solid #187a7c;padding-top:18px;margin-top:50px}
h3{font-size:19px;margin-top:28px}p,li{orphans:3;widows:3}
a{color:#146b78;text-decoration:none;overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;table-layout:fixed;font:12px/1.4 Arial,sans-serif;
margin:20px 0}th,td{padding:9px 7px;vertical-align:top;border-bottom:1px solid #d8e3e6;
overflow-wrap:anywhere}th{background:#eaf5f4;color:#16474b;text-align:left}
tr:nth-child(even) td{background:#f6f9fa}thead{display:table-header-group}tr{break-inside:avoid}
img{display:block;max-width:100%;height:auto;margin:20px auto;break-inside:avoid}
pre{padding:15px;background:#f0f5f6;white-space:pre-wrap;overflow-wrap:anywhere;
font:12px/1.5 monospace;border-left:3px solid #187a7c}code{font-size:.87em}
blockquote{margin:16px 0;padding:6px 20px;border-left:3px solid #c88d39;color:#526b75}
.math-block{text-align:center;max-width:100%;font-size:.92em;margin:24px 0;break-inside:avoid}
.toc{padding:20px;background:#eff7f7;display:grid;grid-template-columns:1fr 1fr;gap:8px;
font:14px/1.5 Arial,sans-serif}.toc strong{grid-column:1/-1}
@media print{@page{size:A4}body{background:white;font-size:10.5pt;line-height:1.5}
main{padding:0;margin:0;max-width:none;box-shadow:none}.cover{min-height:220mm;break-after:page}
.cover h1{font-size:40pt}.cover .eyebrow{font-size:10pt}
h2{break-before:auto;font-size:20pt;margin-top:26px;padding-top:12px;break-after:avoid}
h2:nth-of-type(5),h2:nth-of-type(7),h2:nth-of-type(10),h2:nth-of-type(13){break-before:page;margin-top:0}
h3{font-size:13pt;break-after:avoid}table{font-size:8.3pt}th,td{padding:6px 5px}
pre{font-size:8pt}img{max-height:205mm;object-fit:contain}.toc{font-size:10pt}
a{color:#185a66}h2,h3{break-inside:avoid}.math-block{font-size:.9em}}
"""


def html_informe():
    fuente = RAIZ / "docs/informe/informe.md"
    proyecto = json.loads((RAIZ / "docs/proyecto.json").read_text(encoding="utf-8"))
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    md.use(dollarmath_plugin).use(anchors_plugin, min_level=2, max_level=3)

    def inline(tokens, i, options, env):
        return convert(tokens[i].content, display="inline")

    def bloque(tokens, i, options, env):
        return '<div class="math-block">' + convert(tokens[i].content, display="block") + '</div>\n'

    md.renderer.rules["math_inline"] = inline
    md.renderer.rules["math_block"] = bloque
    texto = fuente.read_text(encoding="utf-8")
    marcador = "**Alcance de cierre:**"
    if marcador not in texto:
        raise ValueError("El informe debe identificar su alcance antes del resumen")
    contenido = md.render(texto[texto.index(marcador):])
    secciones = re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', contenido)
    indice = '<nav class="toc"><strong>Contenido</strong>' + ''.join(
        f'<a href="#{escape(id_)}">{escape(titulo)}</a>' for id_, titulo in secciones
    ) + '</nav>'
    miembros = ''.join(f'<li>{escape(p["nombre"])} — <strong>{escape(p["carne"])}</strong></li>'
                       for p in proyecto["integrantes"])
    portada = f'''<header class="cover"><span class="eyebrow">PROYECTO 2 · INFORME TÉCNICO</span>
<p class="institution">{escape(proyecto["universidad"])}<br>{escape(proyecto["facultad"])}</p>
<p>{escape(proyecto["curso"])}</p>
<h1>Traspasos de inventario<br>entre tiendas</h1>
<ul class="members">{miembros}</ul>
<p class="date">{escape(proyecto["lugar_fecha"])}</p>
<p class="tag">Estudio sintético y contraste externo con ventas M5.</p></header>'''
    destino = fuente.with_suffix(".html")
    destino.write_text('<!doctype html><html lang="es"><head><meta charset="utf-8">'
                        '<meta name="viewport" content="width=device-width,initial-scale=1">'
                        '<title>Informe · Traspasos de inventario</title><style>' + CSS +
                        '</style></head><body><main>' + portada + indice + contenido +
                        '</main></body></html>', encoding="utf-8")
    return destino


def generar():
    figuras = generar_figuras(RAIZ)
    informe = html_informe()
    presentacion = RAIZ / "docs/presentacion/presentacion.html"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        pagina = browser.new_page(viewport={"width": 1280, "height": 900})
        pagina.route("https://**/*", lambda ruta: ruta.abort())
        pagina.goto(informe.as_uri(), wait_until="networkidle")
        pagina.evaluate("document.fonts.ready")
        rotas = pagina.locator("img").evaluate_all("xs=>xs.filter(x=>!x.complete||!x.naturalWidth).map(x=>x.src)")
        if rotas:
            raise RuntimeError(f"Imágenes no disponibles: {rotas}")
        pagina.set_viewport_size({"width": 673, "height": 950})
        pagina.emulate_media(media="print")
        pagina.evaluate('''() => document.querySelectorAll('.math-block math').forEach(m => {
          const max=m.parentElement.clientWidth, w=m.getBoundingClientRect().width;
          if(w>max) m.style.fontSize=(max/w*100)+'%';
        })''')
        pagina.pdf(path=str(informe.with_suffix(".pdf")), format="A4", print_background=True,
                   display_header_footer=True,
                   header_template='<div style="font-size:8px;width:100%;text-align:center;color:#526b75">Universidad del Valle de Guatemala · Facultad de Ingeniería · Modelación y Simulación</div>',
                   footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#526b75"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
                   margin={"top": "17mm", "right": "16mm", "bottom": "17mm", "left": "16mm"})
        pagina.goto(presentacion.as_uri(), wait_until="networkidle")
        datos = pagina.locator("section.slide").evaluate_all(
            "xs=>({diapositivas:xs.length,segundos:xs.reduce((a,x)=>a+Number(x.dataset.segundos),0),apartados:[...new Set(xs.flatMap(x=>(x.dataset.apartados||'').split('|').filter(Boolean)))]})")
        apartados = ["Problema", "Objetivos", "Fuentes", "Técnica investigada", "Modelo", "Implementación",
                     "Diseño experimental", "Validación", "Comparación real", "Resultados", "Limitaciones",
                     "Conclusiones", "Referencias", "Contribuciones"]
        if datos["diapositivas"] != 24 or datos["segundos"] != 900 or set(datos["apartados"]) != set(apartados):
            raise RuntimeError(f"Estructura de presentación inesperada: {datos}")
        if pagina.locator("img").evaluate_all("xs=>xs.some(x=>!x.complete||!x.naturalWidth)"):
            raise RuntimeError("La presentación tiene imágenes rotas")
        pagina.pdf(path=str(presentacion.with_suffix(".pdf")), print_background=True,
                   prefer_css_page_size=True, display_header_footer=False,
                   margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
    archivos = [RAIZ / "docs/informe/informe.md", informe, informe.with_suffix(".pdf"),
                presentacion, presentacion.with_suffix(".pdf"), Path(__file__),
                RAIZ / "docs/graficas_presentacion.py", RAIZ / "docs/proyecto.json", *figuras]
    registro = {"fuente_maestra": "docs/informe/informe.md", **datos,
                "archivos_sha256": {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in archivos},
                "dependencias_documentales": "docs/requirements.txt",
                "alcance": "Estudio sintético y contraste externo parcial M5; no validación operativa"}
    (RAIZ / "docs/entregables.json").write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"informe": str(informe.with_suffix(".pdf")),
                      "presentacion": str(presentacion.with_suffix(".pdf")), **datos}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    generar()
