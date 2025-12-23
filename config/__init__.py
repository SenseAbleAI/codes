"""Config package helpers.

Expose `get_config()` as a convenience wrapper for modules to consume YAML
config without importing the loader implementation directly.
"""

from .loader import get_config, load_all_configs

__all__ = ["get_config", "load_all_configs"]
