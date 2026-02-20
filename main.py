import sys
import os

# Ensure app is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.logger import logger
from app.utils.helpers import get_resource_path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

def main():
    logger.info("Starting LDU Tester Application...")
    
    # Import MainWindow here to avoid circular imports or early Qt init
    try:
        from app.ui.main_window import MainWindow
        app = QApplication(sys.argv)
        
        # Set application icon
        icon_path = get_resource_path('resources/app_icon.png')
        app.setWindowIcon(QIcon(icon_path))
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except ImportError as e:
        logger.error(f"Failed to import UI components: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
