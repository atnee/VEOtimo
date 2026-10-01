"""Carregamento e validação da configuração independente de cidade."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Indica configuração ausente, inconsistente ou fora do domínio."""


@dataclass(frozen=True)
class StudyConfig:
    name: str
    city: str
    country: str
    modeling_level: int
    electrical_network: str
    road_network: str
    timezone: str


@dataclass(frozen=True)
class Config:
    """Configuração validada, mantendo seções extensíveis em ``raw``."""

    study: StudyConfig
    seed: int
    output_root: Path
    raw: dict[str, Any]


REQUIRED_SECTIONS = {
    "study",
    "reproducibility",
    "time",
    "inputs",
    "electrical",
    "mobility",
    "queueing",
    "chargers",
    "optimization",
    "scenarios",
}


def load_config(path: str | Path) -> Config:
    """Lê YAML, valida invariantes transversais e devolve objeto imutável."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError(f"Arquivo de configuração inexistente: {config_path}")
    with config_path.open(encoding="utf-8") as stream:
        # JSON é subconjunto válido de YAML e evita dependência no bootstrap.
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise ConfigurationError("A raiz da configuração deve ser um mapeamento YAML")

    missing = sorted(REQUIRED_SECTIONS - raw.keys())
    if missing:
        raise ConfigurationError(f"Seções obrigatórias ausentes: {', '.join(missing)}")

    study_raw = raw["study"]
    required_study = {
        "name", "city", "country", "modeling_level", "electrical_network",
        "road_network", "timezone",
    }
    missing_study = sorted(required_study - study_raw.keys())
    if missing_study:
        raise ConfigurationError(f"Campos de study ausentes: {', '.join(missing_study)}")
    level = study_raw["modeling_level"]
    if level not in (1, 2, 3):
        raise ConfigurationError("study.modeling_level deve ser 1, 2 ou 3")

    electrical = raw["electrical"]
    v_min, v_max = electrical["voltage_min_pu"], electrical["voltage_max_pu"]
    if not (0 < v_min < v_max):
        raise ConfigurationError("Limites de tensão devem satisfazer 0 < mínimo < máximo")
    loading_limit = electrical["transformer_loading_limit"]
    if not 0 < loading_limit <= 1:
        raise ConfigurationError("transformer_loading_limit deve pertencer a (0, 1]")
    penetration = raw["mobility"]["ev_penetration"]
    if not 0 <= penetration <= 1:
        raise ConfigurationError("mobility.ev_penetration deve pertencer a [0, 1]")
    if raw["time"]["periods"] <= 0 or raw["time"]["resolution_minutes"] <= 0:
        raise ConfigurationError("Horizonte e resolução temporal devem ser positivos")
    catalog = electrical["transformer_catalog_kva"]
    if not catalog or catalog != sorted(set(catalog)) or min(catalog) <= 0:
        raise ConfigurationError("Catálogo de transformadores deve ser positivo e crescente")

    study = StudyConfig(**{key: study_raw[key] for key in required_study})
    reproducibility = raw["reproducibility"]
    return Config(
        study=study,
        seed=int(reproducibility["seed"]),
        output_root=Path(reproducibility["output_root"]),
        raw=raw,
    )
