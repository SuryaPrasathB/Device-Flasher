import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QTextEdit, QTabWidget, QTabBar
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon

from app.modbus.port_scanner import PortScanner
from app.ui.worker import FlashWorker
from app.utils.logger import logger
from app.utils.config import config
from app.utils.helpers import get_resource_path

# Tabs
from app.ui.tabs.slave_id_tab import SlaveIDTab
from app.ui.tabs.testing_tab import TestingTab
from app.ui.tabs.relay_tab import RelayTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.tabs.placeholder_tab import PlaceholderTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load Window Settings
        app_conf = config.get("app", default={})
        title = app_conf.get("window_title", "Device Tester")
        w = app_conf.get("window_width", 500)
        h = app_conf.get("window_height", 650)

        self.setWindowTitle(title)
        self.resize(w, h)
        
        # Apply Dark Theme
        self.setStyleSheet("background-color: #1a202c; color: white;")

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Top Bar: Port Selection & Status (Global)
        self._init_top_bar()
        
        # 2. Tabs
        self._init_tabs()
        
        # 3. Log Area
        self._init_log_area()

        # Port Auto-Refresh Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(2000)

        # Legacy Worker for Flash Tab
        self.flash_thread = None
        self.flash_worker = None

        self.refresh_ports()

    def _init_top_bar(self):
        top_layout = QHBoxLayout()
        
        # Logo/Title small
        lbl = QLabel("🔌")
        lbl.setStyleSheet("font-size: 20px;")
        top_layout.addWidget(lbl)
        
        # Port Combo
        self.combo_ports = QComboBox()
        self.combo_ports.addItem("Select COM Port", None)
        self.combo_ports.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
                min-width: 150px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #4a5568;
            }
        """)
        self.combo_ports.currentIndexChanged.connect(self.on_port_changed)
        top_layout.addWidget(self.combo_ports)
        
        # Status
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background-color: #4a5568; border-radius: 6px;")
        top_layout.addWidget(self.status_dot)
        
        top_layout.addStretch()
        self.layout.addLayout(top_layout)

    def _init_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.South) # Bottom Tabs
        
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4a5568;
                background: #1a202c;
            }
            QTabBar::tab {
                background: #2d3748;
                color: #a0aec0;
                padding: 10px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #4a5568;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #4a5568;
            }
        """)

        # Tab 1: Slave ID (Legacy)
        self.tab_slave_id = SlaveIDTab()
        self.tab_slave_id.request_flash.connect(self.start_flash_legacy)
        self.tabs.addTab(self.tab_slave_id, "Set ID")

        # Tab 2: Testing (Refactored LOE)
        self.tab_testing = TestingTab()
        self.tab_testing.log_message.connect(self.log)
        self.tabs.addTab(self.tab_testing, "Testing")

        # Tab 3: Relays
        self.tab_relays = RelayTab()
        self.tab_relays.log_message.connect(self.log)
        self.tabs.addTab(self.tab_relays, "Relays")

        # Tab 4: Settings
        self.tab_settings = SettingsTab()
        self.tabs.addTab(self.tab_settings, "Settings")
        
        # Tab 4: Placeholder
        self.tab_tbd = PlaceholderTab()
        self.tabs.addTab(self.tab_tbd, "Extra")

        self.layout.addWidget(self.tabs)

    def _init_log_area(self):
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(100)
        self.log_area.setStyleSheet("background-color: #0f131a; color: white; border: 1px solid #2d3748; border-radius: 4px; font-family: Courier New; font-size: 11px;")
        self.layout.addWidget(self.log_area)
        self.log("System ready...")

    # --- Port Logic ---

    def refresh_ports(self):
        self.combo_ports.clear()
        self.combo_ports.addItem("Select COM Port", None)
        ports = PortScanner.get_available_ports()
        for p in ports:
            self.combo_ports.addItem(f"{p['port']} - {p['description']}", p['port'])

    def check_ports(self):
        # Auto-refresh logic same as before
        new_ports = PortScanner.get_available_ports()
        current_port_data = self.combo_ports.currentData()
        
        current_items = []
        for i in range(1, self.combo_ports.count()):
            current_items.append(self.combo_ports.itemData(i))

        new_port_ids = [p['port'] for p in new_ports]
        
        if set(current_items) != set(new_port_ids):
            self.combo_ports.blockSignals(True)
            self.combo_ports.clear()
            self.combo_ports.addItem("Select COM Port", None)
            for p in new_ports:
                self.combo_ports.addItem(f"{p['port']} - {p['description']}", p['port'])
            
            index = self.combo_ports.findData(current_port_data)
            if index >= 0:
                self.combo_ports.setCurrentIndex(index)
            else:
                self.combo_ports.setCurrentIndex(0)

            self.combo_ports.blockSignals(False)
            
            if index == -1 and current_port_data is not None:
                self.on_port_changed()

    def on_port_changed(self):
        port = self.combo_ports.currentData()

        # Notify Tabs
        if hasattr(self, 'tab_testing'):
            self.tab_testing.set_current_port(port)
        if hasattr(self, 'tab_relays'):
            self.tab_relays.set_current_port(port)

        if port:
            self.status_dot.setStyleSheet("background-color: #48bb78; border-radius: 6px;")
            self.log(f"Connected to {port}", "SUCCESS")
            self.tab_slave_id.set_enabled(True)
        else:
            self.status_dot.setStyleSheet("background-color: #4a5568; border-radius: 6px;")
            self.log("Disconnected", "INFO")
            self.tab_slave_id.set_enabled(False)

    # --- Logging ---

    def log(self, message, level="INFO"):
        color = "#e2e8f0"
        if "success" in level.lower(): color = "#48bb78"
        if "error" in level.lower() or "fail" in level.lower(): color = "#f56565"
        
        self.log_area.append(f'<span style="color:{color}">[{level}] {message}</span>')
        logger.info(f"[{level}] {message}")

    # --- Legacy Flash Logic (Tab 1) ---

    def start_flash_legacy(self, slave_id):
        port = self.combo_ports.currentData()
        if not port:
            self.log("No Port Selected", "ERROR")
            return

        self.tab_slave_id.set_button_state("Flashing...", False)
        self.log(f"Starting legacy flash to ID {slave_id}...", "INFO")

        # Create Thread & Worker
        from PySide6.QtCore import QThread
        self.flash_thread = QThread()
        self.flash_worker = FlashWorker(port, slave_id)
        self.flash_worker.moveToThread(self.flash_thread)
        
        self.flash_thread.started.connect(self.flash_worker.run)
        self.flash_worker.finished.connect(self.on_flash_finished)
        self.flash_worker.progress.connect(self.on_flash_progress)
        self.flash_worker.finished.connect(self.flash_thread.quit)
        self.flash_worker.finished.connect(self.flash_worker.deleteLater)
        self.flash_thread.finished.connect(self.flash_thread.deleteLater)
        
        self.flash_thread.start()

    @Slot(str, int)
    def on_flash_progress(self, msg, pct):
        self.log(msg)

    @Slot(bool, str)
    def on_flash_finished(self, success, message):
        if success:
            self.log(message, "SUCCESS")
            self.tab_slave_id.set_button_state("Flash Complete ✓", True)
        else:
            self.log(message, "ERROR")
            self.tab_slave_id.set_button_state("Retry", True)
        
        # Reset button text after 3s
        QTimer.singleShot(3000, lambda: self.tab_slave_id.set_button_state("Set Slave ID", True))
