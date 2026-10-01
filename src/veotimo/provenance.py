"""Proveniência obrigatória para distinguir medições e aproximações."""

from dataclasses import dataclass
from enum import StrEnum


class SourceKind(StrEnum):
    MEASURED = "measured"
    ESTIMATED = "estimated"
    SYNTHETIC = "synthetic"


@dataclass(frozen=True)
class Provenance:
    source_kind: SourceKind
    source: str
    method: str | None = None

    def __post_init__(self) -> None:
        if self.source_kind is not SourceKind.MEASURED and not self.method:
            raise ValueError("Dados estimados ou sintéticos exigem descrição do método")
