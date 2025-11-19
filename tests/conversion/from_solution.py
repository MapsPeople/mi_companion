from pathlib import Path
import pytest

from sync_module.tools import from_json
from mi_companion.mi_editor.conversion.layers.from_solution.venue import _sanitize_graph_name

@pytest.mark.parametrize(
    "input_name,expected",
    [
        # Basic behavior
        ("Ben & Jerry Avenue (First)", "ben_jerry_avenue_first"),
        ("Main Street", "main_street"),
        ("Hello World", "hello_world"),
        # Collapse whitespace
        ("  Too   Many   Spaces  ", "too_many_spaces"),
        # Special characters removed
        ("Crazy!!Name##Here??", "crazy_name_here"),
        # Multiple underscores should collapse
        ("A   B---C", "a_b_c"),
        # Leading/trailing junk
        ("***Hello***", "hello"),
        # Unicode normalization (accents stripped)
        ("Café del Mar", "cafe_del_mar"),
        ("Beyoncé Knowles", "beyonce_knowles"),
        ("Łódź City", "lodz_city"),
        # Non-ASCII punctuation, symbols
        ("Road ✨ to Paradise", "road_to_paradise"),
        ("Price 50€ Only", "price_50_only"),
        # Empty-ish cases
        ("_", ""),  
        ("---", ""),
        ("     ", ""),
        # Mixed complex case
        ("  GrößE & Münchën @ Night!! ", "grosse_munchen_night"),
    ]
)
def test_sanitize_name(input_name, expected):
    assert _sanitize_graph_name(input_name) == expected


def test_load_solution_to_layers():
    with open(Path(__file__).parent.parent / "fixtures" / "mou.json") as f:
        solution = from_json(f.read())

        print(solution)


if __name__ == "__main__":
    test_load_solution_to_layers()
