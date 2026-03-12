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
from app.ui.tabs.stress_tester_tab import StressTesterTab
from app.ui.tabs.placeholder_tab import PlaceholderTab
from app.ui.tabs.slave_tester_tab import SlaveTesterTab
from app.ui.tabs.serial_scan_tab import SerialScanTab
from app.ui.tabs.active_slaves_tab import ActiveSlavesTab
from app.ui.tabs.overall_status_tab import OverallStatusTab

# Web integration
from app.web.manager import WebServerManager
from app.web.bridge import web_bridge
from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QPushButton

class WebControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remote Web Access")
        self.resize(300, 150)
        self.layout = QVBoxLayout(self)

        self.lbl_status = QLabel("Web Server Stopped")
        self.layout.addWidget(self.lbl_status)

        form_layout = QFormLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setReadOnly(True)
        self.pin_edit = QLineEdit()
        self.pin_edit.setReadOnly(True)

        form_layout.addRow("URL:", self.url_edit)
        form_layout.addRow("PIN:", self.pin_edit)
        self.layout.addLayout(form_layout)

        self.btn_toggle = QPushButton("Start Web Server & Ngrok")
        self.layout.addWidget(self.btn_toggle)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load Window Settings
        app_conf = config.get("app", default={})
        title = app_conf.get("window_title", "LDU Tester")
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

        # Web Integration
        self._init_web_integration()

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

        # Web Server Button
        self.btn_web_remote = QPushButton("🌐 Remote Access")
        self.btn_web_remote.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2c5282; }
        """)
        self.btn_web_remote.clicked.connect(self.show_web_dialog)
        top_layout.addWidget(self.btn_web_remote)

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

        # Tab 3: Stress Tester
        self.tab_stress_tester = StressTesterTab()
        self.tab_stress_tester.log_message.connect(self.log)
        self.tabs.addTab(self.tab_stress_tester, "Stress Tester")

        # Tab 4: Relays
        self.tab_relays = RelayTab()
        self.tab_relays.log_message.connect(self.log)
        self.tabs.addTab(self.tab_relays, "Relays")

        # Tab 4: Slave Tester
        self.tab_slave_tester = SlaveTesterTab()
        self.tab_slave_tester.log_message.connect(self.log)
        self.tabs.addTab(self.tab_slave_tester, "Slave Tester")

        # Tab 5: Serial Scan
        self.tab_serial_scan = SerialScanTab()
        self.tab_serial_scan.log_message.connect(self.log)
        self.tabs.addTab(self.tab_serial_scan, "Serial Scan")

        # Tab 6: Active Slaves
        self.tab_active_slaves = ActiveSlavesTab()
        self.tab_active_slaves.log_message.connect(self.log)
        self.tabs.addTab(self.tab_active_slaves, "Active Slaves")

        # Tab 7: Overall Status
        self.tab_overall_status = OverallStatusTab()
        self.tab_overall_status.log_message.connect(self.log)
        self.tabs.addTab(self.tab_overall_status, "Overall Status")

        # Tab 8: Settings
        self.tab_settings = SettingsTab()
        self.tabs.addTab(self.tab_settings, "Settings")

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
        if hasattr(self, 'tab_stress_tester'):
            self.tab_stress_tester.set_current_port(port)
        if hasattr(self, 'tab_relays'):
            self.tab_relays.set_current_port(port)
        if hasattr(self, 'tab_slave_tester'):
            self.tab_slave_tester.set_current_port(port)
        if hasattr(self, 'tab_serial_scan'):
            self.tab_serial_scan.set_current_port(port)
        if hasattr(self, 'tab_active_slaves'):
            self.tab_active_slaves.set_current_port(port)
        if hasattr(self, 'tab_overall_status'):
            self.tab_overall_status.set_current_port(port)

        if port:
            self.status_dot.setStyleSheet("background-color: #48bb78; border-radius: 6px;")
            self.log(f"Connected to {port}", "SUCCESS")
            self.tab_slave_id.set_enabled(True)
        else:
            self.status_dot.setStyleSheet("background-color: #4a5568; border-radius: 6px;")
            self.log("Disconnected", "INFO")
            self.tab_slave_id.set_enabled(False)

    # --- Web Integration ---
    def _init_web_integration(self):
        self.web_manager = WebServerManager(port=8080)
        self.web_manager.server_started.connect(self.on_web_server_started)
        self.web_manager.server_error.connect(self.on_web_server_error)

        self.web_dialog = WebControlDialog(self)
        self.web_dialog.btn_toggle.clicked.connect(self.toggle_web_server)

        # Connect bridge signals to actions
        web_bridge.request_set_slave_id.connect(self.on_web_request_set_id)
        web_bridge.request_start_slave_tester.connect(self.on_web_request_start_slave_test)
        web_bridge.request_start_stress_tester.connect(self.on_web_request_start_stress_test)
        web_bridge.request_stop_stress_tester.connect(self.on_web_request_stop_stress_test)

    def show_web_dialog(self):
        self.web_dialog.show()

    def toggle_web_server(self):
        if not self.web_manager._is_running:
            self.web_dialog.btn_toggle.setText("Starting...")
            self.web_dialog.btn_toggle.setEnabled(False)
            self.web_manager.start_server(use_ngrok=True)
        else:
            self.web_manager.stop_server()
            self.web_dialog.lbl_status.setText("Web Server Stopped")
            self.web_dialog.url_edit.setText("")
            self.web_dialog.pin_edit.setText("")
            self.web_dialog.btn_toggle.setText("Start Web Server & Ngrok")
            self.log("Remote Web Access stopped.", "INFO")

    @Slot(str, str)
    def on_web_server_started(self, url, pin):
        self.web_dialog.btn_toggle.setEnabled(True)
        self.web_dialog.lbl_status.setText(f"Web Server Running")
        self.web_dialog.url_edit.setText(url)
        self.web_dialog.pin_edit.setText(pin)
        self.web_dialog.btn_toggle.setText("Stop Web Server")
        self.log(f"Remote Web Access started. URL: {url} | PIN: {pin}", "SUCCESS")

        # Start state sync timer
        if not hasattr(self, 'state_sync_timer'):
            self.state_sync_timer = QTimer(self)
            self.state_sync_timer.timeout.connect(self.sync_web_state)
            self.state_sync_timer.start(500) # Sync every 500ms

    @Slot(str)
    def on_web_server_error(self, err):
        self.web_dialog.btn_toggle.setEnabled(True)
        self.web_dialog.btn_toggle.setText("Start Web Server & Ngrok")
        self.log(f"Web Server Error: {err}", "ERROR")

    def get_slave_tester_results(self):
        """Parse the results area to send a dictionary to the web."""
        if not hasattr(self.tab_slave_tester, 'results_area'):
            return {}
        html = self.tab_slave_tester.results_area.toHtml()
        import re
        results = {}
        # The SlaveTesterTab emits: 'ID {sid}: <span...>{PASS|FAIL}</span>'
        matches = re.findall(r'ID\s+(\d+):\s*<.*?>\s*(PASS|FAIL)\s*<', html)
        for m in matches:
            results[f"ID {m[0]}"] = m[1]
        return results

    def sync_web_state(self):
        """Build a dictionary of the current UI state to send to the web clients."""
        if not self.web_manager._is_running:
            return

        state = {
            "port": self.combo_ports.currentData(),
            "tabs": {
                "set_id": {
                    "id": self.tab_slave_id.input_slave_id.value(),
                    "status": self.tab_slave_id.btn_flash.text(),
                },
                "slave_tester": {
                    "status": getattr(self.tab_slave_tester, 'btn_test', None).text() if hasattr(self.tab_slave_tester, 'btn_test') else "",
                    "results": self.get_slave_tester_results()
                },
                "stress_tester": {
                    "is_running": getattr(self.tab_stress_tester, 'is_running', False),
                    "from_id": self.tab_stress_tester.spin_from_id.value(),
                    "to_id": self.tab_stress_tester.spin_to_id.value(),
                    "reg": self.tab_stress_tester.spin_register.value(),
                    "delay_ms": self.tab_stress_tester.spin_delay.value(),
                    "data_type": self.tab_stress_tester.combo_data_type.currentText(),
                    "total_hits": int(self.tab_stress_tester.lbl_total_hits.text() or 0),
                    "success": int(self.tab_stress_tester.lbl_success.text() or 0),
                    "failure": int(self.tab_stress_tester.lbl_failure.text() or 0),
                    "failure_percent": self.tab_stress_tester.lbl_failure_percent.text(),
                    "max_fail_id": self.tab_stress_tester.lbl_max_fail_id.text()
                }
            }
        }
        web_bridge.emit_gui_state(state)

    @Slot(int)
    def on_web_request_set_id(self, new_id):
        self.log(f"Web Request: Set ID {new_id}")
        # The legacy worker sets input_slave_id = input_slave_id - 1 upon success.
        # To ensure it ends up on `new_id` when finished, we set the input value
        # to `new_id + 1`. But wait, `start_flash_legacy(new_id)` actually broadcasts
        # the argument. Since we want `new_id` to be broadcasted, we pass `new_id`.
        # However, we must set the UI spinbox to `new_id + 1` so that when the
        # worker decrements it by 1, it settles at `new_id`.
        self.tab_slave_id.input_slave_id.setValue(new_id + 1)
        self.start_flash_legacy(new_id)

    @Slot(int)
    def on_web_request_start_slave_test(self, slave_id):
        self.log(f"Web Request: Test Slave ID {slave_id}")
        self.tab_slave_tester.spin_from.setValue(slave_id)
        self.tab_slave_tester.spin_to.setValue(slave_id)
        self.tab_slave_tester.on_test_clicked()

    @Slot(int, int, int, int, str)
    def on_web_request_start_stress_test(self, from_id, to_id, reg, delay_ms, data_type):
        self.log(f"Web Request: Start Stress Test {from_id}-{to_id}")
        self.tab_stress_tester.spin_from_id.setValue(from_id)
        self.tab_stress_tester.spin_to_id.setValue(to_id)
        self.tab_stress_tester.spin_register.setValue(reg)
        self.tab_stress_tester.spin_delay.setValue(delay_ms)
        self.tab_stress_tester.combo_data_type.setCurrentText(data_type)
        self.tab_stress_tester.start_test()

    @Slot()
    def on_web_request_stop_stress_test(self):
        self.log(f"Web Request: Stop Stress Test")
        self.tab_stress_tester.stop_test()

    # --- Logging ---

    def log(self, message, level="INFO"):
        color = "#e2e8f0"
        if "success" in level.lower(): color = "#48bb78"
        if "error" in level.lower() or "fail" in level.lower(): color = "#f56565"
        
        log_str = f'<span style="color:{color}">[{level}] {message}</span>'
        self.log_area.append(log_str)
        logger.info(f"[{level}] {message}")

        # Broadcast log to web clients
        web_bridge.emit_gui_state({"log": log_str})

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
            slaveid = self.tab_slave_id.input_slave_id.value()
            self.tab_slave_id.input_slave_id.setValue(slaveid - 1)
        else:
            self.log(message, "ERROR")
            self.tab_slave_id.set_button_state("Retry", True)
        
        # Reset button text after 3s
        QTimer.singleShot(3000, lambda: self.tab_slave_id.set_button_state("Set Slave ID", True))
