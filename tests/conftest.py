"""Shared helpers for loading integration logic modules without Home Assistant."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def load_logic(domain: str):
    """Import integrations/<domain>/logic.py directly, bypassing the package __init__."""
    path = ROOT / "integrations" / domain / "logic.py"
    name = f"{domain}_logic"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
