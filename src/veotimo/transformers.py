"""Diagnóstico transparente e seleção discreta de transformadores."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Iterable


@dataclass(frozen=True)
class TransformerAssessment:
    transformer_id: str
    current_kva: float
    base_peak_kva: float
    ev_peak_kva: float
    total_peak_kva: float
    current_loading_percent: float
    ev_loading_percent: float
    current_margin_kva: float
    required_kva: float
    recommended_kva: float | None
    needs_upgrade: bool
    classification: str


def assess_transformer(
    transformer_id: str,
    current_kva: float,
    base_peak_kva: float,
    ev_peak_kva: float,
    loading_limit: float,
    catalog_kva: Iterable[float],
    near_limit_fraction: float = 0.90,
) -> TransformerAssessment:
    """Dimensiona pelo pico temporal já simultaneizado, nunca pela soma de placas."""
    if current_kva <= 0 or base_peak_kva < 0 or ev_peak_kva < 0:
        raise ValueError("Potências devem ser não negativas e a nominal deve ser positiva")
    if not 0 < loading_limit <= 1 or not 0 < near_limit_fraction <= 1:
        raise ValueError("Limites devem pertencer a (0, 1]")
    catalog = sorted(set(float(value) for value in catalog_kva if value > 0))
    if not catalog:
        raise ValueError("Catálogo comercial vazio")

    total = base_peak_kva + ev_peak_kva
    required = total / loading_limit
    recommended = next((value for value in catalog if value >= required), None)
    needs_upgrade = required > current_kva
    if recommended is None:
        classification = "structural_reinforcement_required"
    elif needs_upgrade:
        classification = "replacement_required"
    elif total / (current_kva * loading_limit) >= near_limit_fraction:
        classification = "near_limit"
    else:
        classification = "adequate"

    return TransformerAssessment(
        transformer_id=transformer_id,
        current_kva=current_kva,
        base_peak_kva=base_peak_kva,
        ev_peak_kva=ev_peak_kva,
        total_peak_kva=total,
        current_loading_percent=100 * base_peak_kva / current_kva,
        ev_loading_percent=100 * total / current_kva,
        current_margin_kva=current_kva * loading_limit - base_peak_kva,
        required_kva=required,
        recommended_kva=recommended,
        needs_upgrade=needs_upgrade,
        classification=classification,
    )
