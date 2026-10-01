"""Fluxo de potência radial por varredura backward/forward.

O motor leve é destinado ao benchmark e a testes sem dependências externas. A
validação futura de estudos reais permanece atribuída ao motor AC pandapower.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class NetworkError(ValueError):
    """Indica dados elétricos estruturalmente inválidos."""


@dataclass(frozen=True)
class PowerFlowResult:
    converged: bool
    iterations: int
    bus_voltage_pu: dict[int, float]
    branch_current_pu: dict[tuple[int, int], float]
    active_losses_kw: float
    reactive_losses_kvar: float
    min_voltage_bus: int
    violations: tuple[str, ...]


def load_network(path: str | Path) -> dict[str, Any]:
    """Carrega o contrato JSON e valida que a topologia é uma árvore enraizada."""
    with Path(path).open(encoding="utf-8") as stream:
        network = json.load(stream)
    buses = {int(bus["id"]) for bus in network.get("buses", [])}
    branches = network.get("branches", [])
    slack = int(network.get("base", {}).get("slack_bus", -1))
    if slack not in buses:
        raise NetworkError("A barra slack não existe")
    if len(branches) != len(buses) - 1:
        raise NetworkError("O motor radial requer exatamente n-1 ramos")
    children: dict[int, list[int]] = {bus: [] for bus in buses}
    parents: dict[int, int] = {}
    for branch in branches:
        origin, destination = int(branch["from"]), int(branch["to"])
        if origin not in buses or destination not in buses:
            raise NetworkError("Ramo referencia barra inexistente")
        if destination in parents:
            raise NetworkError("Uma barra radial não pode ter dois pais")
        parents[destination] = origin
        children[origin].append(destination)
    visited, stack = set(), [slack]
    while stack:
        bus = stack.pop()
        if bus in visited:
            raise NetworkError("Ciclo detectado")
        visited.add(bus)
        stack.extend(children[bus])
    if visited != buses:
        raise NetworkError("A rede não é conexa a partir da slack")
    return network


def run_power_flow(
    network: dict[str, Any],
    scenario: dict[int, tuple[float, float]] | None = None,
    *,
    voltage_min_pu: float = 0.95,
    voltage_max_pu: float = 1.05,
    tolerance: float = 1e-10,
    max_iterations: int = 100,
) -> PowerFlowResult:
    """Executa fluxo AC balanceado de carga PQ constante em alimentador radial.

    ``scenario`` adiciona carga por barra como pares ``(kW, kvar)``. O método
    trabalha em pu e retorna perdas físicas; não é um fluxo DC/LinDistFlow.
    """
    buses = {int(bus["id"]): bus for bus in network["buses"]}
    base = network["base"]
    slack = int(base["slack_bus"])
    s_base_kva = float(base["power_mva"]) * 1000
    z_base_ohm = float(base["voltage_kv"]) ** 2 / float(base["power_mva"])
    branches = network["branches"]
    children: dict[int, list[int]] = {bus: [] for bus in buses}
    impedance: dict[tuple[int, int], complex] = {}
    for branch in branches:
        edge = (int(branch["from"]), int(branch["to"]))
        children[edge[0]].append(edge[1])
        impedance[edge] = complex(branch["r_ohm"], branch["x_ohm"]) / z_base_ohm

    order: list[int] = []
    stack = [slack]
    while stack:
        bus = stack.pop()
        order.append(bus)
        stack.extend(reversed(children[bus]))
    if len(order) != len(buses):
        raise NetworkError("Rede inválida; use load_network antes do fluxo")

    additions = scenario or {}
    load_pu = {}
    for bus_id, bus in buses.items():
        add_p, add_q = additions.get(bus_id, (0.0, 0.0))
        load_pu[bus_id] = complex(bus["p_kw"] + add_p, bus["q_kvar"] + add_q) / s_base_kva
    voltage = {bus: complex(base["slack_voltage_pu"]) for bus in buses}
    edge_current: dict[tuple[int, int], complex] = {}
    converged = False
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        injected = {
            bus: (load_pu[bus] / voltage[bus]).conjugate() for bus in buses if bus != slack
        }
        for bus in reversed(order[1:]):
            current = injected[bus] + sum(edge_current[(bus, child)] for child in children[bus])
            parent = next(origin for origin, destination in impedance if destination == bus)
            edge_current[(parent, bus)] = current
        updated = {slack: complex(base["slack_voltage_pu"])}
        for parent in order:
            for child in children[parent]:
                updated[child] = updated[parent] - impedance[(parent, child)] * edge_current[(parent, child)]
        mismatch = max(abs(updated[bus] - voltage[bus]) for bus in buses)
        voltage = updated
        if mismatch <= tolerance:
            converged = True
            break

    active_loss_pu = sum(abs(edge_current[edge]) ** 2 * impedance[edge].real for edge in impedance)
    reactive_loss_pu = sum(abs(edge_current[edge]) ** 2 * impedance[edge].imag for edge in impedance)
    magnitudes = {bus: abs(value) for bus, value in voltage.items()}
    violations = tuple(
        f"bus_{bus}:voltage_{value:.6f}_pu"
        for bus, value in magnitudes.items()
        if value < voltage_min_pu or value > voltage_max_pu
    )
    min_bus = min(magnitudes, key=magnitudes.get)
    return PowerFlowResult(
        converged=converged,
        iterations=iteration,
        bus_voltage_pu=magnitudes,
        branch_current_pu={edge: abs(value) for edge, value in edge_current.items()},
        active_losses_kw=active_loss_pu * s_base_kva,
        reactive_losses_kvar=reactive_loss_pu * s_base_kva,
        min_voltage_bus=min_bus,
        violations=violations,
    )
