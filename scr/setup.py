"""Configurable settings."""
import yaml
from dotenv import load_dotenv
import os
from typing import Any

def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration file."""
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
        return config

def get_from_config(name: str) -> Any:
    """Get variable from config file."""
    keys = name.split(".")
    value = configs
    try:
        for key in keys:
            value = value[key]
        return value
    except KeyError:
        raise ValueError(f"{name} not set. Please set in config.yaml")

configs = load_config()

FACEBOOK_GROUPS = get_from_config("facebook_groups")



