import pytest

from veotimo.provenance import Provenance, SourceKind


def test_estimate_requires_method() -> None:
    with pytest.raises(ValueError, match="método"):
        Provenance(SourceKind.ESTIMATED, "censo")


def test_measurement_does_not_require_estimation_method() -> None:
    value = Provenance(SourceKind.MEASURED, "SCADA")
    assert value.method is None
