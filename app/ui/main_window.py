import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtGui import QIcon, QFont, QColor

from app.modbus.port_scanner import PortScanner
from app.core.validation import Validator
from app.ui.worker import FlashWorker
from app.utils.logger import logger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Device Flasher")
        self.resize(500, 600)
        
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

        # Load Ports
        self.refresh_ports()

    def _init_header(self):
        header_layout = QVBoxLayout()
        title = QLabel("Device Flasher")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d3748;")
        
        subtitle = QLabel("Flash Slave ID to Embedded Controller")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #718096;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.layout.addLayout(header_layout)

    def _init_form(self):
        # COM Port
        self.layout.addWidget(QLabel("COM Port"))
        self.combo_ports = QComboBox()
        self.combo_ports.addItem("Select COM Port", None)
        self.combo_ports.currentIndexChanged.connect(self.on_port_changed)
        self.layout.addWidget(self.combo_ports)
        
        # Status Indicator
        self.status_layout = QHBoxLayout()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background-color: #cbd5e0; border-radius: 6px;")
        self.status_text = QLabel("Not connected")
        self.status_text.setStyleSheet("color: #718096; font-size: 12px;")
        self.status_layout.addWidget(self.status_dot)
        self.status_layout.addWidget(self.status_text)
        self.status_layout.addStretch()
        self.layout.addLayout(self.status_layout)
        
        # Slave ID
        self.layout.addWidget(QLabel("Slave ID"))
        self.input_slave_id = QLineEdit()
        self.input_slave_id.setPlaceholderText("Enter Slave ID (e.g., 1-247)")
        self.input_slave_id.textChanged.connect(self.validate_form)
        self.layout.addWidget(self.input_slave_id)
        
        # Flash Button
        self.btn_flash = QPushButton("Flash Device")
        self.btn_flash.setFixedHeight(45)
        self.btn_flash.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a67d8;
            }
            QPushButton:disabled {
                background-color: #cbd5e0;
            }
        """)
        self.btn_flash.clicked.connect(self.start_flash)
        self.btn_flash.setEnabled(False)
        self.layout.addWidget(self.btn_flash)
        
        # Note
        note = QLabel("Note: Ensure device is connected. Valid ID: 1-247")
        note.setStyleSheet("background-color: #edf2f7; color: #4a5568; padding: 10px; border-radius: 4px; font-size: 12px;")
        self.layout.addWidget(note)

    def _init_log_area(self):
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f7fafc; border-radius: 8px; font-family: Courier New; font-size: 12px;")
        self.layout.addWidget(self.log_area)
        self.log("System ready...")

    def refresh_ports(self):
        self.combo_ports.clear()
        self.combo_ports.addItem("Select COM Port", None)
        ports = PortScanner.get_available_ports()
        for p in ports:
            self.combo_ports.addItem(f"{p['port']} - {p['description']}", p['port'])

    def on_port_changed(self):
        port = self.combo_ports.currentData()
        if port:
            self.status_dot.setStyleSheet("background-color: #48bb78; border-radius: 6px;")
            self.status_text.setText(f"Selected {port}")
            self.log(f"Selected Port: {port}")
        else:
            self.status_dot.setStyleSheet("background-color: #cbd5e0; border-radius: 6px;")
            self.status_text.setText("Not connected")
        self.validate_form()

    def validate_form(self):
        port = self.combo_ports.currentData()
        sid_text = self.input_slave_id.text()
        
        valid_port = port is not None
        valid_sid, _ = Validator.validate_slave_id(sid_text)
        
        self.btn_flash.setEnabled(valid_port and valid_sid)

    def log(self, message, level="INFO"):
        color = "#2d3748"
        if "success" in level.lower(): color = "#38a169"
        if "error" in level.lower() or "fail" in level.lower(): color = "#e53e3e"
        
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
             self.btn_flash.setText("Retry Flash")
        else:
             self.btn_flash.setText("Flash Device")
        self.validate_form()
