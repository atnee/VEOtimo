import json
from pathlib import Path

import pytest

from veotimo.powerflow import load_network, run_power_flow
from veotimo.powerflow.radial import NetworkError


NETWORK = Path(__file__).parents[1] / "data" / "networks" / "ieee33.json"


def test_ieee33_contract_and_reference_totals() -> None:
    network = load_network(NETWORK)
    assert len(network["buses"]) == 33
    assert len(network["branches"]) == 32
    assert sum(bus["p_kw"] for bus in network["buses"]) == 3715
    assert sum(bus["q_kvar"] for bus in network["buses"]) == 2300


def test_ieee33_base_case_matches_published_benchmark() -> None:
    result = run_power_flow(load_network(NETWORK))
    assert result.converged
    assert result.min_voltage_bus == 18
    assert result.bus_voltage_pu[18] == pytest.approx(0.9131, abs=1e-4)
    assert result.active_losses_kw == pytest.approx(202.68, abs=0.1)
    assert result.reactive_losses_kvar == pytest.approx(135.14, abs=0.1)


def test_ev_load_scenario_reduces_voltage_and_increases_losses() -> None:
    network = load_network(NETWORK)
    base = run_power_flow(network)
    with_ev = run_power_flow(network, scenario={18: (120.0, 40.0)})
    assert with_ev.bus_voltage_pu[18] < base.bus_voltage_pu[18]
    assert with_ev.active_losses_kw > base.active_losses_kw


def test_rejects_non_radial_contract(tmp_path: Path) -> None:
    network = json.loads(NETWORK.read_text(encoding="utf-8"))
    network["branches"].append({"from": 1, "to": 33, "r_ohm": 1, "x_ohm": 1})
    invalid = tmp_path / "meshed.json"
    invalid.write_text(json.dumps(network), encoding="utf-8")
    with pytest.raises(NetworkError, match="n-1"):
        load_network(invalid)
