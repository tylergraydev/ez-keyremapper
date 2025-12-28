"""
Configuration management - save/load mappings to JSON file.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    target_device: Optional[int] = None  # Interception device number (1-10)
    mappings: Dict[int, int] = None  # input_vk -> output_vk
    enabled: bool = True

    def __post_init__(self):
        if self.mappings is None:
            self.mappings = {}


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    home = Path.home()
    config_dir = home / ".ez-keyremapper"
    return config_dir


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def save_config(config: Config) -> bool:
    """
    Save configuration to file.

    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_config_dir()
        config_path = get_config_path()

        # Convert to JSON-serializable format
        data = {
            "target_device": config.target_device,
            "mappings": {str(k): v for k, v in config.mappings.items()},
            "enabled": config.enabled,
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def load_config() -> Config:
    """
    Load configuration from file.

    Returns:
        Config object (default if file doesn't exist or is invalid)
    """
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert mappings keys back to int
        mappings = {}
        if "mappings" in data and data["mappings"]:
            mappings = {int(k): v for k, v in data["mappings"].items()}

        # Get target device (int)
        target_device = data.get("target_device")

        return Config(
            target_device=target_device,
            mappings=mappings,
            enabled=data.get("enabled", True),
        )
    except Exception as e:
        print(f"Error loading config: {e}")
        return Config()
