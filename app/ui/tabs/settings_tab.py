from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QPushButton, QMessageBox, QSpinBox, QComboBox
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Modbus Settings
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

        # Register Map Settings
        reg_group = QGroupBox("Register Map (Addresses)")
        reg_group.setStyleSheet("QGroupBox { border: 1px solid #4a5568; border-radius: 6px; margin-top: 6px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")

        self.reg_layout = QFormLayout(reg_group)
        self.reg_layout.setLabelAlignment(Qt.AlignRight)

        # Helper to create inputs
        self.inputs = {}

        def add_reg_input(label, key):
            inp = QSpinBox()
            inp.setRange(0, 65535)
            inp.setStyleSheet("background-color: #2d3748; color: white; border: 1px solid #4a5568; padding: 4px; border-radius: 4px;")
            self.reg_layout.addRow(label, inp)
            self.inputs[key] = inp

        add_reg_input("Slave ID (Legacy):", "slave_id_register_address")
        add_reg_input("Update Coil (Legacy):", "update_coil_address")
        add_reg_input("Meter Const (Reg):", "meter_constant_address")
        add_reg_input("Ref Const (Reg):", "reference_constant_address")
        add_reg_input("Test Pulses (Reg):", "test_pulses_address")
        add_reg_input("Start Coil:", "start_coil_address")

        layout.addWidget(reg_group)

        layout.addStretch()

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
        layout.addWidget(self.btn_save)

        self.load_values()

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
            QMessageBox.information(self, "Settings", "Settings saved successfully. Restart may be required for some changes.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save settings to file.")
