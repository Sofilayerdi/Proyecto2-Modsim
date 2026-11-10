"""Demostración visual: escenario base contra política optimizada en una réplica sintética."""
import argparse
import json
import sys
import time
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import ttk

import numpy as np
import yaml

from experiments.escenarios import construir_escenarios
from src.model.traspasos import decidir_traspasos
from src.simulation.carga import cargar_config, cargar_datos
from src.simulation.motor import simular

RAIZ = Path(__file__).resolve().parents[1]

SUPERFICIE = "#fcfcfb"
PANEL = "#f3f2ef"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
REJILLA = "#e6e5e1"
EJE = "#c9c8c3"

SERIES = {
    "base": ("Base", "#2a78d6", "-"),
    "mejorada": ("Mejorada", "#eb6834", "-"),
    "control": ("Solo bodega ajustada", "#1baf7a", "--"),
}

ESCENARIOS = {
    "Nominal": None,
    "Demanda +20 %": "demanda_mas_20",
    "Tráfico pesado (×2)": "trafico_pesado",
    "Un vehículo": "un_vehiculo",
}

FILAS = [
    ("Costo total (Q)", "costo_total", "q"),
    ("   Inventario (Q)", "costo_inventario", "q"),
    ("   Traslados (Q)", "costo_traslado", "q"),
    ("   Ventas perdidas (Q)", "costo_ventas_perdidas", "q"),
    ("Nivel de servicio", "nivel_servicio", "pct"),
    ("Unidades perdidas", "unidades_perdidas", "n"),
    ("Viajes de traspaso", "num_traspasos", "n"),
    ("Km recorridos", "km_recorridos", "km"),
]


def formato(valor, tipo):
    if tipo == "q":
        return f"Q{valor:,.0f}"
    if tipo == "pct":
        return f"{100 * valor:.2f} %"
    if tipo == "km":
        return f"{valor:,.1f}"
    return f"{valor:,.0f}"


def diferencia(nuevo, base, tipo):
    d = nuevo - base
    if tipo == "pct":
        return f"{100 * d:+.2f} pp"
    texto = f"{d:+,.0f}" if tipo != "km" else f"{d:+,.1f}"
    if tipo == "q" and base:
        texto += f"  ({100 * d / base:+.1f} %)"
    return texto


def preparar_escenarios(config, ganador, diseno):
    condiciones = {c["condicion"]: c["config"] for c in construir_escenarios(config, ganador, diseno)}
    return {nombre: condiciones[clave] if clave else condiciones["base"] for nombre, clave in ESCENARIOS.items()}


def correr(config_escenario, ganador, semilla, dias, con_control):
    """Simula base, mejorada y (opcional) el control con la misma semilla."""
    config = deepcopy(config_escenario)
    config["simulacion"]["horizonte_dias"] = dias
    resultados = {
        "base": simular(config, None, semilla, detalle=True),
        "mejorada": simular(config, ganador, semilla, detalle=True, decidir=decidir_traspasos),
    }
    if con_control:
        ajustada = deepcopy(config)
        ajustada["reposicion"]["bodega"].update(s_dias=ganador["bodega_s_dias"], S_dias=ganador["bodega_S_dias"])
        resultados["control"] = simular(ajustada, None, semilla, detalle=True)
    return resultados


def serie(detalle, clave, tienda, producto):
    datos = detalle[clave]
    if tienda is not None:
        datos = datos[:, [tienda], :]
    if producto is not None:
        datos = datos[:, :, [producto]]
    return datos.sum(axis=(1, 2))


