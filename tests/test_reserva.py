import pytest

from experiments import reserva
from src.simulation.carga import cargar_config


@pytest.fixture
def config():
    return cargar_config("config.yaml")


@pytest.mark.parametrize("dias", reserva.NIVELES)
def test_niveles_validos_y_proporcionales(config, dias):
    nuevo = reserva.config_nivel(config, dias)
    tiendas = nuevo["reposicion"]["tiendas"]
    assert tiendas["dias_objetivo"] == dias
    assert tiendas["dias_seguridad"] == pytest.approx(3 * dias / 12)
    assert tiendas["tiempo_entrega_dias"] + tiendas["dias_seguridad"] <= dias
    assert nuevo["inventario"]["inicial"]["dias_cobertura_tienda"] <= dias
    assert nuevo["reposicion"]["bodega"] == config["reposicion"]["bodega"]
    assert config["reposicion"]["tiendas"]["dias_objetivo"] == 12  # no muta el original


def test_nivel_base_reproduce_config(config):
    assert reserva.config_nivel(config, 12) == config


def test_simulador_ignora_genes_de_bodega(monkeypatch, config):
    recibidos = []
    monkeypatch.setattr(reserva, "simular_politica",
                        lambda cfg, params, semilla: recibidos.append(params) or {})
    reserva.simular_traspasos_bodega_fija(config, {"bodega_s_dias": 5, "bodega_S_dias": 15,
                                                   "umbral_valor_q": 10.0}, 1)
    assert recibidos == [{"umbral_valor_q": 10.0}]


def test_replica_sin_traspasos_reporta_indicadores(config):
    nuevo = reserva.config_nivel(config, 6)
    nuevo["simulacion"]["horizonte_dias"] = 30
    ganador = {"horizonte_dias_alta": 3, "seguridad_dias_alta": 2, "horizonte_dias_media": 3,
               "seguridad_dias_media": 2, "horizonte_dias_baja": 3, "seguridad_dias_baja": 2}
    fila = reserva._replica(("S", 6, "sin", nuevo, ganador, 1001))
    assert fila["condicion"] == "S6_sin" and fila["num_traspasos"] == 0
    assert 0 <= fila["fraccion_dias_agotado"] <= 1
    assert 0 <= fila["eventos_con_donante"] <= fila["eventos_faltante"]


@pytest.mark.parametrize("dias", reserva.NIVELES_ENTREGA)
def test_entrega_conserva_seguridad_y_tamano_pedido(config, dias):
    nuevo = reserva.config_entrega(config, dias)
    tiendas, base = nuevo["reposicion"]["tiendas"], config["reposicion"]["tiendas"]
    assert tiendas["tiempo_entrega_dias"] == dias
    assert tiendas["dias_seguridad"] == base["dias_seguridad"]
    assert tiendas["dias_objetivo"] - dias == base["dias_objetivo"] - base["tiempo_entrega_dias"]
    assert nuevo["reposicion"]["bodega"] == config["reposicion"]["bodega"]


def test_entrega_base_reproduce_config(config):
    assert reserva.config_entrega(config, 2) == config
