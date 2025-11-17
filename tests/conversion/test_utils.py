import pytest
from mi_companion.mi_editor.conversion.layers.from_solution.utils import sanitize_name

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
    assert sanitize_name(input_name) == expected
