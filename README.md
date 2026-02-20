# LDU Tester

A modular, professional desktop application to configure Modbus RTU slave devices.

## Requirements

*   Python 3.8+
*   `pip` packages:
    *   `PySide6`
    *   `pymodbus`
    *   `pyserial`

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:
    ```bash
    python main.py
    ```
2.  Select the **COM Port** connected to the Modbus device.
3.  Enter the new **Slave ID** (1-247).
4.  Click **Flash Device**.

## Configuration

The application is configurable via `config.json`. You can modify:
*   **Modbus Parameters**: Baud rate, parity, timeout, etc.
*   **Register Map**:
    *   `slave_id_register_address`: The holding register address where the Slave ID is written (0-based).
    *   `update_coil_address`: The coil address that triggers the save/update (0-based).

Example `config.json`:
```json
{
    "modbus": {
        "baudrate": 9600,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 1
    },
    "register_map": {
        "slave_id_register_address": 0,
        "update_coil_address": 0
    }
}
```

## Architecture

The application follows a modular architecture:

*   **`app/ui/`**: Contains the User Interface logic (PySide6). The UI is decoupled from the business logic.
*   **`app/core/`**: Contains the business logic (`FlashService`) and validation rules. It uses the Modbus layer to perform operations.
*   **`app/modbus/`**: Wraps the `pymodbus` library and handles serial communication details.
*   **`app/utils/`**: Utilities for configuration and logging.

## Developer Notes

### Extending Modbus Commands
To add more commands (e.g., setting baud rate via Modbus):
1.  Add a method to `app/modbus/modbus_client.py`.
2.  Update `app/core/flash_service.py` to use the new method in the sequence.
3.  Update UI if necessary.

### Packaging
To package this application into an EXE/Installer:
1.  Use `PyInstaller`:
    ```bash
    pip install pyinstaller
    pyinstaller --noconsole --onefile --name "DeviceFlasher" --add-data "config.json;." --add-data "resources;resources" main.py
    ```
2.  Ensure `config.json` is distributed with the executable or embedded (requires code changes to load resource).
