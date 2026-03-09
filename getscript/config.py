"""Configuration loading with XDG base directory compliance."""

import json
import os


def get_config_dir() -> str:
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "getscript",
    )


def get_cache_dir() -> str:
    return os.path.join(
        os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
        "getscript",
    )


def load_config() -> dict:
    """Load config from XDG config file. Returns empty dict if not found."""
    config_path = os.path.join(get_config_dir(), "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return {}


def merge_config(file_config: dict, cli_args: dict) -> dict:
    """Merge config sources: file < env vars < CLI flags.

    CLI flags override env vars override file config.
    Only non-None CLI values override.
    """
    merged = dict(file_config)

    # Env var overrides
    if os.environ.get("NO_COLOR"):
        merged["no_color"] = True

    # CLI flag overrides (only if explicitly set)
    for key, value in cli_args.items():
        if value is not None:
            merged[key] = value

    return merged
