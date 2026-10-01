"""Algoritmo genético inteiro, reprodutível e sem dependências externas."""

from __future__ import annotations

import random
from typing import Any

from .base_optimizer import BaseOptimizer, EvaluatableProblem, OptimizationResult


class GeneticAlgorithmOptimizer(BaseOptimizer):
    def solve(self, problem: EvaluatableProblem, config: dict[str, Any]) -> OptimizationResult:
        rng = random.Random(int(config.get("seed", 42)))
        population_size = int(config.get("population", 50))
        generations = int(config.get("iterations", 100))
        mutation_rate = float(config.get("mutation_rate", 0.10))
        crossover_rate = float(config.get("crossover_rate", 0.90))
        elite_count = max(1, int(config.get("elite_count", 2)))
        max_count = int(config.get("max_count", getattr(problem, "max_count", 1)))
        if population_size < 2 or generations < 1:
            raise ValueError("GA requer população >= 2 e pelo menos uma geração")

        def individual() -> tuple[int, ...]:
            return problem.repair(tuple(rng.randint(0, max_count) for _ in range(problem.dimension)))

        # Inclui soluções de borda úteis sem conhecer a função objetivo: vazio e
        # concentração da capacidade em cada gene. Isso melhora factibilidade
        # inicial e não elimina a exploração estocástica.
        seeds = [problem.repair(tuple(0 for _ in range(problem.dimension)))]
        seeds.extend(
            problem.repair(tuple(max_count if index == active else 0 for index in range(problem.dimension)))
            for active in range(problem.dimension)
        )
        population = seeds[:population_size]
        population.extend(individual() for _ in range(population_size - len(population)))
        evaluations = 0
        best_vector = population[0]
        best = problem.evaluate(best_vector)
        evaluations += 1
        convergence: list[float] = []

        def tournament(scored: list[tuple[float, tuple[int, ...]]]) -> tuple[int, ...]:
            contenders = rng.sample(scored, k=min(3, len(scored)))
            return min(contenders, key=lambda item: item[0])[1]

        for _ in range(generations):
            scored = []
            for vector in population:
                evaluation = problem.evaluate(vector)
                evaluations += 1
                scored.append((evaluation.objective, vector))
                if evaluation.objective < best.objective:
                    best, best_vector = evaluation, vector
            scored.sort(key=lambda item: item[0])
            convergence.append(best.objective)
            next_population = [vector for _, vector in scored[:elite_count]]
            while len(next_population) < population_size:
                parent_a, parent_b = tournament(scored), tournament(scored)
                if problem.dimension > 1 and rng.random() < crossover_rate:
                    point = rng.randrange(1, problem.dimension)
                    child = parent_a[:point] + parent_b[point:]
                else:
                    child = parent_a
                genes = list(child)
                for index in range(problem.dimension):
                    if rng.random() < mutation_rate:
                        genes[index] = rng.randint(0, max_count)
                next_population.append(problem.repair(tuple(genes)))
            population = next_population
        return OptimizationResult(
            algorithm="ga",
            best_vector=best_vector,
            best_evaluation=best,
            evaluations=evaluations,
            iterations=generations,
            convergence=tuple(convergence),
        )
