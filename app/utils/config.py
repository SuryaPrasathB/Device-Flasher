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

    def get(self, section, key=None, default=None):
        if key is None:
             return self._config_data.get(section, default)
        return self._config_data.get(section, {}).get(key, default)

    @property
    def modbus_settings(self):
        return self._config_data.get('modbus', {})

    @property
    def register_map(self):
        return self._config_data.get('register_map', {})

    def save(self):
        try:
            config_path = get_resource_path('config.json')
            # If get_resource_path returns a path inside a purely temporary dir (PyInstaller),
            # saving might not persist for next run if we don't save to a local user path.
            # However, for this task, we will try to save back to the original location if running from source,
            # or the local directory.

            # Simple approach: If running as script, save to file.
            # If compiled, this might need to save to AppData.
            # For now, we assume the file is writable.

            # We need to handle the case where get_resource_path points to the bundled resource.
            # When running from source, it points to the source file.

            with open(config_path, 'w') as f:
                json.dump(self._config_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

# Global instance
config = Config()
