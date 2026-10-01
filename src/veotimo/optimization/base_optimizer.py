"""Contratos comuns aos métodos exatos e metaheurísticos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol


class EvaluatableProblem(Protocol):
    dimension: int

    def evaluate(self, vector: tuple[int, ...]) -> Any: ...


@dataclass(frozen=True)
class OptimizationResult:
    algorithm: str
    best_vector: tuple[int, ...]
    best_evaluation: Any
    evaluations: int
    iterations: int
    convergence: tuple[float, ...]


class BaseOptimizer(ABC):
    """Interface requerida por todos os solvers: ``solve(problem, config)``."""

    @abstractmethod
    def solve(self, problem: EvaluatableProblem, config: dict[str, Any]) -> OptimizationResult:
        """Resolve o problema e retorna resultado padronizado."""
