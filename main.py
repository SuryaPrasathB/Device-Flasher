import sys
import os

# Ensure app is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.logger import logger
from PySide6.QtWidgets import QApplication

def main():
    logger.info("Starting Device Flasher Application...")
    
    # We will import MainWindow here to avoid circular imports or early Qt init
    try:
        from app.ui.main_window import MainWindow
        app = QApplication(sys.argv)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except ImportError as e:
        logger.error(f"Failed to import UI components: {e}")
        # For now, during development before UI is built, we might just exit
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
