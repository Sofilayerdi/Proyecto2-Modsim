from copy import deepcopy

import pytest

from experiments import demo


def test_comparacion_usa_semilla_comun_y_no_modifica_config(monkeypatch):
    config = {"simulacion": {"horizonte_dias": 120}}
    original = deepcopy(config)
    calls = []

    def base(cfg, params, seed):
        calls.append((cfg["simulacion"]["horizonte_dias"], params, seed))
        return {"costo_total": 100, "nivel_servicio": .9}

    def mejorada(cfg, params, seed):
        calls.append((cfg["simulacion"]["horizonte_dias"], params, seed))
        return {"costo_total": 80, "nivel_servicio": .95}

    monkeypatch.setattr(demo, "simular", base)
    monkeypatch.setattr(demo, "simular_politica", mejorada)
    result = demo.comparar(config, {"gen": 1}, semilla=42, dias=15)
    assert config == original
    assert calls == [(15, None, 42), (15, {"gen": 1}, 42)]
    assert result["diferencia_costo"] == -20
    assert result["diferencia_servicio_pp"] == pytest.approx(5)
    with pytest.raises(ValueError):
        demo.comparar(config, {}, dias=0)
