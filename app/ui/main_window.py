import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit, QMessageBox, QSpinBox, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QThread, Slot, QTimer
from PySide6.QtGui import QIcon, QFont, QColor

from app.modbus.port_scanner import PortScanner
from app.core.validation import Validator
from app.ui.worker import FlashWorker
from app.utils.logger import logger
from app.utils.helpers import get_resource_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Device Flasher")
        self.resize(500, 600)
        
        # Apply Dark Theme
        self.setStyleSheet("background-color: #1a202c; color: white;")

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self._init_header()
        
        # Form
        self._init_form()
        
        # Log Area
        self._init_log_area()
        
        # Worker Thread
        self.thread = None
        self.worker = None

        # Port Auto-Refresh Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(2000)  # Check every 2 seconds

        # Load Ports
        self.refresh_ports()

    def _init_header(self):
        header_layout = QVBoxLayout()
        title = QLabel("Device Flasher")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        subtitle = QLabel("Flash Slave ID to Embedded Controller")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #a0aec0;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.layout.addLayout(header_layout)

    def _init_form(self):
        # COM Port
        self.layout.addWidget(QLabel("COM Port"))
        self.combo_ports = QComboBox()
        self.combo_ports.addItem("Select COM Port", None)
        self.combo_ports.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #4a5568;
            }
        """)
        self.combo_ports.currentIndexChanged.connect(self.on_port_changed)
        self.layout.addWidget(self.combo_ports)
        
        # Status Indicator
        self.status_layout = QHBoxLayout()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background-color: #4a5568; border-radius: 6px;")
        self.status_text = QLabel("Not connected")
        self.status_text.setStyleSheet("color: #718096; font-size: 12px;")
        self.status_layout.addWidget(self.status_dot)
        self.status_layout.addWidget(self.status_text)
        self.status_layout.addStretch()
        self.layout.addLayout(self.status_layout)
        
        # Slave ID
        self.layout.addWidget(QLabel("Slave ID"))

        self.input_slave_id = QSpinBox()
        self.input_slave_id.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.input_slave_id.setRange(1, 247)
        self.input_slave_id.setSingleStep(1)
        self.input_slave_id.setValue(1)

        arrow_up = get_resource_path("resources/arrow_up.svg").replace("\\", "/")
        arrow_down = get_resource_path("resources/arrow_down.svg").replace("\\", "/")

        self.input_slave_id.setStyleSheet(f"""
            QSpinBox {{
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding-right: 20px;
                color: white;
            }}

            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #4a5568;
            }}

            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #4a5568;
            }}

            QSpinBox::up-arrow {{
                image: url({arrow_up});
                width: 10px;
                height: 10px;
            }}

            QSpinBox::down-arrow {{
                image: url({arrow_down});
                width: 10px;
                height: 10px;
            }}
        """)

        self.input_slave_id.valueChanged.connect(self.validate_form)

        self.layout.addWidget(self.input_slave_id)
        
        # Flash Button
        self.btn_flash = QPushButton("Set Slave ID")
        self.btn_flash.setFixedHeight(45)
        self.btn_flash.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a67d8, stop:1 #6b46c1);
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #a0aec0;
            }
        """)
        self.btn_flash.clicked.connect(self.start_flash)
        self.btn_flash.setEnabled(False)
        self.layout.addWidget(self.btn_flash)
        
        # Note
        note = QLabel("<b>Note:</b> Ensure the device is properly connected before flashing. "
                      "Valid Slave ID range: 1–247")
        note.setStyleSheet("background-color: #2d3748; color: #cbd5e0; padding: 10px; border-radius: 4px; font-size: 12px; border-left: 4px solid #4299e1;")
        self.layout.addWidget(note)

    def _init_log_area(self):
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #0f131a; color: white; border: 1px solid #2d3748; border-radius: 8px; font-family: Courier New; font-size: 12px;")
        self.layout.addWidget(self.log_area)
        self.log("System ready...")

    def refresh_ports(self):
        self.combo_ports.clear()
        self.combo_ports.addItem("Select COM Port", None)
        ports = PortScanner.get_available_ports()
        for p in ports:
            self.combo_ports.addItem(f"{p['port']} - {p['description']}", p['port'])

    def check_ports(self):
        new_ports = PortScanner.get_available_ports()
        current_port_data = self.combo_ports.currentData()
        
        # Get current items in combo
        current_items = []
        for i in range(1, self.combo_ports.count()): # Skip index 0 "Select COM Port"
            current_items.append(self.combo_ports.itemData(i))
            
        new_port_ids = [p['port'] for p in new_ports]
        
        # Check if lists match
        if set(current_items) != set(new_port_ids):
            self.combo_ports.blockSignals(True)
            self.combo_ports.clear()
            self.combo_ports.addItem("Select COM Port", None)
            for p in new_ports:
                self.combo_ports.addItem(f"{p['port']} - {p['description']}", p['port'])
            
            # Restore selection if possible
            index = self.combo_ports.findData(current_port_data)
            if index >= 0:
                self.combo_ports.setCurrentIndex(index)
            else:
                self.combo_ports.setCurrentIndex(0)
                
            self.combo_ports.blockSignals(False)
            
            # If the selected port is gone, we need to handle that manually since we blocked signals
            if index == -1 and current_port_data is not None:
                self.on_port_changed()

    def on_port_changed(self):
        port = self.combo_ports.currentData()
        if port:
            self.status_dot.setStyleSheet("background-color: #48bb78; border-radius: 6px;")
            self.status_text.setText(f"Connected to {port}")
            self.status_text.setStyleSheet("color: #48bb78; font-size: 12px;")
            self.log(f"Connected to {port}", "SUCCESS")
        else:
            self.status_dot.setStyleSheet("background-color: #4a5568; border-radius: 6px;")
            self.status_text.setText("Not connected")
            self.status_text.setStyleSheet("color: #718096; font-size: 12px;")
        self.validate_form()

    def validate_form(self):
        port = self.combo_ports.currentData()
        sid_text = self.input_slave_id.text()
        
        valid_port = port is not None
        valid_sid, _ = Validator.validate_slave_id(sid_text)
        
        self.btn_flash.setEnabled(valid_port and valid_sid)

    def log(self, message, level="INFO"):
        color = "#e2e8f0"
        if "success" in level.lower(): color = "#48bb78"
        if "error" in level.lower() or "fail" in level.lower(): color = "#f56565"
        
        self.log_area.append(f'<span style="color:{color}">[{level}] {message}</span>')
        # Also log to file/console via logger
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)

    def start_flash(self):
        port = self.combo_ports.currentData()
        slave_id = int(self.input_slave_id.text())
        
        self.btn_flash.setEnabled(False)
        self.btn_flash.setText("Flashing...")
        self.log("Starting flash operation...")
        
        # Threading
        self.thread = QThread()
        self.worker = FlashWorker(port, slave_id)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_flash_finished)
        self.worker.progress.connect(self.on_flash_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    @Slot(str, int)
    def on_flash_progress(self, msg, pct):
        self.log(msg)

    @Slot(bool, str)
    def on_flash_finished(self, success, message):
        if success:
            self.log(message, "SUCCESS")
            self.btn_flash.setText("Flash Complete ✓")
        else:
            self.log(message, "ERROR")
            self.btn_flash.setText("Flash Failed")
        
        # Reset button after delay (simulated by timer or just manual reset logic)
        # For now, we leave it, user can change inputs to reset or we just re-enable:
        self.btn_flash.setEnabled(True)
        if not success:
             self.btn_flash.setText("Retry")
        else:
             self.btn_flash.setText("Set Slave ID")
        self.validate_form()
