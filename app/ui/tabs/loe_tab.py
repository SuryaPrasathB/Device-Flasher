from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QAbstractSpinBox, QCheckBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QObject
from app.utils.helpers import get_resource_path
from app.utils.config import config
from app.modbus.modbus_client import ModbusClientWrapper
import time

class LOETab(QWidget):
    """
    Tab 2: LOE (Line of Energy) Testing Screen
    """

    # Signals for logging to main window
    log_message = Signal(str, str) # message, level

    def __init__(self):
        super().__init__()
        self.modbus_client = None # Will be passed or created?
        # Ideally, we should reuse the connection from main window or create ad-hoc.
        # Given the requirements say "Uses entered Slave ID", it implies we need access to the Modbus Client.
        # We'll instantiate a wrapper here or accept one.
        # Since MainWindow manages the Port, MainWindow should probably pass the client or we use a shared singleton approach.
        # However, the current architecture passes PortScanner but handles Client in `FlashWorker`.
        # We need a `TesterWorker` or similar.

        self.worker_thread = None
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header Section - Slave ID Control
        header_group = QGroupBox("Target Device")
        header_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        header_layout = QHBoxLayout(header_group)

        self.input_slave_id = QSpinBox()
        self.input_slave_id.setRange(1, 247)
        self.input_slave_id.setValue(1)
        self.input_slave_id.setPrefix("ID: ")
        self.input_slave_id.setFixedWidth(100)
        self._style_spinbox(self.input_slave_id)

        self.toggle_broadcast = QCheckBox("Broadcast Mode (ID 0)")
        self.toggle_broadcast.setStyleSheet("""
            QCheckBox { spacing: 5px; color: white; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        self.toggle_broadcast.toggled.connect(self.on_broadcast_toggled)

        header_layout.addWidget(self.input_slave_id)
        header_layout.addWidget(self.toggle_broadcast)
        header_layout.addStretch()

        layout.addWidget(header_group)

        # 2. Parameter Input Section
        param_group = QGroupBox("Parameters")
        param_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        form_layout = QFormLayout(param_group)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Meter Constant (16-bit)
        self.input_meter_const = QSpinBox()
        self.input_meter_const.setRange(0, 65535)
        self._style_spinbox(self.input_meter_const)
        form_layout.addRow("Meter Constant:", self.input_meter_const)

        # Reference Constant (32-bit)
        # QSpinBox normally handles int32 (approx +- 2 billion).
        self.input_ref_const = QSpinBox()
        self.input_ref_const.setRange(0, 2147483647) # Max signed 32-bit, usually unsigned is used but let's stick to safe positive range for constants
        self._style_spinbox(self.input_ref_const)
        form_layout.addRow("Reference Constant:", self.input_ref_const)

        # No. of Test Pulses (16-bit)
        self.input_pulses = QSpinBox()
        self.input_pulses.setRange(0, 65535)
        self.input_pulses.setValue(10) # Default
        self._style_spinbox(self.input_pulses)
        form_layout.addRow("No. Test Pulses:", self.input_pulses)

        layout.addWidget(param_group)

        # 3. UPDATE Button
        self.btn_update = QPushButton("UPDATE PARAMETERS")
        self.btn_update.setFixedHeight(40)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:pressed { background-color: #2a4365; }
            QPushButton:disabled { background-color: #4a5568; color: #a0aec0; }
        """)
        self.btn_update.clicked.connect(self.on_update_clicked)
        layout.addWidget(self.btn_update)

        layout.addStretch()

        # 4. START Button
        self.btn_start = QPushButton("START TEST")
        self.btn_start.setFixedHeight(60)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:pressed { background-color: #276749; }
            QPushButton:disabled { background-color: #4a5568; color: #a0aec0; }
        """)
        self.btn_start.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.btn_start)

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
                min-width: 120px;
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

    def on_broadcast_toggled(self, checked):
        if checked:
            self.input_slave_id.setEnabled(False)
            self.input_slave_id.setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748;")
        else:
            self.input_slave_id.setEnabled(True)
            self._style_spinbox(self.input_slave_id)

    def get_target_id(self):
        return 0 if self.toggle_broadcast.isChecked() else self.input_slave_id.value()

    def set_port_connected(self, connected):
        self.btn_update.setEnabled(connected)
        self.btn_start.setEnabled(connected)
        self.setEnabled(connected) # Disable whole tab if disconnected? Or just buttons.
        # Requirement says "Only LOE tab should be functional". Disabling buttons is safer.

    def on_update_clicked(self):
        # Gather data
        target_id = self.get_target_id()
        meter_c = self.input_meter_const.value()
        ref_c = self.input_ref_const.value()
        pulses = self.input_pulses.value()

        # We need the current port from MainWindow.
        # Ideally passed in. For now we assume a way to run this.
        # We will emit a signal or start a worker directly if we have the port.
        # Let's use the 'worker' pattern similar to FlashWorker but logic is here or in a separate class.

        # We need the port name.
        port = self.parent_port_name()
        if not port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        self.run_worker("update", port, target_id, meter_c, ref_c, pulses)

    def on_start_clicked(self):
        target_id = self.get_target_id()
        port = self.parent_port_name()
        if not port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        self.run_worker("start", port, target_id)

    def parent_port_name(self):
        # This is a bit tight-coupled, but we need the port.
        # MainWindow sets this.
        # Alternatively, MainWindow calls `set_port` on us.
        if hasattr(self, 'current_port'):
            return self.current_port
        return None

    def set_current_port(self, port):
        self.current_port = port
        self.set_port_connected(port is not None)

    def run_worker(self, mode, port, slave_id, *args):
        # Prevent double click
        self.btn_update.setEnabled(False)
        self.btn_start.setEnabled(False)

        self.thread = QThread()
        self.worker = LOEWorker(mode, port, slave_id, *args)
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
        self.btn_update.setEnabled(True)
        self.btn_start.setEnabled(True)


class LOEWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(str, int)

    def __init__(self, mode, port, slave_id, *args):
        super().__init__()
        self.mode = mode
        self.port = port
        self.slave_id = slave_id
        self.args = args
        self.client = ModbusClientWrapper()

    def run(self):
        try:
            self.progress.emit(f"Connecting to {self.port}...", 10)
            if not self.client.connect(self.port):
                self.finished.emit(False, "Failed to connect.")
                return

            if self.mode == "update":
                self._run_update()
            elif self.mode == "start":
                self._run_start()

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            self.client.disconnect()

    def _run_update(self):
        meter_c, ref_c, pulses = self.args

        # Load addresses
        reg_map = config.register_map
        addr_meter = reg_map.get("meter_constant_address", 13)
        addr_ref = reg_map.get("reference_constant_address", 6)
        addr_pulses = reg_map.get("test_pulses_address", 14)

        is_broadcast = (self.slave_id == 0)
        retries = 3 if is_broadcast else 1

        # Write Loop
        # If broadcast, we write multiple times and ignore specific errors usually,
        # but ModbusClientWrapper returns False on error.

        # 1. Meter Constant (16-bit)
        self.progress.emit(f"Writing Meter Constant: {meter_c}", 20)
        if not self._write_with_retry(self.client.write_register, retries, not is_broadcast, self.slave_id, addr_meter, meter_c):
             if not is_broadcast:
                 self.finished.emit(False, "Failed to write Meter Constant")
                 return

        # 2. Reference Constant (32-bit)
        self.progress.emit(f"Writing Reference Constant: {ref_c}", 50)
        if not self._write_with_retry(self.client.write_int32, retries, not is_broadcast, self.slave_id, addr_ref, ref_c):
             if not is_broadcast:
                 self.finished.emit(False, "Failed to write Reference Constant")
                 return

        # 3. Pulses (16-bit)
        self.progress.emit(f"Writing Test Pulses: {pulses}", 80)
        if not self._write_with_retry(self.client.write_register, retries, not is_broadcast, self.slave_id, addr_pulses, pulses):
             if not is_broadcast:
                 self.finished.emit(False, "Failed to write Test Pulses")
                 return

        self.progress.emit("Update complete", 100)
        self.finished.emit(True, "Parameters Updated Successfully")

    def _run_start(self):
        reg_map = config.register_map
        addr_start = reg_map.get("start_coil_address", 1)

        is_broadcast = (self.slave_id == 0)
        retries = 3 if is_broadcast else 1

        self.progress.emit("Sending START Command...", 50)
        if not self._write_with_retry(self.client.write_coil, retries, not is_broadcast, self.slave_id, addr_start, True):
             if not is_broadcast:
                 self.finished.emit(False, "Failed to send Start Command")
                 return

        self.progress.emit("Command Sent.", 100)
        self.finished.emit(True, "Test Started")

    def _write_with_retry(self, func, retries, stop_on_success, *args):
        # func(slave_id, addr, value)
        success_at_least_once = False
        for i in range(retries):
            success, msg = func(*args)
            if success:
                success_at_least_once = True
                if stop_on_success:
                    return True
            time.sleep(0.05)

        return success_at_least_once
