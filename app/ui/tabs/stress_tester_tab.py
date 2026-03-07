import time
import struct
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QGroupBox, QFormLayout, QGridLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QObject
from app.utils.helpers import get_resource_path
from app.utils.config import config
from app.modbus.modbus_client import ModbusClientWrapper

class StressTesterTab(QWidget):
    """
    Tab: Stress Tester
    Continuously reads a specific register to test communication reliability.
    """

    log_message = Signal(str, str) # message, level

    def __init__(self):
        super().__init__()
        self.current_port = None
        self.is_running = False
        
        # Load config
        reg_map = config.get("register_map", default={})
        self.default_target_register = reg_map.get("error_address", 17)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Configuration Group
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; color: white; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        config_layout = QGridLayout(config_group)

        # Slave ID
        config_layout.addWidget(QLabel("Slave ID:"), 0, 0)
        self.spin_slave_id = self._create_spinbox(1, 1, 247)
        config_layout.addWidget(self.spin_slave_id, 0, 1)

        # Data Type
        config_layout.addWidget(QLabel("Data Type:"), 0, 2)
        self.combo_data_type = QComboBox()
        self.combo_data_type.addItems(["Integer (16-bit)", "Float (32-bit)", "Coil"])
        self.combo_data_type.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
                min-width: 100px;
            }
        """)
        config_layout.addWidget(self.combo_data_type, 0, 3)

        # Target Register
        config_layout.addWidget(QLabel("Target Register:"), 1, 0)
        self.spin_register = self._create_spinbox(self.default_target_register, 0, 65535)
        config_layout.addWidget(self.spin_register, 1, 1)

        # Delay
        config_layout.addWidget(QLabel("Delay (ms):"), 1, 2)
        self.spin_delay = self._create_spinbox(200, 0, 60000)
        config_layout.addWidget(self.spin_delay, 1, 3)

        layout.addWidget(config_group)

        # 2. Action Button
        self.btn_toggle = QPushButton("START STRESS TEST")
        self.btn_toggle.setFixedHeight(45)
        self.btn_toggle.setStyleSheet(self._get_btn_style("#48bb78", "#38a169"))
        self.btn_toggle.clicked.connect(self.on_toggle_clicked)
        self.btn_toggle.setEnabled(False) # Disabled until port selected
        layout.addWidget(self.btn_toggle)

        # 3. Stats Area
        stats_group = QGroupBox("Statistics")
        stats_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; color: white; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        stats_layout = QGridLayout(stats_group)
        
        # Labels
        self.lbl_total_hits = self._create_stat_label("0")
        self.lbl_success = self._create_stat_label("0", "#48bb78")
        self.lbl_failure = self._create_stat_label("0", "#f56565")
        self.lbl_failure_percent = self._create_stat_label("0.00%", "#f6ad55")
        self.lbl_error_value = self._create_stat_label("-", "#e2e8f0")

        stats_layout.addWidget(QLabel("Total Hit Count:"), 0, 0)
        stats_layout.addWidget(self.lbl_total_hits, 0, 1)

        stats_layout.addWidget(QLabel("Success Count:"), 0, 2)
        stats_layout.addWidget(self.lbl_success, 0, 3)

        stats_layout.addWidget(QLabel("Failure Count:"), 1, 0)
        stats_layout.addWidget(self.lbl_failure, 1, 1)

        stats_layout.addWidget(QLabel("Failure %:"), 1, 2)
        stats_layout.addWidget(self.lbl_failure_percent, 1, 3)

        stats_layout.addWidget(QLabel("Read Value:"), 2, 0)
        stats_layout.addWidget(self.lbl_error_value, 2, 1)

        layout.addWidget(stats_group)
        
        # 4. Snapshot Table
        self.snapshot_table = QTableWidget()
        self.snapshot_table.setColumnCount(5)
        self.snapshot_table.setHorizontalHeaderLabels(["Time", "Total Hits", "Success", "Failure", "Failure %"])
        self.snapshot_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.snapshot_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a202c;
                color: white;
                gridline-color: #4a5568;
                border: 1px solid #4a5568;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2d3748;
                color: white;
                padding: 4px;
                border: 1px solid #4a5568;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.snapshot_table)
        
        layout.addStretch()

    def _create_spinbox(self, val, min_val, max_val):
        sb = QSpinBox()
        sb.setRange(min_val, max_val)
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

    def _create_stat_label(self, text, color="#e2e8f0"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

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
        if not self.is_running:
            self.btn_toggle.setEnabled(port is not None)
            
        if not port and self.is_running:
            self.stop_test()
            self.log_message.emit("Port disconnected. Stress test stopped.", "ERROR")

    def on_toggle_clicked(self):
        if not self.is_running:
            self.start_test()
        else:
            self.stop_test()

    def start_test(self):
        if not self.current_port:
            self.log_message.emit("No Port Selected", "ERROR")
            return

        self.is_running = True
        self.btn_toggle.setText("STOP STRESS TEST")
        self.btn_toggle.setStyleSheet(self._get_btn_style("#e53e3e", "#c53030")) # Red style for STOP

        # Reset Stats
        self.lbl_total_hits.setText("0")
        self.lbl_success.setText("0")
        self.lbl_failure.setText("0")
        self.lbl_failure_percent.setText("0.00%")
        self.lbl_error_value.setText("-")

        # Get values
        slave_id = self.spin_slave_id.value()
        target_reg = self.spin_register.value()
        delay_ms = self.spin_delay.value()
        data_type = self.combo_data_type.currentText()

        self.log_message.emit(f"Starting stress test on ID {slave_id}, target {target_reg} ({data_type})...", "INFO")

        # Setup Thread and Worker
        self.thread = QThread()
        self.worker = StressTestWorker(self.current_port, slave_id, target_reg, delay_ms, data_type)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        
        self.worker.stats_updated.connect(self.on_stats_updated)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def stop_test(self):
        if not self.is_running: return
        self.log_message.emit("Stopping stress test...", "INFO")
        if hasattr(self, 'worker'):
            self.worker.stop()
        
        self.btn_toggle.setEnabled(False) # Disable momentarily until thread stops

    @Slot(int, int, int, str)
    def on_stats_updated(self, total, success, failure, val_str):
        self.lbl_total_hits.setText(str(total))
        self.lbl_success.setText(str(success))
        self.lbl_failure.setText(str(failure))
        
        fail_pct = (failure / total * 100.0) if total > 0 else 0.0
        self.lbl_failure_percent.setText(f"{fail_pct:.2f}%")
        
        self.lbl_error_value.setText(val_str)

    @Slot(str)
    def on_worker_progress(self, msg):
        self.log_message.emit(msg, "ERROR")

    @Slot()
    def on_worker_finished(self):
        self.is_running = False
        self.btn_toggle.setText("START STRESS TEST")
        self.btn_toggle.setStyleSheet(self._get_btn_style("#48bb78", "#38a169")) # Green style for START
        self.btn_toggle.setEnabled(self.current_port is not None)
        self.log_message.emit("Stress test stopped.", "INFO")
        
        # Add snapshot to table
        row_idx = self.snapshot_table.rowCount()
        self.snapshot_table.insertRow(row_idx)
        
        curr_time = datetime.now().strftime("%H:%M:%S")
        self.snapshot_table.setItem(row_idx, 0, QTableWidgetItem(curr_time))
        self.snapshot_table.setItem(row_idx, 1, QTableWidgetItem(self.lbl_total_hits.text()))
        self.snapshot_table.setItem(row_idx, 2, QTableWidgetItem(self.lbl_success.text()))
        self.snapshot_table.setItem(row_idx, 3, QTableWidgetItem(self.lbl_failure.text()))
        self.snapshot_table.setItem(row_idx, 4, QTableWidgetItem(self.lbl_failure_percent.text()))


class StressTestWorker(QObject):
    finished = Signal()
    progress = Signal(str)
    # total, success, failure, current_value
    stats_updated = Signal(int, int, int, str)

    def __init__(self, port, slave_id, target_reg, delay_ms, data_type="Integer (16-bit)"):
        super().__init__()
        self.port = port
        self.slave_id = slave_id
        self.target_reg = target_reg
        self.delay_ms = delay_ms
        self.data_type = data_type
        self.client = ModbusClientWrapper()
        self._is_running = True

        self.total_hits = 0
        self.success_count = 0
        self.failure_count = 0

    def run(self):
        if not self.client.connect(self.port):
            self.progress.emit("Failed to connect to port for stress testing.")
            self.finished.emit()
            return

        try:
            while self._is_running:
                # Read register based on data type
                err = None
                regs = None
                val_str = "-"
                
                if self.data_type == "Float (32-bit)":
                    regs, err = self.client.read_holding_registers(self.slave_id, self.target_reg, 2)
                    if not err and regs and len(regs) == 2:
                        try:
                            # Usually Big Endian Float
                            float_val = struct.unpack('>f', struct.pack('>HH', regs[0], regs[1]))[0]
                            val_str = f"{float_val:.4f}"
                        except Exception as e:
                            err = f"Conv Error: {e}"
                elif self.data_type == "Coil":
                    bits, err = self.client.read_coils(self.slave_id, self.target_reg, 1)
                    if not err and bits:
                        regs = bits
                        val_str = str(bits[0])
                else: # Integer (16-bit)
                    regs, err = self.client.read_holding_registers(self.slave_id, self.target_reg, 1)
                    if not err and regs:
                        val_str = str(regs[0])

                self.total_hits += 1

                if not err and regs:
                    self.success_count += 1
                else:
                    self.failure_count += 1
                    val_str = "ERR"
                    # Emit specific failure msg
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    if err:
                        self.progress.emit(f"[{timestamp}] Failure #{self.failure_count} at target {self.target_reg}. Reason: {err}")
                    else:
                        self.progress.emit(f"[{timestamp}] Failure #{self.failure_count} at target {self.target_reg}.")

                self.stats_updated.emit(self.total_hits, self.success_count, self.failure_count, val_str)

                # Delay logic
                # Break down delay to allow quick stopping
                sleep_interval = 0.05 # 50 ms
                time_slept = 0
                target_sleep = self.delay_ms / 1000.0

                while time_slept < target_sleep and self._is_running:
                    time.sleep(sleep_interval)
                    time_slept += sleep_interval
                
        except Exception as e:
            self.progress.emit(f"Stress test error: {e}")
        finally:
            self.client.disconnect()
            self.finished.emit()
            
    def stop(self):
        self._is_running = False
