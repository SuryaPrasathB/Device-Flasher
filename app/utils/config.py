import json
import os
import sys

class Config:
    _instance = None
    _config_data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        try:
            # Look for config.json in the current directory or app root
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels to root (app/utils -> app -> root)
            root_path = os.path.dirname(os.path.dirname(base_path))
            config_path = os.path.join(root_path, 'config.json')
            
            if not os.path.exists(config_path):
                # Fallback to current directory
                config_path = 'config.json'

            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self._config_data = json.load(f)
            else:
                print(f"Warning: Config file not found at {config_path}. Using defaults.")
                self._config_data = {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config_data = {}

    def get(self, section, key, default=None):
        return self._config_data.get(section, {}).get(key, default)

    @property
    def modbus_settings(self):
        return self._config_data.get('modbus', {})

    @property
    def register_map(self):
        return self._config_data.get('register_map', {})

# Global instance
config = Config()
