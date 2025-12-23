"""Lightweight YAML loader for the config/ directory.

This helper reads YAML files present in the `config/` directory and exposes a
programmatic `get_config(name)` helper. It performs minimal redaction of
sensitive keys (client_secret, api_key) when returning `redacted=True`.

Note: This module depends on `pyyaml`. If it's not available the functions
will raise an informative ImportError.
"""

from __future__ import annotations

import glob
import os
from typing import Any, Dict


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in ("secret", "password", "api_key", "client_secret")):
                out[k] = "<REDACTED>"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _load_yaml(path: str) -> Dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - informative
        raise ImportError("PyYAML is required to load config files. Install with `pip install pyyaml`") from exc

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_all_configs(config_dir: str = None) -> Dict[str, Dict[str, Any]]:
    config_dir = config_dir or os.path.join(os.path.dirname(__file__))
    result: Dict[str, Dict[str, Any]] = {}
    for path in glob.glob(os.path.join(config_dir, "*.yaml")):
        name = os.path.splitext(os.path.basename(path))[0]
        result[name] = _load_yaml(path)
    return result


def get_config(name: str, redacted: bool = True) -> Dict[str, Any]:
    """Return the named config (filename without extension).

    Args:
        name: e.g. "azure", "models", "personalization"
        redacted: if True, sensitive-looking keys are redacted from the result
    """
    config_dir = os.path.join(os.path.dirname(__file__))
    path = os.path.join(config_dir, f"{name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    data = _load_yaml(path)
    if redacted:
        return _redact(data)
    return data


__all__ = ["load_all_configs", "get_config"]
