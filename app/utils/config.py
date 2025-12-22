import json
import os
import sys
from app.utils.helpers import get_resource_path

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
            config_path = get_resource_path('config.json')
            
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
