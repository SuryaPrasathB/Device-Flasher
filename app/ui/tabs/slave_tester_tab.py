import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QObject
from app.utils.helpers import get_resource_path
from app.modbus.modbus_client import ModbusClientWrapper

class SlaveTesterTab(QWidget):
    """
    Tab: Slave Tester
    Iterates through a range of Slave IDs and checks communication.
    """

    log_message = Signal(str, str) # message, level

    def __init__(self):
        super().__init__()
        self.current_port = None
        self.is_running = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Configuration Group
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; color: white; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        config_layout = QHBoxLayout(config_group)

        # From ID
        config_layout.addWidget(QLabel("From ID:"))
        self.spin_from = self._create_spinbox(1)
        config_layout.addWidget(self.spin_from)

        # To ID
        config_layout.addWidget(QLabel("To ID:"))
        self.spin_to = self._create_spinbox(40)
        config_layout.addWidget(self.spin_to)

        config_layout.addStretch()
        layout.addWidget(config_group)

        # 2. Action Button
        self.btn_test = QPushButton("TEST RANGE")
        self.btn_test.setFixedHeight(45)
        self.btn_test.setStyleSheet(self._get_btn_style("#4299e1", "#3182ce"))
        self.btn_test.clicked.connect(self.on_test_clicked)
        self.btn_test.setEnabled(False) # Disabled until port selected
        layout.addWidget(self.btn_test)

        # 3. Results Area
        layout.addWidget(QLabel("Results:"))
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setStyleSheet("background-color: #0f131a; color: white; border: 1px solid #2d3748; border-radius: 4px; font-family: Courier New; font-size: 12px;")
        layout.addWidget(self.results_area)

    def _create_spinbox(self, val):
        sb = QSpinBox()
        sb.setRange(1, 247)
        sb.setValue(val)
        arrow_up = get_resource_path("resources/arrow_up.svg").replace("\\", "/")
        arrow_down = get_resource_path("resources/arrow_down.svg").replace("\\", "/")
        sb.setStyleSheet(f"""
            QSpinBox {{
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
                min-width: 80px;
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
        return sb

    def _get_btn_style(self, normal, hover):
        return f"""
            QPushButton {{
                background-color: {normal};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{ background-color: #4a5568; color: #a0aec0; }}
        """

    def set_current_port(self, port):
        self.current_port = port
        self.btn_test.setEnabled(port is not None)
        if not port:
            self.results_area.append('<span style="color:#f56565">[INFO] Port disconnected.</span>')

    def on_test_clicked(self):
        if not self.current_port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        start_id = self.spin_from.value()
        end_id = self.spin_to.value()

        if start_id > end_id:
            self.results_area.append('<span style="color:#f56565">Error: "From ID" must be less than or equal to "To ID"</span>')
            return

        self.results_area.clear()
        self.results_area.append(f'<span style="color:#cbd5e0">Starting test from ID {start_id} to {end_id}...</span>')
        self.btn_test.setEnabled(False)
        self.btn_test.setText("TESTING...")

        self.thread = QThread()
        self.worker = SlaveTestWorker(self.current_port, start_id, end_id)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.result.connect(self.on_worker_result)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    @Slot(str, str)
    def on_worker_result(self, slave_id_str, status):
        color = "#48bb78" if status == "PASS" else "#f56565"
        self.results_area.append(f'ID {slave_id_str}: <span style="color:{color}; font-weight:bold;">{status}</span>')

    @Slot(str)
    def on_worker_progress(self, msg):
        self.results_area.append(f'<span style="color:#cbd5e0">{msg}</span>')

    @Slot()
    def on_worker_finished(self):
        self.results_area.append('<span style="color:#cbd5e0">Test Complete.</span>')
        self.btn_test.setText("TEST RANGE")
        self.btn_test.setEnabled(True)


class SlaveTestWorker(QObject):
    finished = Signal()
    progress = Signal(str)
    result = Signal(str, str) # slave_id, status

    def __init__(self, port, start_id, end_id):
        super().__init__()
        self.port = port
        self.start_id = start_id
        self.end_id = end_id
        self.client = ModbusClientWrapper()

    def run(self):
        if not self.client.connect(self.port):
            self.progress.emit("Failed to connect to port.")
            self.finished.emit()
            return

        try:
            # We will use register 22 (Slave ID Register) as the check
            # This is based on config.json: "slave_id_register_address": 22
            check_addr = 22

            for sid in range(self.start_id, self.end_id + 1):
                # Small delay to prevent bus flooding if needed, though Modbus is synchronous usually

                # We read 1 register
                regs, err = self.client.read_holding_registers(sid, check_addr, 1)

                if not err and regs:
                    self.result.emit(str(sid), "PASS")
                else:
                    self.result.emit(str(sid), "FAIL")

                time.sleep(1)
                

        except Exception as e:
            self.progress.emit(f"Error: {e}")
        finally:
            self.client.disconnect()
            self.finished.emit()
