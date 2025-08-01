from pathlib import Path

from sync_module.tools import from_json


def test_load_solution_to_layers():
    with open(Path(__file__).parent.parent / "fixtures" / "mou.json") as f:
        solution = from_json(f.read())

        print(solution)


if __name__ == "__main__":
    test_load_solution_to_layers()
