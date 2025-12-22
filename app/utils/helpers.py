import sys
import os

def get_resource_path(relative_path):
    """ 
    Get absolute path to resource, works for dev and for PyInstaller.
    relative_path: Path relative to the project root (e.g. "config.json", "resources/icon.png")
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, relative_path)
