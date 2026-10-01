"""Interface mínima do pipeline incremental."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigurationError, load_config
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
