from pathlib import Path

import pytest
import json

from veotimo.config import ConfigurationError, load_config


ROOT = Path(__file__).parents[1]


def test_example_configuration_is_valid() -> None:
    config = load_config(ROOT / "config.yaml")
    assert config.study.modeling_level == 1
    assert config.study.city == "synthetic"


def test_invalid_penetration_is_rejected(tmp_path: Path) -> None:
    raw = json.loads((ROOT / "config.yaml").read_text(encoding="utf-8"))
    raw["mobility"]["ev_penetration"] = 1.1
    path = tmp_path / "invalid.yaml"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="ev_penetration"):
        load_config(path)
