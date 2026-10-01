"""Enumeração exata para benchmarks pequenos."""

from itertools import product
from typing import Any

from .base_optimizer import BaseOptimizer, EvaluatableProblem, OptimizationResult


class ExhaustiveOptimizer(BaseOptimizer):
    """Obtém o ótimo global no espaço inteiro finito do benchmark."""

    def solve(self, problem: EvaluatableProblem, config: dict[str, Any]) -> OptimizationResult:
        max_count = int(config.get("max_count", getattr(problem, "max_count", 1)))
        best_vector: tuple[int, ...] | None = None
        best = None
        evaluations = 0
        convergence: list[float] = []
        for vector in product(range(max_count + 1), repeat=problem.dimension):
            evaluation = problem.evaluate(vector)
            evaluations += 1
            if best is None or evaluation.objective < best.objective:
                best, best_vector = evaluation, vector
            convergence.append(best.objective)
        assert best is not None and best_vector is not None
        return OptimizationResult(
            algorithm="exhaustive",
            best_vector=problem.repair(best_vector),
            best_evaluation=best,
            evaluations=evaluations,
            iterations=evaluations,
            convergence=tuple(convergence),
        )
