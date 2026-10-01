"""Interface mínima do pipeline incremental."""

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigurationError, load_config
from .optimization import ExhaustiveOptimizer, GeneticAlgorithmOptimizer, load_problem
from .powerflow import load_network, run_power_flow


def _run_id(study_name: str, seed: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{study_name}-{stamp}-s{seed}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="veotimo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validar configuração do caso")
    validate.add_argument("--config", default="config.yaml")
    powerflow = subparsers.add_parser("powerflow", help="executar benchmark radial")
    powerflow.add_argument("--network", default="data/networks/ieee33.json")
    powerflow.add_argument("--voltage-min", type=float, default=0.95)
    powerflow.add_argument("--voltage-max", type=float, default=1.05)
    optimize = subparsers.add_parser("optimize", help="otimizar alocação VE no benchmark")
    optimize.add_argument(
        "--case", default="data/processed/ieee33_optimization_case.json"
    )
    optimize.add_argument("--algorithm", choices=("exhaustive", "ga"), default="exhaustive")
    optimize.add_argument("--population", type=int, default=50)
    optimize.add_argument("--iterations", type=int, default=100)
    optimize.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    if args.command == "powerflow":
        network = load_network(args.network)
        result = run_power_flow(
            network,
            voltage_min_pu=args.voltage_min,
            voltage_max_pu=args.voltage_max,
        )
        payload = {
            "network": network["metadata"]["name"],
            "converged": result.converged,
            "iterations": result.iterations,
            "minimum_voltage_pu": result.bus_voltage_pu[result.min_voltage_bus],
            "minimum_voltage_bus": result.min_voltage_bus,
            "active_losses_kw": result.active_losses_kw,
            "reactive_losses_kvar": result.reactive_losses_kvar,
            "voltage_violation_count": len(result.violations),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.converged else 2
    if args.command == "optimize":
        problem = load_problem(args.case)
        optimizer = (
            ExhaustiveOptimizer()
            if args.algorithm == "exhaustive"
            else GeneticAlgorithmOptimizer()
        )
        result = optimizer.solve(
            problem,
            {
                "population": args.population,
                "iterations": args.iterations,
                "seed": args.seed,
            },
        )
        payload = {
            "algorithm": result.algorithm,
            "evaluations": result.evaluations,
            "iterations": result.iterations,
            "decision_vector": result.best_vector,
            "solution": asdict(result.best_evaluation),
            "note": "synthetic_benchmark_not_a_city_result",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.best_evaluation.feasible else 3
    try:
        config = load_config(args.config)
    except ConfigurationError as error:
        parser.error(str(error))
    payload = {
        "status": "configuration_valid",
        "study": config.study.name,
        "city": config.study.city,
        "modeling_level": config.study.modeling_level,
        "run_id": _run_id(config.study.name, config.seed),
        "note": "validation_only_no_optimization_executed",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
