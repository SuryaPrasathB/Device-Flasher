import time
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QCheckBox, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject

from app.modbus.modbus_client import ModbusClientWrapper
from app.utils.config import config
from app.utils.logger import logger

class OverallStatusWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(str)

    def __init__(self, port, status_states):
        super().__init__()
        self.port = port
        self.status_states = status_states  # List of 40 booleans (True=Pass, False=Fail)
        self.client = ModbusClientWrapper()

    def run(self):
        try:
            if not self.client.connect(self.port):
                self.finished.emit(False, "Failed to connect to COM port.")
                return

            self.progress.emit("Connected. Preparing overall status states...")

            # Pack 40 booleans into 3 integers
            status_1 = 0
            status_2 = 0
            status_3 = 0
            failed_slaves = []

            for i in range(40):
                if self.status_states[i]:
                    # Pass
                    if i < 16:
                        status_1 |= (1 << i)
                    elif i < 32:
                        status_2 |= (1 << (i - 16))
                    else:
                        status_3 |= (1 << (i - 32))
                else:
                    # Fail
                    failed_slaves.append(i + 1) # Slave IDs are 1-indexed

            reg_map = config.register_map
            addr_1 = reg_map.get("overall_status_1_address", 23)
            addr_2 = reg_map.get("overall_status_2_address", 24)
            addr_3 = reg_map.get("overall_status_3_address", 25)
            err_addr = reg_map.get("error_code_address", 26)
            test_type_addr = reg_map.get("test_type_address", 12)
            start_coil = reg_map.get("start_coil_address", 1)

            BROADCAST_ID = 0
            OVERALL_RESULT_DISPLAY = 777

            self.progress.emit("Broadcasting OVERALL_STATUS_1...")
            self.client.write_register(BROADCAST_ID, addr_1, status_1)
            time.sleep(0.05)

            self.progress.emit("Broadcasting OVERALL_STATUS_2...")
            self.client.write_register(BROADCAST_ID, addr_2, status_2)
            time.sleep(0.05)

            self.progress.emit("Broadcasting OVERALL_STATUS_3...")
            self.client.write_register(BROADCAST_ID, addr_3, status_3)
            time.sleep(0.05)

            # Assign random error codes to failed slaves individually
            if failed_slaves:
                self.progress.emit(f"Writing random error codes to {len(failed_slaves)} failed slaves...")
                for slave_id in failed_slaves:
                    # Bitmask for errors: 0x01 (LOE), 0x02 (STA), 0x04 (NLD), 0x08 (COMM)
                    random_err = random.randint(1, 15)
                    self.client.write_register(slave_id, err_addr, random_err)
                    time.sleep(0.05)

            self.progress.emit("Broadcasting TEST_TYPE (777)...")
            self.client.write_register(BROADCAST_ID, test_type_addr, OVERALL_RESULT_DISPLAY)
            time.sleep(0.05)

            self.progress.emit("Triggering START_TRIGGER_COIL...")
            self.client.write_coil(BROADCAST_ID, start_coil, True)
            time.sleep(0.05)

            self.finished.emit(True, "Successfully sent overall status tests.")

        except Exception as e:
            logger.error(f"OverallStatusWorker error: {e}")
            self.finished.emit(False, f"Error: {e}")
        finally:
            self.client.disconnect()


class OverallStatusTab(QWidget):
    log_message = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_port = None
        self.worker_thread = None
        self.worker = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("Overall Status Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e2e8f0;")
        layout.addWidget(title)

        desc = QLabel("Select Pass (Checked) or Fail (Unchecked) for each slave. LSB is Slave 1. Failed slaves will receive a random error code.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0aec0; font-size: 12px;")
        layout.addWidget(desc)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_pass_all = QPushButton("Pass All")
        self.btn_pass_all.clicked.connect(self._pass_all)
        self.btn_pass_all.setStyleSheet(self._btn_style())
        btn_layout.addWidget(self.btn_pass_all)

        self.btn_fail_all = QPushButton("Fail All")
        self.btn_fail_all.clicked.connect(self._fail_all)
        self.btn_fail_all.setStyleSheet(self._btn_style())
        btn_layout.addWidget(self.btn_fail_all)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Grid of Checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #4a5568; background-color: #1a202c; }")
        
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)

        self.checkboxes = []
        for i in range(40):
            cb = QCheckBox(f"Slave {i + 1}")
            cb.setStyleSheet("""
                QCheckBox { color: white; font-size: 12px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
            """)
            cb.setChecked(True) # Default all Pass
            self.checkboxes.append(cb)
            
            row = i // 4
            col = i % 4
            grid_layout.addWidget(cb, row, col)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        # Action Layout
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_send = QPushButton("Send Overall Status")
        self.btn_send.setMinimumHeight(40)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #3182ce;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #2b6cb0; }
            QPushButton:disabled { background-color: #4a5568; color: #a0aec0; }
        """)
        self.btn_send.clicked.connect(self._on_send_clicked)
        action_layout.addWidget(self.btn_send)

        layout.addLayout(action_layout)

    def _btn_style(self):
        return """
            QPushButton {
                background-color: #4a5568;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #2d3748; }
        """

    def _pass_all(self):
        for cb in self.checkboxes:
            cb.setChecked(True)

    def _fail_all(self):
        for cb in self.checkboxes:
            cb.setChecked(False)

    def set_current_port(self, port):
        self.current_port = port
        self.btn_send.setEnabled(bool(port))

    def _on_send_clicked(self):
        if not self.current_port:
            QMessageBox.warning(self, "Error", "Please select a COM port first.")
            return

        states = [cb.isChecked() for cb in self.checkboxes]
        
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Sending...")
        self.log_message.emit("Starting broadcast of Overall Status...", "INFO")

        self.worker_thread = QThread()
        self.worker = OverallStatusWorker(self.current_port, states)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda msg: self.log_message.emit(msg, "INFO"))
        self.worker.finished.connect(self._on_worker_finished)
        
        # Cleanup
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    @Slot(bool, str)
    def _on_worker_finished(self, success, message):
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Send Overall Status")
        
        level = "SUCCESS" if success else "ERROR"
        self.log_message.emit(message, level)

        if not success:
            QMessageBox.critical(self, "Failure", message)