class Demo:
    def __init__(self, raiz, config, ganador, diseno):
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.raiz = raiz
        self.ganador = ganador
        self.escenarios = preparar_escenarios(config, ganador, diseno)
        datos = cargar_datos(config)
        self.ids_tiendas = datos["ids_tiendas"]
        self.ids_productos = datos["ids_productos"]
        self.resultados = None

        raiz.title("Demo · Traspasos de inventario entre tiendas")
        raiz.configure(bg=SUPERFICIE)
        raiz.geometry("1360x860")
        raiz.minsize(1180, 700)
        try:
            raiz.state("zoomed")
        except tk.TclError:
            pass
        self._estilos()

        encabezado = tk.Frame(raiz, bg=SUPERFICIE)
        encabezado.pack(fill="x", padx=24, pady=(18, 6))
        tk.Label(encabezado, text="Traspasos de inventario entre tiendas", font=("Segoe UI Semibold", 20),
                 fg=TEXTO, bg=SUPERFICIE).pack(anchor="w")
        tk.Label(encabezado, text="Una réplica de la simulación: escenario base contra la política optimizada "
                 "por el algoritmo genético, con exactamente la misma demanda.",
                 font=("Segoe UI", 11), fg=TEXTO_2, bg=SUPERFICIE).pack(anchor="w")

        self.estado = tk.Label(raiz, text="", font=("Segoe UI", 9), fg=TEXTO_2, bg=PANEL, anchor="w", padx=24, pady=6)
        self.estado.pack(fill="x", side="bottom")

        cuerpo = tk.Frame(raiz, bg=SUPERFICIE)
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(6, 0))
        self._panel_controles(cuerpo)

        derecha = tk.Frame(cuerpo, bg=SUPERFICIE)
        derecha.pack(side="left", fill="both", expand=True, padx=(18, 0))

        self.marco_tarjetas = tk.Frame(derecha, bg=SUPERFICIE)
        self.marco_tarjetas.pack(fill="x")

        pestanas = ttk.Notebook(derecha)
        pestanas.pack(side="bottom", fill="x", pady=(4, 8))

        self.figura = Figure(figsize=(10, 3), dpi=100, facecolor=SUPERFICIE)
        self.lienzo = FigureCanvasTkAgg(self.figura, master=derecha)
        self.lienzo.get_tk_widget().pack(fill="both", expand=True, pady=(10, 4))
        self.lienzo.mpl_connect("motion_notify_event", self._al_mover)
        self.tabla = self._tabla(pestanas, ("metrica", "base", "mejorada", "control", "dif"),
                                 ("Métrica", "Base", "Mejorada", "Solo bodega ajustada", "Mejorada − base"),
                                 (210, 130, 130, 170, 190), filas=8)
        pestanas.add(self.tabla.master, text="  Resumen  ")
        self.tabla_traspasos = self._tabla(pestanas, ("llega", "origen", "destino", "producto", "cantidad", "costo", "km"),
                                           ("Llega el día", "Origen", "Destino", "Producto", "Unidades", "Costo (Q)", "Km"),
                                           (110, 110, 110, 110, 100, 110, 90), filas=8)
        pestanas.add(self.tabla_traspasos.master, text="  Traspasos de la mejorada  ")

        self.simular()

    def _estilos(self):
        estilo = ttk.Style(self.raiz)
        estilo.theme_use("clam")
        estilo.configure(".", font=("Segoe UI", 10), background=SUPERFICIE, foreground=TEXTO)
        estilo.configure("Treeview", rowheight=24, background="white", fieldbackground="white", bordercolor=EJE)
        estilo.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background=PANEL, foreground=TEXTO)
        estilo.configure("TNotebook", background=SUPERFICIE, borderwidth=0)
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(10, 4))
        estilo.configure("Accion.TButton", font=("Segoe UI Semibold", 11), padding=(10, 8),
                         background="#2a78d6", foreground="white")
        estilo.map("Accion.TButton", background=[("active", "#1f63b5")])
        estilo.configure("TCheckbutton", background=PANEL)
        estilo.configure("TLabel", background=PANEL)

    def _panel_controles(self, padre):
        panel = tk.Frame(padre, bg=PANEL, padx=18, pady=16)
        panel.pack(side="left", fill="y")

        def etiqueta(texto):
            tk.Label(panel, text=texto, font=("Segoe UI Semibold", 10), fg=TEXTO, bg=PANEL).pack(anchor="w", pady=(12, 3))

        tk.Label(panel, text="Parámetros de la réplica", font=("Segoe UI Semibold", 12), fg=TEXTO, bg=PANEL).pack(anchor="w")

        etiqueta("Semilla de demanda")
        self.semilla = tk.IntVar(value=1001)
        ttk.Spinbox(panel, from_=1, to=99999, textvariable=self.semilla, width=18).pack(anchor="w")

        etiqueta("Días simulados")
        self.dias = tk.IntVar(value=120)
        ttk.Spinbox(panel, from_=14, to=180, increment=1, textvariable=self.dias, width=18).pack(anchor="w")

        etiqueta("Escenario")
        self.escenario = tk.StringVar(value="Nominal")
        caja = ttk.Combobox(panel, textvariable=self.escenario, values=list(ESCENARIOS), state="readonly", width=20)
        caja.pack(anchor="w")
        caja.bind("<<ComboboxSelected>>", lambda _: self.simular())

        self.con_control = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Mostrar control:\nsolo bodega ajustada", variable=self.con_control,
                        command=self.simular).pack(anchor="w", pady=(14, 0))

        ttk.Button(panel, text="Simular", style="Accion.TButton", command=self.simular).pack(fill="x", pady=(18, 6))

        tk.Frame(panel, bg=EJE, height=1).pack(fill="x", pady=12)
        tk.Label(panel, text="Ver en las gráficas", font=("Segoe UI Semibold", 12), fg=TEXTO, bg=PANEL).pack(anchor="w")

        etiqueta("Tienda")
        self.tienda = tk.StringVar(value="Todas las tiendas")
        caja = ttk.Combobox(panel, textvariable=self.tienda, values=["Todas las tiendas"] + self.ids_tiendas,
                            state="readonly", width=20)
        caja.pack(anchor="w")
        caja.bind("<<ComboboxSelected>>", lambda _: self.dibujar())

        etiqueta("Producto")
        self.producto = tk.StringVar(value="Todos los productos")
        caja = ttk.Combobox(panel, textvariable=self.producto, values=["Todos los productos"] + self.ids_productos,
                            state="readonly", width=20)
        caja.pack(anchor="w")
        caja.bind("<<ComboboxSelected>>", lambda _: self.dibujar())

        tk.Label(panel, text="Una sola réplica sintética.\nLas conclusiones del estudio\nse basan en 30 réplicas.",
                 font=("Segoe UI", 9), fg=TEXTO_2, bg=PANEL, justify="left").pack(anchor="w", side="bottom")
        self.raiz.bind("<Return>", lambda _: self.simular())

    def _tabla(self, padre, columnas, titulos, anchos, filas):
        marco = tk.Frame(padre, bg=SUPERFICIE)
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=filas)
        for col, titulo, ancho in zip(columnas, titulos, anchos):
            tabla.heading(col, text=titulo)
            tabla.column(col, width=ancho, anchor="w" if col in ("metrica", "origen", "destino", "producto") else "e")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    def simular(self):
        try:
            semilla, dias = int(self.semilla.get()), int(self.dias.get())
        except (tk.TclError, ValueError):
            self.estado.config(text="La semilla y los días deben ser números enteros.")
            return
        if not 1 <= dias <= 365:
            self.estado.config(text="Los días deben estar entre 1 y 365.")
            return
        inicio = time.perf_counter()
        self.resultados = correr(self.escenarios[self.escenario.get()], self.ganador, semilla, dias,
                                 self.con_control.get())
        segundos = time.perf_counter() - inicio
        self.dibujar()
        self._llenar_tablas()
        self._tarjetas()
        self.estado.config(text=f"Semilla {semilla} · {dias} días · escenario {self.escenario.get()} · "
                                f"simulado en {segundos:.2f} s · base y mejorada enfrentan la misma demanda. "
                                "Pasa el cursor sobre las gráficas para ver los valores de cada día.")

    def _tarjetas(self):
        for hijo in self.marco_tarjetas.winfo_children():
            hijo.destroy()
        base = self.resultados["base"]
        for titulo, clave, tipo in (("Costo total", "costo_total", "q"), ("Nivel de servicio", "nivel_servicio", "pct"),
                                    ("Unidades perdidas", "unidades_perdidas", "n"), ("Viajes de traspaso", "num_traspasos", "n")):
            tarjeta = tk.Frame(self.marco_tarjetas, bg="white", highlightbackground=EJE, highlightthickness=1, padx=14, pady=10)
            tarjeta.pack(side="left", fill="both", expand=True, padx=(0, 10))
            tk.Label(tarjeta, text=titulo, font=("Segoe UI", 10), fg=TEXTO_2, bg="white").pack(anchor="w")
            for nombre, resultado in self.resultados.items():
                etiqueta, color, _ = SERIES[nombre]
                fila = tk.Frame(tarjeta, bg="white")
                fila.pack(anchor="w", fill="x")
                tk.Label(fila, text="■", font=("Segoe UI", 11), fg=color, bg="white").pack(side="left")
                tk.Label(fila, text=f" {etiqueta}", font=("Segoe UI", 10), fg=TEXTO_2, bg="white").pack(side="left")
                tk.Label(fila, text=formato(resultado[clave], tipo), font=("Segoe UI Semibold", 15),
                         fg=TEXTO, bg="white").pack(side="right")
            tk.Label(tarjeta, text=f"Mejorada − base: {diferencia(self.resultados['mejorada'][clave], base[clave], tipo)}",
                     font=("Segoe UI", 9), fg=TEXTO_2, bg="white").pack(anchor="w", pady=(4, 0))

    def _llenar_tablas(self):
        self.tabla.delete(*self.tabla.get_children())
        base, mejorada = self.resultados["base"], self.resultados["mejorada"]
        control = self.resultados.get("control")
        for titulo, clave, tipo in FILAS:
            self.tabla.insert("", "end", values=(
                titulo, formato(base[clave], tipo), formato(mejorada[clave], tipo),
                formato(control[clave], tipo) if control else "—", diferencia(mejorada[clave], base[clave], tipo)))

        self.tabla_traspasos.delete(*self.tabla_traspasos.get_children())
        traspasos = mejorada["detalle"]["traspasos"]
        if not traspasos:
            self.tabla_traspasos.insert("", "end", values=("—", "Sin traspasos en esta réplica", "", "", "", "", ""))
        for tr in sorted(traspasos, key=lambda t: t.dia_llegada):
            self.tabla_traspasos.insert("", "end", values=(
                tr.dia_llegada, self.ids_tiendas[tr.origen], self.ids_tiendas[tr.destino],
                self.ids_productos[tr.producto], tr.cantidad,
                f"{tr.costo:,.2f}" if tr.costo else "consolidado", f"{tr.km:,.1f}" if tr.km else "—"))

    def dibujar(self):
        from matplotlib import patheffects

        if self.resultados is None:
            return
        tienda = None if self.tienda.get() == "Todas las tiendas" else self.ids_tiendas.index(self.tienda.get())
        producto = None if self.producto.get() == "Todos los productos" else self.ids_productos.index(self.producto.get())
        lugar = self.tienda.get() if tienda is not None else "todas las tiendas"
        articulo = self.producto.get() if producto is not None else "todos los productos"

        self.figura.clear()
        ejes = self.figura.subplots(1, 2)
        titulos = ("Inventario al cierre del día", "Ventas perdidas acumuladas")
        unidades = ("Unidades al cierre", "Unidades perdidas")
        self.ejes, self.datos_ejes, self.guias, self.notas = list(ejes), [], [], []

        for eje, titulo, unidad, clave in zip(ejes, titulos, unidades, ("inventario_tiendas", "perdidas")):
            series = []
            for orden, (nombre, resultado) in enumerate(self.resultados.items()):
                etiqueta, color, trazo = SERIES[nombre]
                valores = serie(resultado["detalle"], clave, tienda, producto)
                if clave == "perdidas":
                    valores = np.cumsum(valores)
                eje.plot(np.arange(len(valores)), valores, color=color, linewidth=2, linestyle=trazo,
                         label=etiqueta, zorder=3 + orden,
                         path_effects=[patheffects.withStroke(linewidth=4, foreground=SUPERFICIE)] if orden else None)
                series.append((etiqueta, valores))
            self.datos_ejes.append(series)
            eje.set_title(titulo, loc="left", fontsize=10.5, color=TEXTO, pad=8)
            eje.set_xlabel("Día", fontsize=9, color=TEXTO_2)
            eje.set_ylabel(unidad, fontsize=9, color=TEXTO_2)
            eje.set_facecolor(SUPERFICIE)
            eje.grid(axis="y", color=REJILLA, linewidth=0.8)
            eje.set_axisbelow(True)
            eje.set_ylim(bottom=0)
            eje.set_xlim(0, len(series[0][1]) - 1)
            for lado in ("top", "right"):
                eje.spines[lado].set_visible(False)
            for lado in ("left", "bottom"):
                eje.spines[lado].set_color(EJE)
            eje.tick_params(colors=TEXTO_2, labelsize=8.5)
            self.guias.append(eje.axvline(0, color=TEXTO_2, linewidth=0.8, visible=False, zorder=10))
            self.notas.append(eje.annotate("", xy=(0.02, 0.97), xycoords="axes fraction", va="top", fontsize=8.5,
                                           color=TEXTO, zorder=11, visible=False,
                                           bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=EJE)))

        manijas, etiquetas = ejes[0].get_legend_handles_labels()
        self.figura.legend(manijas, etiquetas, loc="upper right", ncol=len(etiquetas), frameon=False, fontsize=9.5)
        self.figura.text(0.01, 0.975, f"Mostrando: {lugar} · {articulo}", va="top", fontsize=9.5, color=TEXTO_2)
        self.figura.tight_layout(rect=(0, 0, 1, 0.92))
        self.lienzo.draw_idle()

    def _al_mover(self, evento):
        if self.resultados is None or evento.inaxes not in self.ejes:
            if any(g.get_visible() for g in self.guias):
                for guia, nota in zip(self.guias, self.notas):
                    guia.set_visible(False)
                    nota.set_visible(False)
                self.lienzo.draw_idle()
            return
        largo = len(self.datos_ejes[0][0][1])
        dia = int(min(max(round(evento.xdata), 0), largo - 1))
        derecha = dia < largo * 0.55
        for guia, nota, series in zip(self.guias, self.notas, self.datos_ejes):
            guia.set_xdata([dia, dia])
            guia.set_visible(True)
            nota.set_text(f"Día {dia}\n" + "\n".join(f"{nombre}: {valores[dia]:,.0f}" for nombre, valores in series))
            nota.xy = (0.98, 0.97) if derecha else (0.02, 0.97)
            nota.set_ha("right" if derecha else "left")
            nota.set_visible(True)
        self.lienzo.draw_idle()


def capturar(raiz, ruta):
    from PIL import ImageGrab

    raiz.update()
    x, y = raiz.winfo_rootx(), raiz.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + raiz.winfo_width(), y + raiz.winfo_height())).save(ruta)
    raiz.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(RAIZ / "config.yaml"))
    parser.add_argument("--ganador", default=str(RAIZ / "results/optimizacion/semilla_20261109/ganador.json"))
    parser.add_argument("--diseno", default=str(RAIZ / "experiments/diseno.yaml"))
    parser.add_argument("--captura", help="guarda una captura de la ventana en esta ruta y cierra")
    args = parser.parse_args()

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass

    config = cargar_config(args.config)
    ganador = json.loads(Path(args.ganador).read_text(encoding="utf-8"))
    diseno = yaml.safe_load(Path(args.diseno).read_text(encoding="utf-8"))

    raiz = tk.Tk()
    Demo(raiz, config, ganador, diseno)
    if args.captura:
        raiz.after(2500, lambda: capturar(raiz, args.captura))
    raiz.mainloop()


if __name__ == "__main__":
    main()
