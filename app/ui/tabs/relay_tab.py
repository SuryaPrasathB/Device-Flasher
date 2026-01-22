from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QObject
from app.utils.helpers import get_resource_path
from app.utils.config import config
from app.modbus.modbus_client import ModbusClientWrapper

class RelayTab(QWidget):
    """
    Tab 3: Relay Operations
    """

    log_message = Signal(str, str) # message, level

    def __init__(self):
        super().__init__()
        self.modbus_client = None
        self.worker_thread = None
        self.worker = None
        self.current_port = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Target Device Section
        target_group = QGroupBox("Target Device")
        target_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        target_layout = QHBoxLayout(target_group)

        self.input_slave_id = QSpinBox()
        self.input_slave_id.setRange(1, 247)
        self.input_slave_id.setValue(1)
        self.input_slave_id.setPrefix("ID: ")
        self.input_slave_id.setFixedWidth(100)
        self._style_spinbox(self.input_slave_id)

        target_layout.addWidget(QLabel("Slave ID:"))
        target_layout.addWidget(self.input_slave_id)
        target_layout.addStretch()

        layout.addWidget(target_group)

        # 2. Relays Section
        relay_group = QGroupBox("Relay Control")
        relay_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        relay_layout = QVBoxLayout(relay_group)

        self.relay_checkboxes = []

        # Grid layout for relays (2 columns)
        grid_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        for i in range(1, 9):
            cb = QCheckBox(f"Relay {i}")
            cb.setStyleSheet("""
                QCheckBox { spacing: 8px; font-size: 14px; }
                QCheckBox::indicator { width: 20px; height: 20px; }
            """)
            self.relay_checkboxes.append(cb)
            if i <= 4:
                col1.addWidget(cb)
            else:
                col2.addWidget(cb)

        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        relay_layout.addLayout(grid_layout)

        layout.addWidget(relay_group)

        # 3. Actions
        self.btn_update = QPushButton("UPDATE RELAYS")
        self.btn_update.setFixedHeight(40)
        self.btn_update.setStyleSheet(self._get_btn_style("#2b6cb0", "#2c5282"))
        self.btn_update.clicked.connect(self.on_update_clicked)

        layout.addWidget(self.btn_update)
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
        self.btn_update.setEnabled(port is not None)

    def on_update_clicked(self):
        if not self.current_port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        slave_id = self.input_slave_id.value()
        relay_states = [cb.isChecked() for cb in self.relay_checkboxes]

        self.run_worker(self.current_port, slave_id, relay_states)

    def run_worker(self, port, slave_id, states):
        self.btn_update.setEnabled(False)

        self.thread = QThread()
        self.worker = RelayWorker(port, slave_id, states)
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


class RelayWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(str, int)

    def __init__(self, port, slave_id, states):
        super().__init__()
        self.port = port
        self.slave_id = slave_id
        self.states = states
        self.client = ModbusClientWrapper()

    def run(self):
        try:
            if not self.client.connect(self.port):
                self.finished.emit(False, "Failed to connect.")
                return

            self.progress.emit("Updating Relays...", 10)

            # Write each relay state
            for i, state in enumerate(self.states):
                relay_num = i + 1
                addr_key = f"relay_{relay_num}_coil"
                addr = config.register_map.get(addr_key)

                if addr is None:
                    # Fallback or error?
                    # Assuming config is populated correctly.
                    continue

                success, msg = self.client.write_coil(self.slave_id, addr, state)
                if not success:
                    raise Exception(f"Failed to set Relay {relay_num}: {msg}")

            # Trigger Update
            self.progress.emit("Triggering Update...", 80)
            update_addr = config.register_map.get("relay_update_coil")
            if update_addr:
                 success, msg = self.client.write_coil(self.slave_id, update_addr, True)
                 if not success:
                     raise Exception(f"Failed to trigger update: {msg}")

            self.finished.emit(True, "Relays Updated Successfully")

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            self.client.disconnect()
