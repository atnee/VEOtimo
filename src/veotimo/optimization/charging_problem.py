"""Problema integrado mínimo de alocação de recarga e avaliação elétrica."""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import acos, tan
from pathlib import Path
from typing import Any

from veotimo.powerflow import load_network, run_power_flow


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    bus: int
    connection_cost: float


@dataclass(frozen=True)
class Evaluation:
    objective: float
    feasible: bool
    charger_counts: tuple[int, ...]
    selected_stations: tuple[str, ...]
    installed_kw: float
    served_kw: float
    unserved_kw: float
    station_capex: float
    charger_capex: float
    connection_capex: float
    incremental_loss_cost: float
    penalty_cost: float
    minimum_voltage_pu: float
    minimum_voltage_bus: int
    active_losses_kw: float
    voltage_violation_pu: float


class ChargingAllocationProblem:
    """Avalia decisões inteiras de carregadores nos candidatos.

    A demanda agregada é distribuída proporcionalmente à potência instalada. A
    simultaneidade, custos e candidatos deste benchmark são sintéticos e ficam
    fora do código. A avaliação elétrica usa fluxo AC radial a cada solução.
    """

    def __init__(self, case: dict[str, Any], root: Path) -> None:
        self.case = case
        self.network = load_network(root / case["network_path"])
        self.candidates = tuple(
            Candidate(item["id"], int(item["bus"]), float(item["connection_cost"]))
            for item in case["candidates"]
        )
        self.dimension = len(self.candidates)
        self.demand_kw = float(case["demand_kw"])
        self.power_factor = float(case["power_factor"])
        self.charger_kw = float(case["charger"]["power_kw"])
        self.charger_capex = float(case["charger"]["capex"])
        self.annualization = float(case["charger"]["annualization_factor"])
        self.constraints = case["constraints"]
        self.economics = case["economics"]
        self.max_count = int(self.constraints["max_chargers_per_station"])
        self._base_flow = run_power_flow(
            self.network,
            voltage_min_pu=float(self.constraints["voltage_min_pu"]),
            voltage_max_pu=float(self.constraints["voltage_max_pu"]),
        )
        self._cache: dict[tuple[int, ...], Evaluation] = {}

    def repair(self, vector: tuple[int, ...]) -> tuple[int, ...]:
        """Projeta contagens no domínio e respeita o máximo de estações."""
        values = [min(self.max_count, max(0, int(round(value)))) for value in vector]
        max_stations = int(self.constraints["max_stations"])
        active = [index for index, count in enumerate(values) if count > 0]
        if len(active) > max_stations:
            keep = set(sorted(active, key=lambda index: (-values[index], index))[:max_stations])
            values = [count if index in keep else 0 for index, count in enumerate(values)]
        return tuple(values)

    def evaluate(self, vector: tuple[int, ...]) -> Evaluation:
        counts = self.repair(vector)
        if counts in self._cache:
            return self._cache[counts]
        installed_kw = sum(counts) * self.charger_kw
        served_kw = min(installed_kw, self.demand_kw)
        unserved_kw = self.demand_kw - served_kw
        utilization = served_kw / installed_kw if installed_kw else 0.0
        q_ratio = tan(acos(self.power_factor))
        scenario = {
            candidate.bus: (count * self.charger_kw * utilization,
                            count * self.charger_kw * utilization * q_ratio)
            for candidate, count in zip(self.candidates, counts)
            if count
        }
        flow = run_power_flow(
            self.network,
            scenario,
            voltage_min_pu=float(self.constraints["voltage_min_pu"]),
            voltage_max_pu=float(self.constraints["voltage_max_pu"]),
        )
        selected = tuple(
            candidate.candidate_id
            for candidate, count in zip(self.candidates, counts)
            if count > 0
        )
        station_capex = len(selected) * float(self.economics["station_fixed_cost"])
        charger_capex = sum(counts) * self.charger_capex
        connection_capex = sum(
            candidate.connection_cost
            for candidate, count in zip(self.candidates, counts)
            if count > 0
        )
        incremental_losses = max(0.0, flow.active_losses_kw - self._base_flow.active_losses_kw)
        loss_cost = (
            incremental_losses
            * float(self.economics["annual_peak_equivalent_hours"])
            * float(self.economics["energy_price_per_kwh"])
        )
        voltage_min = float(self.constraints["voltage_min_pu"])
        voltage_max = float(self.constraints["voltage_max_pu"])
        voltage_violation = sum(
            max(0.0, voltage_min - value, value - voltage_max)
            for value in flow.bus_voltage_pu.values()
        )
        penalty = (
            unserved_kw * float(self.economics["unserved_penalty_per_kw"])
            + voltage_violation * float(self.economics["voltage_penalty_per_pu"])
        )
        annualized_capex = self.annualization * (
            station_capex + charger_capex + connection_capex
        )
        minimum_served = float(self.constraints["minimum_served_fraction"])
        feasible = (
            flow.converged
            and served_kw + 1e-9 >= minimum_served * self.demand_kw
            and voltage_violation <= 1e-9
        )
        evaluation = Evaluation(
            objective=annualized_capex + loss_cost + penalty,
            feasible=feasible,
            charger_counts=counts,
            selected_stations=selected,
            installed_kw=installed_kw,
            served_kw=served_kw,
            unserved_kw=unserved_kw,
            station_capex=station_capex,
            charger_capex=charger_capex,
            connection_capex=connection_capex,
            incremental_loss_cost=loss_cost,
            penalty_cost=penalty,
            minimum_voltage_pu=min(flow.bus_voltage_pu.values()),
            minimum_voltage_bus=flow.min_voltage_bus,
            active_losses_kw=flow.active_losses_kw,
            voltage_violation_pu=voltage_violation,
        )
        self._cache[counts] = evaluation
        return evaluation


def load_problem(path: str | Path, root: str | Path | None = None) -> ChargingAllocationProblem:
    case_path = Path(path)
    with case_path.open(encoding="utf-8") as stream:
        case = json.load(stream)
    project_root = Path(root) if root is not None else case_path.resolve().parents[2]
    return ChargingAllocationProblem(case, project_root)
