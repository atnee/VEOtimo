from pathlib import Path

import pytest

from veotimo.optimization import (
    ExhaustiveOptimizer,
    GeneticAlgorithmOptimizer,
    load_problem,
)


ROOT = Path(__file__).parents[1]
CASE = ROOT / "data" / "processed" / "ieee33_optimization_case.json"


def test_problem_repair_limits_counts_and_number_of_stations() -> None:
    problem = load_problem(CASE, ROOT)
    repaired = problem.repair((9, -2, 3, 2, 1))
    assert all(0 <= count <= 3 for count in repaired)
    assert sum(count > 0 for count in repaired) <= 3


def test_unserved_solution_is_penalized_and_infeasible() -> None:
    problem = load_problem(CASE, ROOT)
    empty = problem.evaluate((0, 0, 0, 0, 0))
    assert not empty.feasible
    assert empty.unserved_kw == 180
    assert empty.penalty_cost >= 180_000_000


def test_exhaustive_optimizer_finds_feasible_global_optimum() -> None:
    problem = load_problem(CASE, ROOT)
    result = ExhaustiveOptimizer().solve(problem, {})
    assert result.evaluations == 4 ** 5
    assert result.best_evaluation.feasible
    assert result.best_evaluation.served_kw == 180
    assert sum(result.best_vector) == 3
    # Confirma por construção que nenhuma solução enumerada é melhor.
    assert result.best_evaluation.objective == min(result.convergence)


def test_ga_is_reproducible_and_reaches_exact_benchmark() -> None:
    exact_problem = load_problem(CASE, ROOT)
    exact = ExhaustiveOptimizer().solve(exact_problem, {})
    config = {"population": 40, "iterations": 40, "seed": 7}
    first = GeneticAlgorithmOptimizer().solve(load_problem(CASE, ROOT), config)
    second = GeneticAlgorithmOptimizer().solve(load_problem(CASE, ROOT), config)
    assert first.best_vector == second.best_vector
    assert first.convergence == second.convergence
    assert first.best_evaluation.objective == pytest.approx(exact.best_evaluation.objective)
