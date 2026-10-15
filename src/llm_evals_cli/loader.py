from pathlib import Path
from typing import Any

import yaml

from llm_evals_cli.schema import Suite


def load_suite(path: str) -> Suite:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Suite file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return Suite.model_validate(data)
