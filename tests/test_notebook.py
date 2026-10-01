import ast
import json
from pathlib import Path


NOTEBOOK = Path(__file__).parents[1] / "notebooks" / "ieee33_analise_cientifica.ipynb"


def test_scientific_notebook_is_valid_and_code_compiles() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 15
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    for position, cell in enumerate(code_cells):
        ast.parse("".join(cell["source"]), filename=f"notebook-cell-{position}")


def test_notebook_covers_required_scientific_analyses() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    content = "".join("".join(cell["source"]) for cell in notebook["cells"])
    required_topics = (
        "Topologia do alimentador",
        "Caso base e validação numérica",
        "Decomposição espacial das perdas",
        "Efeito locacional",
        "Curva de estresse",
        "Capacidade de hospedagem",
        "Interpretação científica",
    )
    assert all(topic in content for topic in required_topics)
