from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QMessageBox, QSpinBox, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt
from app.utils.config import config

class SettingsTab(QWidget):
    """
    Tab 3: Settings (Modbus & Register Map)
    """
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)

        # --- Modbus Settings ---
        modbus_group = QGroupBox("Modbus Communication")
        modbus_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")

        self.modbus_layout = QFormLayout(modbus_group)
        self.modbus_layout.setLabelAlignment(Qt.AlignRight)

        # Baudrate
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        self._style_combo(self.combo_baud)
        self.modbus_layout.addRow("Baudrate:", self.combo_baud)

        # Parity
        self.combo_parity = QComboBox()
        self.combo_parity.addItems(["N", "E", "O"])
        self._style_combo(self.combo_parity)
        self.modbus_layout.addRow("Parity:", self.combo_parity)

        # Stopbits
        self.combo_stop = QComboBox()
        self.combo_stop.addItems(["1", "2"])
        self._style_combo(self.combo_stop)
        self.modbus_layout.addRow("Stop Bits:", self.combo_stop)

        layout.addWidget(modbus_group)

        # --- Register Map Settings ---
        self.inputs = {}

        # Group 1: Common Registers
        common_group = QGroupBox("Common Registers")
        common_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        self.common_layout = QFormLayout(common_group)
        self.common_layout.setLabelAlignment(Qt.AlignRight)

        self._add_reg_input(self.common_layout, "Slave ID (Reg):", "slave_id_register_address")
        self._add_reg_input(self.common_layout, "Test Type:", "test_type_address")
        self._add_reg_input(self.common_layout, "Start Trigger Coil:", "start_coil_address")
        self._add_reg_input(self.common_layout, "Result Code:", "result_code_address")

        layout.addWidget(common_group)

        # Group 2: LOE (Limits of Error)
        loe_group = QGroupBox("Limits of Error (LOE)")
        loe_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        self.loe_layout = QFormLayout(loe_group)
        self.loe_layout.setLabelAlignment(Qt.AlignRight)

        self._add_reg_input(self.loe_layout, "Meter Constant:", "dut_meter_constant_address")
        self._add_reg_input(self.loe_layout, "Ref Constant (HB):", "ref_meter_constant_address")
        self._add_reg_input(self.loe_layout, "Target Pulses:", "dut_meter_target_pulses_address")
        self._add_reg_input(self.loe_layout, "Pulse Skip:", "num_of_pulse_skip_address")
        self._add_reg_input(self.loe_layout, "Error Read (HB):", "error_address")

        layout.addWidget(loe_group)

        # Group 3: Starting Current & No Load
        sc_nl_group = QGroupBox("Starting Current & No Load")
        sc_nl_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        self.sc_nl_layout = QFormLayout(sc_nl_group)
        self.sc_nl_layout.setLabelAlignment(Qt.AlignRight)

        self._add_reg_input(self.sc_nl_layout, "Time Duration:", "time_duration_address")
        self._add_reg_input(self.sc_nl_layout, "Min Pulse Expected:", "min_pulse_expected_address")
        self._add_reg_input(self.sc_nl_layout, "Max Pulse Accepted:", "max_pulse_accepted_address")
        self._add_reg_input(self.sc_nl_layout, "DUT Pulse Count:", "dut_meter_pulse_count_address")

        layout.addWidget(sc_nl_group)

        # Group 4: Dial Test
        dial_group = QGroupBox("Dial Test")
        dial_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        self.dial_layout = QFormLayout(dial_group)
        self.dial_layout.setLabelAlignment(Qt.AlignRight)

        # Note: Ref Const and Pulse Skip are already in LOE, but also used here.
        # Since they are the same address key, we don't duplicate the input widget unless we want dual controls (bad).
        # We just assume the user sets them in LOE section or Common.
        # But wait, User asked to categorize. If I add it again, I need unique dict keys or synced widgets.
        # I'll stick to listing unique registers per group where they primarily belong, or add the new ones specifically.

        self._add_reg_input(self.dial_layout, "Target Energy:", "target_energy_address")

        layout.addWidget(dial_group)

        # Group 5: Legacy/Other
        other_group = QGroupBox("Other")
        other_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        self.other_layout = QFormLayout(other_group)
        self.other_layout.setLabelAlignment(Qt.AlignRight)

        self._add_reg_input(self.other_layout, "Comm Mode:", "comm_mode_address")
        self._add_reg_input(self.other_layout, "Num Set Reading:", "num_of_set_of_reading_address")
        self._add_reg_input(self.other_layout, "Nth Reading:", "nth_reading_address")
        self._add_reg_input(self.other_layout, "Slave ID Set Coil:", "slave_id_set_coil")
        self._add_reg_input(self.other_layout, "SW Reset Coil:", "software_reset_coil")

        layout.addWidget(other_group)

        layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Save Button
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2c5282; }
        """)
        self.btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(self.btn_save)

        self.load_values()

    def _add_reg_input(self, layout, label, key):
        inp = QSpinBox()
        inp.setRange(0, 65535)
        inp.setStyleSheet("background-color: #2d3748; color: white; border: 1px solid #4a5568; padding: 4px; border-radius: 4px;")
        layout.addRow(label, inp)
        self.inputs[key] = inp

    def _style_combo(self, combo):
        combo.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                selection-background-color: #4a5568;
            }
        """)

    def load_values(self):
        # Load Modbus
        m = config.modbus_settings
        self.combo_baud.setCurrentText(str(m.get("baudrate", 115200)))
        self.combo_parity.setCurrentText(m.get("parity", "N"))
        self.combo_stop.setCurrentText(str(m.get("stopbits", 1)))

        # Load Registers
        r = config.register_map
        for key, inp in self.inputs.items():
            inp.setValue(r.get(key, 0))

    def save_settings(self):
        # Update Config Object
        # Modbus
        config._config_data['modbus']['baudrate'] = int(self.combo_baud.currentText())
        config._config_data['modbus']['parity'] = self.combo_parity.currentText()
        config._config_data['modbus']['stopbits'] = int(self.combo_stop.currentText())

        # Registers
        if 'register_map' not in config._config_data:
            config._config_data['register_map'] = {}

        for key, inp in self.inputs.items():
            config._config_data['register_map'][key] = inp.value()

        # Persist
        if config.save():
            QMessageBox.information(self, "Settings", "Settings saved successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings to file.")
