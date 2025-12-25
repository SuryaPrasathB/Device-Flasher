from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox,
    QAbstractSpinBox
)
from PySide6.QtCore import Qt, Signal
from app.utils.helpers import get_resource_path
from app.core.validation import Validator

class SlaveIDTab(QWidget):
    """
    Tab 1: Flash Slave ID (Legacy Functionality)
    """

    # Signal to request a flash operation.
    # Args: slave_id (int)
    request_flash = Signal(int)

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header / Title
        title = QLabel("Set Slave ID")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)

        subtitle = QLabel("Flash Slave ID to Embedded Controller")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #a0aec0;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Slave ID Input
        layout.addWidget(QLabel("New Slave ID"))

        self.input_slave_id = QSpinBox()
        self.input_slave_id.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.input_slave_id.setRange(1, 247)
        self.input_slave_id.setSingleStep(1)
        self.input_slave_id.setValue(1)

        # Reusing the style from main_window (we will eventually centralize styles)
        arrow_up = get_resource_path("resources/arrow_up.svg").replace("\\", "/")
        arrow_down = get_resource_path("resources/arrow_down.svg").replace("\\", "/")

        self.input_slave_id.setStyleSheet(f"""
            QSpinBox {{
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding-right: 20px;
                color: white;
            }}

            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #4a5568;
            }}

            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #4a5568;
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
        self.input_slave_id.valueChanged.connect(self.validate_form)
        layout.addWidget(self.input_slave_id)

        layout.addSpacing(20)

        # Flash Button
        self.btn_flash = QPushButton("Set Slave ID")
        self.btn_flash.setFixedHeight(45)
        self.btn_flash.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a67d8, stop:1 #6b46c1);
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #a0aec0;
            }
        """)
        self.btn_flash.clicked.connect(self.on_flash_clicked)
        self.btn_flash.setEnabled(False) # Initially disabled until port connected
        layout.addWidget(self.btn_flash)

        # Note
        note = QLabel("<b>Note:</b> Ensure the device is properly connected before flashing. "
                      "Valid Slave ID range: 1–247")
        note.setStyleSheet("background-color: #2d3748; color: #cbd5e0; padding: 10px; border-radius: 4px; font-size: 12px; border-left: 4px solid #4299e1;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

    def set_enabled(self, enabled):
        self.btn_flash.setEnabled(enabled)
        # We re-validate to ensure ID is valid too
        if enabled:
            self.validate_form()

    def validate_form(self):
        # We assume Main Window controls the port connection status
        # Here we just check the ID (which spinbox limits anyway)
        sid_text = self.input_slave_id.text()
        valid_sid, _ = Validator.validate_slave_id(sid_text)

        # If the parent says we are "connected" (enabled), we check validity
        # If the parent disabled us, we stay disabled.
        if self.isEnabled():
             self.btn_flash.setEnabled(valid_sid)

    def on_flash_clicked(self):
        slave_id = int(self.input_slave_id.text())
        self.request_flash.emit(slave_id)

    def set_button_state(self, state_text, enabled):
        self.btn_flash.setText(state_text)
        self.btn_flash.setEnabled(enabled)
