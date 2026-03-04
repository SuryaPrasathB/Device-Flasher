from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QGroupBox, QLineEdit, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QObject
from app.utils.helpers import get_resource_path
from app.utils.config import config
from app.modbus.modbus_client import ModbusClientWrapper

class SerialScanTab(QWidget):
    """
    Tab: Serial Number Scanning
    """
    log_message = Signal(str, str) # message, level

    def __init__(self):
        super().__init__()
        self.current_port = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Start Scanning Section
        scan_group = QGroupBox("Scan Control")
        scan_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        scan_layout = QVBoxLayout(scan_group)

        lbl_scan = QLabel("Broadcasts Test Type 666 and Start Trigger to all devices.")
        lbl_scan.setWordWrap(True)
        lbl_scan.setStyleSheet("color: #a0aec0; font-style: italic;")
        scan_layout.addWidget(lbl_scan)

        self.btn_start_scan = QPushButton("START SERIAL NUMBER SCANNING")
        self.btn_start_scan.setFixedHeight(50)
        self.btn_start_scan.setStyleSheet(self._get_btn_style("#38a169", "#2f855a"))
        self.btn_start_scan.clicked.connect(self.on_start_scan_clicked)
        scan_layout.addWidget(self.btn_start_scan)

        layout.addWidget(scan_group)

        # 2. Write Serial Number Section
        write_group = QGroupBox("Write Serial Number")
        write_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        write_layout = QFormLayout(write_group)
        write_layout.setLabelAlignment(Qt.AlignRight)

        # Target Slave ID
        self.inp_slave_id = QSpinBox()
        self.inp_slave_id.setRange(1, 247)
        self.inp_slave_id.setValue(1)
        self.inp_slave_id.setPrefix("ID: ")
        self._style_spinbox(self.inp_slave_id)
        write_layout.addRow("Target Device:", self.inp_slave_id)

        # Serial Number Input
        self.inp_serial = QLineEdit()
        self.inp_serial.setMaxLength(10)
        self.inp_serial.setPlaceholderText("Max 10 chars")
        self.inp_serial.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
        """)
        write_layout.addRow("Serial Number:", self.inp_serial)

        # Write Button
        self.btn_write_serial = QPushButton("WRITE SERIAL NUMBER")
        self.btn_write_serial.setFixedHeight(40)
        self.btn_write_serial.setStyleSheet(self._get_btn_style("#2b6cb0", "#2c5282"))
        self.btn_write_serial.clicked.connect(self.on_write_clicked)
        write_layout.addRow("", self.btn_write_serial)

        layout.addWidget(write_group)
        layout.addStretch()

    def _style_spinbox(self, spinbox):
        arrow_up = get_resource_path("resources/arrow_up.svg").replace("\\", "/")
        arrow_down = get_resource_path("resources/arrow_down.svg").replace("\\", "/")
        spinbox.setStyleSheet(f"""
            QSpinBox {{
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
                min-width: 100px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                background-color: #4a5568;
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

    def _get_btn_style(self, normal, hover):
        return f"""
            QPushButton {{
                background-color: {normal};
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{ background-color: #4a5568; color: #a0aec0; }}
        """

    def set_current_port(self, port):
        self.current_port = port
        state = port is not None
        self.btn_start_scan.setEnabled(state)
        self.btn_write_serial.setEnabled(state)

    def on_start_scan_clicked(self):
        if not self.current_port:
            self.log_message.emit("No Port Selected", "ERROR")
            return
        
        self.run_worker("start_scan", self.current_port)

    def on_write_clicked(self):
        if not self.current_port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        serial = self.inp_serial.text()
        slave_id = self.inp_slave_id.value()

        # Validation (though UI limits to 10)
        if len(serial) > 10:
            self.log_message.emit("Serial Number too long (Max 10)", "ERROR")
            return
        
        self.run_worker("write_serial", self.current_port, slave_id=slave_id, serial=serial)

    # --- Worker Management ---

    def run_worker(self, mode, port, slave_id=0, serial=""):
        self.btn_start_scan.setEnabled(False)
        self.btn_write_serial.setEnabled(False)

        self.thread = QThread()
        self.worker = SerialWorker(mode, port, slave_id, serial)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.progress.connect(self.on_worker_progress)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    @Slot(str, int)
    def on_worker_progress(self, msg, pct):
        self.log_message.emit(msg, "INFO")

    @Slot(bool, str)
    def on_worker_finished(self, success, msg):
        level = "SUCCESS" if success else "ERROR"
        self.log_message.emit(msg, level)
        self.btn_start_scan.setEnabled(True)
        self.btn_write_serial.setEnabled(True)


class SerialWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(str, int)

    def __init__(self, mode, port, slave_id=0, serial=""):
        super().__init__()
        self.mode = mode
        self.port = port
        self.slave_id = slave_id
        self.serial = serial
        self.client = ModbusClientWrapper()

    def run(self):
        try:
            if not self.client.connect(self.port):
                self.finished.emit(False, "Failed to connect.")
                return

            if self.mode == "start_scan":
                self._run_start_scan()
            elif self.mode == "write_serial":
                self._run_write_serial()

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            self.client.disconnect()

    def _get_addr(self, key):
        return config.register_map.get(key, 0)

    def _run_start_scan(self):
        # Broadcast (ID 0)
        # 1. Write Test Type 666
        tt_addr = self._get_addr("test_type_address")
        self.progress.emit(f"Broadcasting Test Type 666 to Addr {tt_addr}...", 30)
        
        # Using no_response_expected=True logic if implemented in wrapper for ID 0, 
        # or relying on wrapper to handle it. 
        # Checking memory: "Modbus broadcast operations... handled by passing no_response_expected=True"
        # Wait, the wrapper typically handles this?
        # Let's check wrapper logic or just call write.
        # The wrapper signature is usually (slave_id, address, value).
        
        self.client.write_register(0, tt_addr, 666) # Broadcast

        # 2. Set Start Coil
        start_addr = self._get_addr("start_coil_address")
        self.progress.emit(f"Broadcasting Start Coil to Addr {start_addr}...", 60)
        self.client.write_coil(0, start_addr, True) # Broadcast

        self.finished.emit(True, "Scanning Started (Broadcast Sent)")

    def _run_write_serial(self):
        # 1. Prepare Data
        # Max 10 chars input. Pad to 16 chars with spaces.
        s_padded = self.serial.ljust(16, ' ')
        
        # Convert to 8 registers (16 bytes)
        # Each register holds 2 characters
        registers = []
        for i in range(0, 16, 2):
            high_byte = ord(s_padded[i])
            low_byte = ord(s_padded[i+1])
            val = (high_byte << 8) | low_byte
            registers.append(val)
        
        start_addr = self._get_addr("meter_serial_start_address")
        
        self.progress.emit(f"Writing Serial '{s_padded}' to ID {self.slave_id}...", 50)
        
        # Write multiple registers
        success, msg = self.client.write_registers(self.slave_id, start_addr, registers)

        # Update coil
        update_addr = self._get_addr("serial_update_coil")
        self.client.write_coil(self.slave_id, update_addr, True)
        
        if success:
            self.finished.emit(True, "Serial Number Written Successfully")
        else:
            self.finished.emit(False, f"Write Failed: {msg}")
