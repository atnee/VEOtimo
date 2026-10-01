from veotimo.transformers import assess_transformer


def test_selects_next_commercial_rating() -> None:
    result = assess_transformer("T1", 75, 55, 20, 0.8, [75, 112.5, 150])
    assert result.required_kva == 93.75
    assert result.recommended_kva == 112.5
    assert result.needs_upgrade
    assert result.classification == "replacement_required"


def test_flags_structural_reinforcement_beyond_catalog() -> None:
    result = assess_transformer("T2", 150, 120, 200, 0.8, [150, 225, 300])
    assert result.recommended_kva is None
    assert result.classification == "structural_reinforcement_required"
