"""
Configuration manager for the Mangago Downloader GUI.
Handles saving and loading user preferences.
"""

import os
import json
from typing import Any, Dict
from pathlib import Path


class ConfigManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_file: str = "gui_config.json"):
        """Initialize the configuration manager."""
        self.config_file = Path(config_file)
        self.default_config = {
            "download_location": str(Path.home() / "Downloads" / "mangago"),
            "max_workers": 5,
            "retry_count": 3,
            "timeout": 30,
            "overwrite_existing": False,
            "format": "images",
            "delete_images": False
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, or return defaults if file doesn't exist."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys are present
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                return self.default_config.copy()
        else:
            # Create config file with defaults if it doesn't exist
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save to file."""
        self.config[key] = value
        self.save_config(self.config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.copy()
    
    def set_all(self, config: Dict[str, Any]) -> None:
        """Set all configuration values and save to file."""
        self.config = config
        self.save_config(self.config)