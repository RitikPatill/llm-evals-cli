import yaml
import pathlib


def test_ci_yaml_is_valid():
    text = (pathlib.Path(__file__).parent.parent / ".github/workflows/ci.yml").read_text()
    assert yaml.safe_load(text) is not None
