import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QCheckBox, QScrollArea, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject

from app.modbus.modbus_client import ModbusClientWrapper
from app.utils.config import config
from app.utils.logger import logger

class ActiveSlavesWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(str)

    def __init__(self, port, active_states):
        super().__init__()
        self.port = port
        self.active_states = active_states  # List of 40 booleans (True=Active, False=Inactive)
        self.client = ModbusClientWrapper()

    def run(self):
        try:
            if not self.client.connect(self.port):
                self.finished.emit(False, "Failed to connect to COM port.")
                return

            self.progress.emit("Connected. Preparing active slave states...")

            # Pack 40 booleans into 3 integers
            active_1 = 0
            active_2 = 0
            active_3 = 0

            for i in range(40):
                if self.active_states[i]:
                    if i < 16:
                        active_1 |= (1 << i)
                    elif i < 32:
                        active_2 |= (1 << (i - 16))
                    else:
                        active_3 |= (1 << (i - 32))

            reg_map = config.register_map
            addr_1 = reg_map.get("active_slaves_1_address", 35)
            addr_2 = reg_map.get("active_slaves_2_address", 36)
            addr_3 = reg_map.get("active_slaves_3_address", 37)
            update_coil = reg_map.get("active_update_coil", 17)

            BROADCAST_ID = 0

            self.progress.emit("Broadcasting ACTIVE_SLAVES_1...")
            self.client.write_register(BROADCAST_ID, addr_1, active_1)
            time.sleep(0.05)

            self.progress.emit("Broadcasting ACTIVE_SLAVES_2...")
            self.client.write_register(BROADCAST_ID, addr_2, active_2)
            time.sleep(0.05)

            self.progress.emit("Broadcasting ACTIVE_SLAVES_3...")
            self.client.write_register(BROADCAST_ID, addr_3, active_3)
            time.sleep(0.05)

            self.progress.emit("Triggering ACTIVE_UPDATE_COIL...")
            self.client.write_coil(BROADCAST_ID, update_coil, True)
            time.sleep(0.05)

            self.finished.emit(True, "Successfully updated active slave states.")

        except Exception as e:
            logger.error(f"ActiveSlavesWorker error: {e}")
            self.finished.emit(False, f"Error: {e}")
        finally:
            self.client.disconnect()


class ActiveSlavesTab(QWidget):
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
        title = QLabel("Active/Inactive Slaves Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e2e8f0;")
        layout.addWidget(title)

        desc = QLabel("Select the slaves to mark as active. LSB is Slave 1. Changes are broadcast to all slaves.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0aec0; font-size: 12px;")
        layout.addWidget(desc)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_select_all.setStyleSheet(self._btn_style())
        btn_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        self.btn_deselect_all.setStyleSheet(self._btn_style())
        btn_layout.addWidget(self.btn_deselect_all)

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
            cb.setChecked(True) # Default all active
            self.checkboxes.append(cb)
            
            row = i // 4
            col = i % 4
            grid_layout.addWidget(cb, row, col)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        # Action Layout
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_send = QPushButton("Send Active States")
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

    def _select_all(self):
        for cb in self.checkboxes:
            cb.setChecked(True)

    def _deselect_all(self):
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
        self.log_message.emit("Starting broadcast of Active Slave states...", "INFO")

        self.worker_thread = QThread()
        self.worker = ActiveSlavesWorker(self.current_port, states)
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
        self.btn_send.setText("Send Active States")
        
        level = "SUCCESS" if success else "ERROR"
        self.log_message.emit(message, level)

        if not success:
            QMessageBox.critical(self, "Failure", message)
